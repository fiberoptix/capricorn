#!/bin/bash
# Restart Capricorn frontend container

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOCKER_DIR="$(dirname "$SCRIPT_DIR")/docker"

echo "🔄 Restarting Capricorn Frontend..."

cd "$DOCKER_DIR"

if [ -f "docker-compose.yml" ]; then
    echo "📦 Restarting via Docker..."
    docker compose restart frontend
    echo ""
    echo "✅ Frontend restarted!"
    echo "🌐 Access at http://localhost:5001"
    echo ""
    echo "💡 Tip: Run './scripts/qa-test.sh' to verify all services"
else
    echo "❌ Error: docker-compose.yml not found in $DOCKER_DIR"
    exit 1
fi
