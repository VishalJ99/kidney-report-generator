#!/bin/bash

# Railway Deployment Script
# Deploys both frontend and backend in parallel

set -e

echo "🚀 Starting Railway deployment for both frontend and backend..."

# Function to deploy frontend
deploy_frontend() {
    echo "📱 Deploying frontend..."
    cd frontend
    railway up
    echo "✅ Frontend deployment completed"
}

# Function to deploy backend
deploy_backend() {
    echo "🔧 Deploying backend..."
    cd backend
    railway up
    echo "✅ Backend deployment completed"
}

# Run both deployments in parallel
deploy_frontend &
FRONTEND_PID=$!

deploy_backend &
BACKEND_PID=$!

# Wait for both processes to complete
echo "⏳ Waiting for deployments to complete..."

wait $FRONTEND_PID
FRONTEND_STATUS=$?

wait $BACKEND_PID
BACKEND_STATUS=$?

# Check results
if [ $FRONTEND_STATUS -eq 0 ] && [ $BACKEND_STATUS -eq 0 ]; then
    echo "🎉 Both deployments completed successfully!"
else
    echo "❌ One or more deployments failed"
    echo "Frontend exit code: $FRONTEND_STATUS"
    echo "Backend exit code: $BACKEND_STATUS"
    exit 1
fi
