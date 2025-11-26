#!/bin/bash
# Capricorn Docker Management Script
# Based on finance-manager/run-docker.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DOCKER_DIR="$PROJECT_ROOT/docker"

ACTION=${1:-help}

cd "$DOCKER_DIR"

case $ACTION in
  start)
    echo "🚀 Starting Capricorn..."
    docker-compose up -d
    echo ""
    echo "✅ Capricorn is running!"
    echo "   Frontend:  http://localhost:5001"
    echo "   Backend:   http://localhost:5002"
    echo "   API Docs:  http://localhost:5002/docs"
    echo "   Database:  localhost:5003"
    echo "   Redis:     localhost:5004"
    echo ""
    echo "Run './scripts/qa-test.sh' to verify all services"
    ;;
  
  stop)
    echo "🛑 Stopping Capricorn..."
    docker-compose down
    echo "✅ Capricorn stopped"
    ;;
  
  restart)
    echo "🔄 Restarting Capricorn..."
    docker-compose restart
    echo "✅ Capricorn restarted"
    ;;
  
  rebuild)
    echo "🔨 Rebuilding Capricorn..."
    docker-compose down
    docker-compose build --no-cache
    docker-compose up -d
    echo ""
    echo "⏳ Waiting for services to be ready..."
    sleep 5
    echo ""
    echo "🧪 Running QA tests..."
    cd "$PROJECT_ROOT"
    ./scripts/qa-test.sh
    ;;
  
  logs)
    docker-compose logs -f
    ;;
  
  logs-frontend)
    docker-compose logs -f frontend
    ;;
  
  logs-backend)
    docker-compose logs -f backend
    ;;
  
  logs-db)
    docker-compose logs -f postgres
    ;;
  
  logs-redis)
    docker-compose logs -f redis
    ;;
  
  ps)
    docker-compose ps
    ;;
  
  clean)
    echo "🧹 Cleaning up Capricorn..."
    docker-compose down -v
    echo "✅ All containers and volumes removed"
    ;;
  
  bb)
    echo ""
    echo "⚠️  =============================================="
    echo "⚠️  BURN & BUILD - COMPLETE FRESH INSTALLATION"
    echo "⚠️  =============================================="
    echo ""
    echo "🔥 This will DESTROY all data including:"
    echo "   • All database records (transactions, portfolios, etc.)"
    echo "   • All user profile settings"
    echo "   • All uploaded files and caches"
    echo ""
    echo "   YOU WILL LOSE ALL YOUR DATA!"
    echo ""
    read -p "Are you sure you want to continue? (yes/no): " confirm
    if [ "$confirm" != "yes" ]; then
      echo "❌ Aborted. No changes made."
      exit 0
    fi
    echo ""
    echo "🧹 Step 1/4: Stopping and removing all containers..."
    docker-compose down -v --remove-orphans
    echo ""
    echo "🗑️  Step 2/4: Removing Docker build cache..."
    docker builder prune -f 2>/dev/null || true
    echo ""
    echo "🔨 Step 3/4: Rebuilding all containers from scratch..."
    docker-compose build --no-cache
    echo ""
    echo "🚀 Step 4/4: Starting fresh Capricorn..."
    docker-compose up -d
    echo ""
    echo "⏳ Waiting for services to initialize..."
    sleep 8
    echo ""
    echo "🧪 Running QA tests..."
    cd "$PROJECT_ROOT"
    ./scripts/qa-test.sh
    echo ""
    echo "🎉 Burn & Build complete! Fresh Capricorn is running."
    echo "   Frontend:  http://localhost:5001"
    echo "   Backend:   http://localhost:5002"
    ;;
  
  *)
    echo "Capricorn Docker Management"
    echo ""
    echo "Usage: ./run-docker.sh [command]"
    echo ""
    echo "Commands:"
    echo "  start         Start all services"
    echo "  stop          Stop all services"
    echo "  restart       Restart all services"
    echo "  rebuild       Rebuild and restart with QA tests"
    echo "  bb            🔥 Burn & Build - WIPE ALL DATA and rebuild fresh"
    echo "  logs          Show all logs (live)"
    echo "  logs-frontend Show frontend logs"
    echo "  logs-backend  Show backend logs"
    echo "  logs-db       Show database logs"
    echo "  logs-redis    Show Redis logs"
    echo "  ps            Show running containers"
    echo "  clean         Stop and remove all containers and volumes"
    echo ""
    ;;
esac

