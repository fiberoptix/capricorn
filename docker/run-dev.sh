#!/bin/bash
# Capricorn DEV Environment
# Usage: ./run-dev.sh

set -e
cd "$(dirname "$0")"

echo ""
echo "🐐 Capricorn DEV Environment"
echo "=============================="
echo ""

# Tear down any existing containers (both DEV and PROD)
echo "🧹 Cleaning up existing containers..."
docker-compose down 2>/dev/null || true
docker-compose -f docker-compose.prod.yml down 2>/dev/null || true

echo ""
echo "🔨 Building and starting DEV environment..."
docker-compose up -d --build

echo ""
echo "⏳ Waiting for services to initialize..."
sleep 5

echo ""
echo "✅ DEV environment running!"
echo ""
echo "   Frontend:  http://localhost:5001"
echo "   Backend:   http://localhost:5002"
echo "   API Docs:  http://localhost:5002/docs"
echo "   Database:  localhost:5003"
echo "   Redis:     localhost:5004"
echo ""
echo "📋 Logs:  docker-compose logs -f"
echo "🛑 Stop:  docker-compose down"
echo ""

