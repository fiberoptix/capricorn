#!/bin/bash
# Capricorn GCP Environment Management
# Usage: ./run-gcp.sh [command]
#
# Commands:
#   start   - Deploy to GCP (build images + terraform + kubernetes)
#   stop    - Stop GCP deployments (keep cluster to save startup time)
#   restart - Restart GCP deployments
#   bb      - Burn & Build (full rebuild + redeploy)
#   nuke    - DESTROY everything (cluster, images, ALL GCP resources)
#
# GCP-Specific Commands:
#   status  - Show GKE pod/service status
#   logs    - Tail backend logs
#   fix-fe  - Rebuild frontend with correct backend URL

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DOCKER_DIR="$PROJECT_ROOT/docker"
CLOUD_DIR="$PROJECT_ROOT/cloud"
TERRAFORM_DIR="$CLOUD_DIR/terraform"
K8S_DIR="$CLOUD_DIR/kubernetes"
ACTION=${1:-start}

# GCP Settings
PROJECT_ID="voltaic-cirrus-476620-h5"
REGION="us-east1"
CLUSTER_NAME="capricorn-cluster"
NAMESPACE="capricorn"

# Service Account Key (stored in capricorn/cloud/ - DO NOT commit to git)
SERVICE_ACCOUNT_KEY="$CLOUD_DIR/gcp-service-account.json"

show_help() {
    echo ""
    echo "🐐 Capricorn GCP Environment"
    echo "=============================="
    echo ""
    echo "Usage: ./run-gcp.sh [command]"
    echo ""
    echo "Commands:"
    echo "  start   - Deploy to GCP (default)"
    echo "  stop    - Stop GCP deployments (keeps cluster)"
    echo "  restart - Restart GCP deployments"
    echo "  bb      - Burn & Build (full rebuild + redeploy)"
    echo "  nuke    - ⚠️  DESTROY everything on GCP"
    echo ""
    echo "GCP-Specific:"
    echo "  status  - Show GKE pod/service status"
    echo "  logs    - Tail backend logs"
    echo "  fix-fe  - Rebuild frontend with correct backend URL"
    echo ""
    echo "GCP Project: $PROJECT_ID"
    echo "Cluster:     $CLUSTER_NAME"
    echo ""
}

# Check prerequisites
check_prerequisites() {
    echo "📋 Checking prerequisites..."
    
    local missing=0
    
    if ! command -v gcloud &> /dev/null; then
        echo "  ❌ gcloud CLI not found"
        missing=1
    fi
    
    if ! command -v terraform &> /dev/null; then
        echo "  ❌ Terraform not found"
        missing=1
    fi
    
    if ! command -v kubectl &> /dev/null; then
        echo "  ❌ kubectl not found"
        missing=1
    fi
    
    if ! command -v docker &> /dev/null; then
        echo "  ❌ Docker not found"
        missing=1
    fi
    
    if [ ! -f "$SERVICE_ACCOUNT_KEY" ]; then
        echo "  ❌ Service account key not found"
        missing=1
    fi
    
    if [ $missing -eq 1 ]; then
        exit 1
    fi
    
    echo "  ✅ All prerequisites installed"
}

# Set up authentication
setup_auth() {
    echo ""
    echo "🔐 Setting up authentication..."
    export GOOGLE_APPLICATION_CREDENTIALS="$SERVICE_ACCOUNT_KEY"
    gcloud auth configure-docker gcr.io --quiet 2>/dev/null
    echo "  ✅ Authentication configured"
}

# Configure kubectl for the cluster
configure_kubectl() {
    echo ""
    echo "🔧 Configuring kubectl..."
    gcloud container clusters get-credentials $CLUSTER_NAME \
        --region $REGION \
        --project $PROJECT_ID 2>/dev/null
    echo "  ✅ kubectl configured for $CLUSTER_NAME"
}

# Build and push all images
build_images() {
    echo ""
    echo "🐳 Building and pushing container images..."
    cd "$PROJECT_ROOT"
    
    echo "  [1/3] Building postgres (with SQL init scripts)..."
    docker buildx build \
        --platform linux/amd64 \
        -f docker/Dockerfile.postgres.gcp \
        -t gcr.io/$PROJECT_ID/capricorn-postgres:latest \
        --push \
        . 2>&1 | tail -5
    
    echo "  [2/3] Building backend..."
    docker buildx build \
        --platform linux/amd64 \
        -f docker/Dockerfile.backend.gcp \
        -t gcr.io/$PROJECT_ID/capricorn-backend:latest \
        --push \
        . 2>&1 | tail -5
    
    # Get backend IP if available, otherwise use placeholder
    BACKEND_IP=$(kubectl get svc backend -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "")
    if [ -n "$BACKEND_IP" ]; then
        BACKEND_URL="http://${BACKEND_IP}:5002"
    else
        BACKEND_URL="http://localhost:5002"
    fi
    
    echo "  [3/3] Building frontend (API URL: $BACKEND_URL)..."
    docker buildx build \
        --platform linux/amd64 \
        -f docker/Dockerfile.frontend.gcp \
        --build-arg VITE_API_URL="$BACKEND_URL" \
        --build-arg VITE_BUILD_NUMBER="GCP" \
        -t gcr.io/$PROJECT_ID/capricorn-frontend:latest \
        --push \
        . 2>&1 | tail -5
    
    echo "  ✅ All images built and pushed to GCR"
}

# Create GKE cluster with Terraform
create_cluster() {
    echo ""
    echo "🏗️  Creating GKE cluster..."
    cd "$TERRAFORM_DIR"
    
    if gcloud container clusters describe $CLUSTER_NAME --region $REGION --project $PROJECT_ID &>/dev/null; then
        echo "  ✅ Cluster already exists"
    else
        echo "  ⏳ This may take 5-10 minutes..."
        terraform init -input=false 2>&1 | tail -3
        terraform apply -auto-approve -input=false 2>&1 | tail -10
        echo "  ✅ Cluster created"
    fi
}

# Deploy all Kubernetes resources
deploy_k8s() {
    echo ""
    echo "🚀 Deploying to Kubernetes..."
    cd "$K8S_DIR"
    
    kubectl apply -f namespace.yaml 2>/dev/null
    
    echo "  Deploying postgres..."
    kubectl apply -f postgres.yaml 2>/dev/null
    
    echo "  Deploying redis..."
    kubectl apply -f redis.yaml 2>/dev/null
    
    echo "  Waiting for databases..."
    kubectl wait --for=condition=ready pod -l app=postgres -n $NAMESPACE --timeout=300s 2>/dev/null || true
    kubectl wait --for=condition=ready pod -l app=redis -n $NAMESPACE --timeout=120s 2>/dev/null || true
    
    echo "  Deploying backend..."
    kubectl apply -f backend.yaml 2>/dev/null
    
    echo "  Waiting for backend..."
    kubectl wait --for=condition=ready pod -l app=backend -n $NAMESPACE --timeout=300s 2>/dev/null || true
    
    echo "  Deploying frontend..."
    kubectl apply -f frontend.yaml 2>/dev/null
    
    echo "  Waiting for frontend..."
    kubectl wait --for=condition=ready pod -l app=frontend -n $NAMESPACE --timeout=120s 2>/dev/null || true
    
    echo "  ✅ All services deployed"
}

# Get and display URLs
show_urls() {
    echo ""
    echo "🌐 Getting external URLs..."
    
    for i in {1..30}; do
        FRONTEND_IP=$(kubectl get svc frontend -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "")
        BACKEND_IP=$(kubectl get svc backend -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "")
        
        if [ -n "$FRONTEND_IP" ] && [ -n "$BACKEND_IP" ]; then
            break
        fi
        echo "  Waiting for LoadBalancer IPs... ($i/30)"
        sleep 10
    done
    
    echo ""
    echo "✅ GCP environment running!"
    echo ""
    echo "   Frontend:  http://$FRONTEND_IP"
    echo "   Backend:   http://$BACKEND_IP:5002"
    echo "   Health:    http://$BACKEND_IP:5002/health"
    echo ""
    echo "📋 Logs:   ./scripts/run-gcp.sh logs"
    echo "📊 Status: ./scripts/run-gcp.sh status"
    echo "🛑 Stop:   ./scripts/run-gcp.sh stop"
    echo ""
}

# Rebuild frontend with correct backend URL
fix_frontend() {
    echo ""
    echo "🔧 Fixing frontend with backend URL..."
    
    BACKEND_IP=$(kubectl get svc backend -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null)
    
    if [ -z "$BACKEND_IP" ]; then
        echo "  ❌ Backend service not found"
        exit 1
    fi
    
    BACKEND_URL="http://${BACKEND_IP}:5002"
    echo "  VITE_API_URL: $BACKEND_URL"
    
    cd "$PROJECT_ROOT"
    docker buildx build \
        --platform linux/amd64 \
        -f docker/Dockerfile.frontend.gcp \
        --build-arg VITE_API_URL="$BACKEND_URL" \
        --build-arg VITE_BUILD_NUMBER="GCP" \
        -t gcr.io/$PROJECT_ID/capricorn-frontend:latest \
        --push \
        . 2>&1 | tail -5
    
    echo "  🔄 Restarting frontend deployment..."
    kubectl rollout restart deployment/frontend -n $NAMESPACE
    kubectl rollout status deployment/frontend -n $NAMESPACE --timeout=120s 2>/dev/null
    
    echo "  ✅ Frontend fixed"
    show_urls
}

# === MAIN COMMANDS (matching run-dev.sh / run-prod.sh) ===

start_containers() {
    echo ""
    echo "🐐 Capricorn GCP Environment"
    echo "=============================="
    echo "  Project: $PROJECT_ID"
    echo "  Cluster: $CLUSTER_NAME"
    echo ""
    
    check_prerequisites
    setup_auth
    build_images
    create_cluster
    configure_kubectl
    deploy_k8s
    
    # Fix frontend with actual backend URL
    BACKEND_IP=$(kubectl get svc backend -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "")
    if [ -n "$BACKEND_IP" ]; then
        echo ""
        echo "🔧 Rebuilding frontend with backend URL..."
        BACKEND_URL="http://${BACKEND_IP}:5002"
        cd "$PROJECT_ROOT"
        docker buildx build \
            --platform linux/amd64 \
            -f docker/Dockerfile.frontend.gcp \
            --build-arg VITE_API_URL="$BACKEND_URL" \
            --build-arg VITE_BUILD_NUMBER="GCP" \
            -t gcr.io/$PROJECT_ID/capricorn-frontend:latest \
            --push \
            . 2>&1 | tail -3
        kubectl rollout restart deployment/frontend -n $NAMESPACE 2>/dev/null
        sleep 10
    fi
    
    show_urls
}

stop_containers() {
    echo ""
    echo "🛑 Stopping Capricorn GCP deployments..."
    echo "  (Keeping cluster to save startup time)"
    echo ""
    
    check_prerequisites
    setup_auth
    configure_kubectl
    
    kubectl delete deployment --all -n $NAMESPACE 2>/dev/null || true
    kubectl delete service frontend backend -n $NAMESPACE 2>/dev/null || true
    
    echo ""
    echo "✅ GCP deployments stopped"
    echo "   Cluster is still running (use 'nuke' to delete cluster)"
    echo "   Run './scripts/run-gcp.sh start' to redeploy"
    echo ""
}

restart_containers() {
    echo ""
    echo "🔄 Restarting Capricorn GCP deployments..."
    
    check_prerequisites
    setup_auth
    configure_kubectl
    
    kubectl rollout restart deployment/postgres -n $NAMESPACE 2>/dev/null || true
    kubectl rollout restart deployment/redis -n $NAMESPACE 2>/dev/null || true
    kubectl rollout restart deployment/backend -n $NAMESPACE 2>/dev/null || true
    kubectl rollout restart deployment/frontend -n $NAMESPACE 2>/dev/null || true
    
    echo "  ⏳ Waiting for rollouts..."
    kubectl rollout status deployment/backend -n $NAMESPACE --timeout=120s 2>/dev/null || true
    kubectl rollout status deployment/frontend -n $NAMESPACE --timeout=60s 2>/dev/null || true
    
    echo ""
    echo "✅ GCP deployments restarted"
    show_urls
}

burn_and_build() {
    echo ""
    echo "🔥 Burn & Build - GCP Environment"
    echo "=================================="
    echo ""
    
    check_prerequisites
    setup_auth
    configure_kubectl
    
    echo "🧹 Step 1/4: Deleting deployments..."
    kubectl delete deployment --all -n $NAMESPACE 2>/dev/null || true
    kubectl delete pvc --all -n $NAMESPACE 2>/dev/null || true
    
    echo ""
    echo "🔨 Step 2/4: Rebuilding images (no cache)..."
    cd "$PROJECT_ROOT"
    
    docker buildx build \
        --platform linux/amd64 \
        --no-cache \
        -f docker/Dockerfile.postgres.gcp \
        -t gcr.io/$PROJECT_ID/capricorn-postgres:latest \
        --push \
        . 2>&1 | tail -3
    
    docker buildx build \
        --platform linux/amd64 \
        --no-cache \
        -f docker/Dockerfile.backend.gcp \
        -t gcr.io/$PROJECT_ID/capricorn-backend:latest \
        --push \
        . 2>&1 | tail -3
    
    docker buildx build \
        --platform linux/amd64 \
        --no-cache \
        -f docker/Dockerfile.frontend.gcp \
        --build-arg VITE_API_URL="http://localhost:5002" \
        --build-arg VITE_BUILD_NUMBER="GCP" \
        -t gcr.io/$PROJECT_ID/capricorn-frontend:latest \
        --push \
        . 2>&1 | tail -3
    
    echo ""
    echo "🚀 Step 3/4: Deploying fresh..."
    deploy_k8s
    
    # Fix frontend URL
    sleep 15
    BACKEND_IP=$(kubectl get svc backend -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "")
    if [ -n "$BACKEND_IP" ]; then
        echo ""
        echo "🔧 Rebuilding frontend with backend URL..."
        BACKEND_URL="http://${BACKEND_IP}:5002"
        docker buildx build \
            --platform linux/amd64 \
            -f docker/Dockerfile.frontend.gcp \
            --build-arg VITE_API_URL="$BACKEND_URL" \
            --build-arg VITE_BUILD_NUMBER="GCP" \
            -t gcr.io/$PROJECT_ID/capricorn-frontend:latest \
            --push \
            . 2>&1 | tail -3
        kubectl rollout restart deployment/frontend -n $NAMESPACE 2>/dev/null
        sleep 10
    fi
    
    echo ""
    echo "🧪 Step 4/4: Running QA tests..."
    FRONTEND_IP=$(kubectl get svc frontend -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "")
    if [ -n "$BACKEND_IP" ]; then
        echo "  Testing backend health..."
        curl -s "http://$BACKEND_IP:5002/health" | head -1 || echo "  ⚠️  Backend health check failed"
    fi
    
    echo ""
    echo "✅ Burn & Build complete!"
    show_urls
}

nuke_everything() {
    echo ""
    echo "⚠️  =============================================="
    echo "⚠️  NUKE - COMPLETE GCP DESTRUCTION"
    echo "⚠️  =============================================="
    echo ""
    echo "🔥 This will DESTROY:"
    echo "   • GKE cluster ($CLUSTER_NAME)"
    echo "   • All Kubernetes deployments and services"
    echo "   • All persistent volumes and data"
    echo "   • All Docker images in GCR"
    echo "   • All Terraform state"
    echo ""
    echo "   ⚠️  THIS CANNOT BE UNDONE! ⚠️"
    echo ""
    read -p "Type 'NUKE' to confirm destruction: " confirm
    if [ "$confirm" != "NUKE" ]; then
        echo "❌ Aborted. No changes made."
        exit 0
    fi
    
    check_prerequisites
    setup_auth
    
    echo ""
    echo "🧹 Step 1/4: Deleting Kubernetes resources..."
    configure_kubectl 2>/dev/null || true
    kubectl delete namespace $NAMESPACE --ignore-not-found 2>/dev/null || true
    
    echo ""
    echo "🗑️  Step 2/4: Deleting GKE cluster..."
    gcloud container clusters delete $CLUSTER_NAME \
        --region $REGION \
        --project $PROJECT_ID \
        --quiet 2>/dev/null || echo "  Cluster already deleted or not found"
    
    echo ""
    echo "🗑️  Step 3/4: Deleting GCR images..."
    for image in capricorn-postgres capricorn-backend capricorn-frontend; do
        gcloud container images delete gcr.io/$PROJECT_ID/$image:latest --quiet --force-delete-tags 2>/dev/null || true
    done
    
    echo ""
    echo "🗑️  Step 4/4: Cleaning Terraform state..."
    cd "$TERRAFORM_DIR"
    rm -rf .terraform terraform.tfstate* .terraform.lock.hcl 2>/dev/null || true
    
    echo ""
    echo "💀 NUKE complete. Everything destroyed on GCP."
    echo "   Run './scripts/run-gcp.sh start' to rebuild from scratch."
    echo ""
}

show_status() {
    echo ""
    echo "📊 Capricorn GCP Status"
    echo "========================"
    echo ""
    echo "Pods:"
    kubectl get pods -n $NAMESPACE 2>/dev/null || echo "  (namespace not found - run 'start' first)"
    echo ""
    echo "Services:"
    kubectl get svc -n $NAMESPACE 2>/dev/null || echo "  (namespace not found)"
    echo ""
}

show_logs() {
    kubectl logs -f deployment/backend -n $NAMESPACE
}

# === MAIN SWITCH ===

case $ACTION in
    start)
        start_containers
        ;;
    stop)
        stop_containers
        ;;
    restart)
        restart_containers
        ;;
    bb)
        burn_and_build
        ;;
    nuke)
        nuke_everything
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs
        ;;
    fix-fe|fix-frontend)
        check_prerequisites
        setup_auth
        configure_kubectl
        fix_frontend
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo "❌ Unknown command: $ACTION"
        show_help
        exit 1
        ;;
esac
