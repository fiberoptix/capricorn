#!/bin/bash
# Capricorn PROD Environment Management
# Usage: ./run-prod.sh [command]
#
# Commands:
#   start   - Start PROD containers
#   stop    - Stop PROD containers
#   restart - Restart PROD containers
#   bb      - Burn & Build (teardown + rebuild + start)
#   nuke    - DESTROY everything (containers, volumes, caches, ALL DATA)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOCKER_DIR="$(dirname "$SCRIPT_DIR")/docker"
ACTION=${1:-start}

# Detect Docker Compose version (V1 vs V2)
if docker compose version &>/dev/null; then
    DOCKER_COMPOSE="docker compose"
elif docker-compose version &>/dev/null; then
    DOCKER_COMPOSE="docker-compose"
else
    echo "❌ Neither 'docker compose' nor 'docker-compose' found"
    exit 1
fi

cd "$DOCKER_DIR"

show_help() {
    echo ""
    echo "🐐 Capricorn PROD Environment"
    echo "=============================="
    echo ""
    echo "Usage: ./run-prod.sh [command]"
    echo ""
    echo "Commands:"
    echo "  start   - Start PROD containers (default)"
    echo "  stop    - Stop PROD containers"
    echo "  restart - Restart PROD containers"
    echo "  bb      - Burn & Build (teardown + rebuild + start)"
    echo "  nuke    - ⚠️  DESTROY everything including all data"
    echo ""
}

stop_containers() {
    echo "🛑 Stopping Capricorn PROD containers..."
    $DOCKER_COMPOSE -f docker-compose.prod.yml down 2>/dev/null || true
    echo "✅ PROD containers stopped"
}

start_containers() {
    echo ""
    echo "🐐 Capricorn PROD Environment"
    echo "=============================="
    echo ""
    
    # Stop DEV if running (to free ports)
    $DOCKER_COMPOSE -f docker-compose.dev.yml down 2>/dev/null || true
    
    # Check for optional TwelveData config
    if [ ! -f "../backend/market_data/TwelveData_Config.txt" ]; then
        echo "⚠️  TwelveData config not found (optional - live prices disabled)"
        echo ""
    fi
    
    echo "🔨 Building and starting PROD environment..."
    $DOCKER_COMPOSE -f docker-compose.prod.yml up -d --build
    
    echo ""
    echo "⏳ Waiting for services to initialize..."
    sleep 8
    
    echo ""
    echo "✅ PROD environment running!"
    echo ""
    echo "   Application: http://localhost:5001"
    echo ""
    echo "📋 Logs:  $DOCKER_COMPOSE -f docker-compose.prod.yml logs -f"
    echo "🛑 Stop:  ./scripts/run-prod.sh stop"
    echo ""
    echo "🔒 PROD mode: Database and Redis are internal-only (not exposed)"
    echo ""
}

restart_containers() {
    echo "🔄 Restarting Capricorn PROD containers..."
    $DOCKER_COMPOSE -f docker-compose.prod.yml restart
    echo "✅ PROD containers restarted"
}

burn_and_build() {
    echo ""
    echo "🔥 Burn & Build - PROD Environment"
    echo "==================================="
    echo ""
    
    echo "🧹 Step 1/4: Stopping containers..."
    $DOCKER_COMPOSE -f docker-compose.dev.yml down 2>/dev/null || true
    $DOCKER_COMPOSE -f docker-compose.prod.yml down 2>/dev/null || true
    
    echo ""
    echo "🔨 Step 2/4: Rebuilding without cache..."
    $DOCKER_COMPOSE -f docker-compose.prod.yml build --no-cache
    
    echo ""
    echo "🚀 Step 3/4: Starting fresh containers..."
    $DOCKER_COMPOSE -f docker-compose.prod.yml up -d
    
    echo ""
    echo "⏳ Waiting for services to initialize..."
    sleep 8
    
    echo ""
    echo "🧪 Step 4/4: Running QA tests..."
    "$SCRIPT_DIR/qa-test.sh"
    
    echo ""
    echo "✅ Burn & Build complete!"
    echo "   Application: http://localhost:5001"
    echo ""
    echo "🔒 PROD mode: Database and Redis are internal-only (not exposed)"
    echo ""
}

nuke_everything() {
    echo ""
    echo "⚠️  =============================================="
    echo "⚠️  NUKE - COMPLETE DESTRUCTION"
    echo "⚠️  =============================================="
    echo ""
    echo "🔥 This will DESTROY:"
    echo "   • All Capricorn containers"
    echo "   • All database data (transactions, portfolios, etc.)"
    echo "   • All Redis cache data"
    echo "   • All Docker build caches for this project"
    echo ""
    echo "   ⚠️  YOU WILL LOSE ALL YOUR DATA! ⚠️"
    echo ""
    read -p "Type 'NUKE' to confirm destruction: " confirm
    if [ "$confirm" != "NUKE" ]; then
        echo "❌ Aborted. No changes made."
        exit 0
    fi
    
    echo ""
    echo "🧹 Step 1/4: Stopping all containers..."
    $DOCKER_COMPOSE -f docker-compose.dev.yml down -v --remove-orphans 2>/dev/null || true
    $DOCKER_COMPOSE -f docker-compose.prod.yml down -v --remove-orphans 2>/dev/null || true
    
    echo ""
    echo "🗑️  Step 2/4: Removing Capricorn images..."
    docker images | grep -E "docker-frontend|docker-backend" | awk '{print $3}' | xargs -r docker rmi -f 2>/dev/null || true
    
    echo ""
    echo "🗑️  Step 3/4: Removing dangling images and build cache..."
    docker builder prune -f 2>/dev/null || true
    docker image prune -f 2>/dev/null || true
    
    echo ""
    echo "🗑️  Step 4/4: Removing volumes..."
    docker volume ls | grep -E "docker_postgres_data|docker_redis_data" | awk '{print $2}' | xargs -r docker volume rm 2>/dev/null || true
    
    echo ""
    echo "💀 NUKE complete. Everything destroyed."
    echo "   Run './scripts/run-prod.sh start' to rebuild from scratch."
    echo ""
}

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
    help|--help|-h)
        show_help
        ;;
    *)
        echo "❌ Unknown command: $ACTION"
        show_help
        exit 1
        ;;
esac

