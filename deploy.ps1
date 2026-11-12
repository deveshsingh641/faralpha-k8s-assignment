# ==============================================================================
# Automated Deployment Script for Flask + MongoDB Stack on Minikube
# ==============================================================================

$ErrorActionPreference = "Stop"

function Check-ExitCode {
    param ([string]$StepName)
    if ($LASTEXITCODE -ne 0) {
        Write-Error "$StepName failed with exit code $LASTEXITCODE. Please review the output above."
        exit $LASTEXITCODE
    }
}

Write-Host "=== 1. Setting up Environment & Binaries ===" -ForegroundColor Cyan

# Add FarAlpha\bin (minikube, kubectl) to PATH
$binDir = Join-Path $PSScriptRoot "bin"
if (Test-Path $binDir) {
    $env:PATH = "$binDir;$env:PATH"
}

# Add Docker Desktop to PATH if not present
$dockerDir = "C:\Users\vic\AppData\Local\Programs\DockerDesktop\resources\bin"
if (Test-Path $dockerDir) {
    $env:PATH = "$dockerDir;$env:PATH"
}
$dockerProgFiles = "C:\Program Files\Docker\Docker\resources\bin"
if (Test-Path $dockerProgFiles) {
    $env:PATH = "$dockerProgFiles;$env:PATH"
}

if (-not (Get-Command minikube -ErrorAction SilentlyContinue)) {
    Write-Error "Minikube binary not found. Please ensure minikube is installed and in your PATH."
}
if (-not (Get-Command kubectl -ErrorAction SilentlyContinue)) {
    Write-Error "kubectl binary not found. Please ensure kubectl is installed and in your PATH."
}

Write-Host "=== 2. Starting Minikube Cluster (Driver: Docker) ===" -ForegroundColor Cyan
$minikubeStatus = (minikube status --format "{{.Host}}") 2>$null
if ($minikubeStatus -ne "Running") {
    Write-Host "Starting Minikube with Docker driver (4 CPUs, 4096MB memory)..."
    minikube start --driver=docker --cpus=4 --memory=4096
    Check-ExitCode "Minikube cluster startup"
} else {
    Write-Host "Minikube is already running." -ForegroundColor Green
}

Write-Host "=== 3. Enabling Metrics Server (Required for HPA) ===" -ForegroundColor Cyan
minikube addons enable metrics-server
Check-ExitCode "Enable metrics-server addon"

Write-Host "=== 4. Building & Loading Docker Image into Minikube ===" -ForegroundColor Cyan
$appDir = Join-Path $PSScriptRoot "flask-mongodb-app"

Write-Host "Building Docker image using Docker Desktop..."
docker build -t flask-mongodb-app:latest $appDir
Check-ExitCode "Docker image build"

Write-Host "Loading image into Minikube..."
minikube image load flask-mongodb-app:latest
Check-ExitCode "Minikube image load"

Write-Host "=== 5. Deploying Kubernetes Resources ===" -ForegroundColor Cyan
$k8sDir = Join-Path $PSScriptRoot "k8s"
kubectl apply -k $k8sDir
Check-ExitCode "kubectl apply"

Write-Host "=== 6. Waiting for Pods to Reach Ready State ===" -ForegroundColor Cyan
Write-Host "Waiting for MongoDB StatefulSet..."
kubectl rollout status statefulset/mongodb -n flask-mongo-app --timeout=180s
Check-ExitCode "MongoDB StatefulSet rollout"

Write-Host "Waiting for Flask Application Deployment..."
kubectl rollout status deployment/flask-app -n flask-mongo-app --timeout=180s
Check-ExitCode "Flask Application Deployment rollout"

Write-Host "=== 7. Cluster Deployment Summary ===" -ForegroundColor Green
kubectl get all,pv,pvc,hpa -n flask-mongo-app

Write-Host "`n=== 8. Application URL ===" -ForegroundColor Cyan
$serviceUrl = minikube service flask-service -n flask-mongo-app --url
Write-Host "The Flask Application is accessible at: $serviceUrl" -ForegroundColor Yellow
Write-Host "To open directly in your browser, run: minikube service flask-service -n flask-mongo-app"
