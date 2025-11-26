#!/bin/bash
# Capricorn PROD Environment
# Usage: ./run-prod.sh

set -e
cd "$(dirname "$0")"

echo ""
echo "🐐 Capricorn PROD Environment"
echo "=============================="
echo ""

# Tear down any existing containers (both DEV and PROD)
echo "🧹 Cleaning up existing containers..."
docker-compose down 2>/dev/null || true
docker-compose -f docker-compose.prod.yml down 2>/dev/null || true

# Check for optional TwelveData config
if [ ! -f "../backend/market_data/TwelveData_Config.txt" ]; then
    echo ""
    echo "⚠️  TwelveData config not found (optional - live prices disabled)"
    echo "   To enable: cp backend/market_data/TwelveData_Config.example.txt backend/market_data/TwelveData_Config.txt"
fi

echo ""
echo "🔨 Building and starting PROD environment..."
docker-compose -f docker-compose.prod.yml up -d --build

echo ""
echo "⏳ Waiting for services to initialize..."
sleep 8

echo ""
echo "✅ PROD environment running!"
echo ""
echo "   Application: http://localhost:5001"
echo ""
echo "   📋 Logs:  docker-compose -f docker-compose.prod.yml logs -f"
echo "   🛑 Stop:  docker-compose -f docker-compose.prod.yml down"
echo ""
echo "🔒 PROD mode: Database and Redis are internal-only (not exposed)"
echo ""

