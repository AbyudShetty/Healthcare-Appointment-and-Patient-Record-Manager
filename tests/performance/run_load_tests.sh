#!/bin/bash

echo "🚀 Starting HCRM Load Tests"
echo "================================"

# Test 1: 500 concurrent users (NF-003)
echo "📊 Test 1: 500 Concurrent Users"
locust -f tests/performance/locustfile.py \
    --host=http://localhost:8000 \
    --users 500 \
    --spawn-rate 10 \
    --run-time 5m \
    --headless \
    --csv=results/load_test_500 \
    --html=results/load_test_500.html

# Test 2: Stress test with 1000 users
echo "📊 Test 2: Stress Test (1000 Users)"
locust -f tests/performance/locustfile.py \
    --host=http://localhost:8000 \
    --users 1000 \
    --spawn-rate 20 \
    --run-time 3m \
    --headless \
    --csv=results/stress_test_1000 \
    --html=results/stress_test_1000.html

echo "✅ Load tests complete! Check results/ directory"