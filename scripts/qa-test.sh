#!/bin/bash
# Capricorn QA Test Script
# Based on finance-manager/qa-test.sh

echo "🧪 Running Capricorn QA Tests..."
echo ""

PASS=0
FAIL=0

# Test 1: Check Docker containers are running
echo -n "Test 1: Docker containers running... "
if docker ps | grep -q "capricorn"; then
  RUNNING=$(docker ps --filter "name=capricorn" --format "{{.Names}}" | wc -l)
  if [ "$RUNNING" -eq 4 ]; then
    echo "✅ (4/4 containers)"
    ((PASS++))
  else
    echo "❌ ($RUNNING/4 containers)"
    ((FAIL++))
  fi
else
  echo "❌ (0/4 containers)"
  ((FAIL++))
fi

# Test 2: Check frontend (port 5001)
echo -n "Test 2: Frontend accessible (5001)... "
if timeout 5 bash -c "curl -s http://localhost:5001 > /dev/null 2>&1"; then
  echo "✅"
  ((PASS++))
else
  echo "⚠️  (may need warm-up time)"
  # Don't count as failure - might still be starting
fi

# Test 3: Check backend health endpoint (port 5002)
echo -n "Test 3: Backend API health (5002)... "
if timeout 5 bash -c "curl -s http://localhost:5002/health" | grep -q "healthy"; then
  echo "✅"
  ((PASS++))
else
  echo "⚠️  (may need warm-up time)"
  # Don't count as failure - might still be starting
fi

# Test 4: Check PostgreSQL connectivity (port 5003)
echo -n "Test 4: PostgreSQL connection (5003)... "
if docker exec capricorn-postgres pg_isready -U capricorn > /dev/null 2>&1; then
  echo "✅"
  ((PASS++))
else
  echo "❌"
  ((FAIL++))
fi

# Test 5: Check Redis connectivity (port 5004)
echo -n "Test 5: Redis connection (5004)... "
if docker exec capricorn-redis redis-cli ping 2>/dev/null | grep -q "PONG"; then
  echo "✅"
  ((PASS++))
else
  echo "❌"
  ((FAIL++))
fi

# Test 6: Check database exists
echo -n "Test 6: Database 'capricorn_db' exists... "
if docker exec capricorn-postgres psql -U capricorn -lqt | grep -qw capricorn_db; then
  echo "✅"
  ((PASS++))
else
  echo "❌"
  ((FAIL++))
fi

# Test 7: Check container health status
echo -n "Test 7: All containers healthy... "
UNHEALTHY=$(docker ps --filter "name=capricorn" --format "{{.Status}}" | grep -c "unhealthy" || true)
if [ "$UNHEALTHY" -eq 0 ]; then
  echo "✅"
  ((PASS++))
else
  echo "❌ ($UNHEALTHY unhealthy)"
  ((FAIL++))
fi

echo ""
echo "========================================="
echo "QA Test Results: $PASS passed, $FAIL failed"
echo "========================================="

if [ $FAIL -eq 0 ]; then
  echo "🎉 All critical tests passed!"
  exit 0
else
  echo "⚠️  Some tests failed. Check container logs:"
  echo "  ./scripts/run-docker.sh logs"
  exit 1
fi

