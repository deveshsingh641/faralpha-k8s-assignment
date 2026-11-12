#!/usr/bin/env bash
# ==============================================================================
# Automated Deployment Script for Flask + MongoDB Stack on Minikube (Linux/macOS)
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=== 1. Starting Minikube Cluster ==="
if ! minikube status | grep -q "Running"; then
    echo "Starting Minikube..."
    minikube start --cpus=4 --memory=4096
else
    echo "Minikube is already running."
fi

echo "=== 2. Enabling Metrics Server (Required for HPA) ==="
minikube addons enable metrics-server

echo "=== 3. Building & Loading Docker Image into Minikube ==="
if command -v docker >/dev/null 2>&1; then
    docker build -t flask-mongodb-app:latest "${SCRIPT_DIR}/flask-mongodb-app"
    minikube image load flask-mongodb-app:latest
else
    eval $(minikube docker-env)
    minikube image build -t flask-mongodb-app:latest "${SCRIPT_DIR}/flask-mongodb-app"
fi

echo "=== 4. Deploying Kubernetes Resources ==="
kubectl apply -k "${SCRIPT_DIR}/k8s"

echo "=== 5. Waiting for Rollouts to Complete ==="
kubectl rollout status statefulset/mongodb -n flask-mongo-app --timeout=180s
kubectl rollout status deployment/flask-app -n flask-mongo-app --timeout=180s

echo "=== 6. Cluster Resources Summary ==="
kubectl get all,pv,pvc,hpa -n flask-mongo-app

echo "=== 7. Application URL ==="
minikube service flask-service -n flask-mongo-app --url

