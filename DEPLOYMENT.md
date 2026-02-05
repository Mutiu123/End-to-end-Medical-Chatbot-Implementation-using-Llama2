# Deployment Guide

This document provides comprehensive deployment instructions for the Medical Chatbot API across different environments.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Local Development](#local-development)
3. [Docker Deployment](#docker-deployment)
4. [Kubernetes Deployment](#kubernetes-deployment)
5. [AWS EKS Deployment](#aws-eks-deployment)
6. [Environment Configuration](#environment-configuration)
7. [Database Setup](#database-setup)
8. [Monitoring Setup](#monitoring-setup)
9. [Security Considerations](#security-considerations)
10. [Troubleshooting](#troubleshooting)

## Prerequisites

### Software Requirements

- Python 3.11+
- Docker 24.0+
- Docker Compose 2.0+
- kubectl 1.28+
- AWS CLI 2.0+ (for AWS deployment)
- Helm 3.0+ (optional, for Kubernetes)

### External Services

- MongoDB 7.0+ (or MongoDB Atlas)
- Pinecone account with API key
- Llama 2 model file (download separately)

## Local Development

### Step 1: Clone Repository

```bash
git clone https://github.com/Mutiu123/End-to-end-Medical-Chatbot-Implementation-using-Llama2.git
cd End-to-end-Medical-Chatbot-Implementation-using-Llama2
```

### Step 2: Set Up Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate  # Windows
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### Step 4: Configure Environment

```bash
cp .env.example .env
# Edit .env with your configuration
```

### Step 5: Download LLM Model

```bash
mkdir -p model
# Download llama-2-7b-chat.ggmlv3.q4_0.bin to model/ directory
```

### Step 6: Start MongoDB

```bash
# Using Docker
docker run -d --name mongodb -p 27017:27017 mongo:7.0

# Or install locally and start
```

### Step 7: Initialize Vector Store

```bash
python store_index.py
```

### Step 8: Run Application

```bash
uvicorn app.main:app --reload --port 8080
```

Access the API at http://localhost:8080

## Docker Deployment

### Development with Docker Compose

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f app

# Stop services
docker-compose down
```

### Production Docker Build

```bash
# Build production image
docker build -t medical-chatbot:latest .

# Run container
docker run -d \
  --name medical-chatbot \
  -p 8080:8080 \
  --env-file .env \
  medical-chatbot:latest
```

### Docker Compose Production

```bash
# Use production compose file
docker-compose -f docker-compose.prod.yml up -d
```

## Kubernetes Deployment

### Step 1: Create Namespace

```bash
kubectl apply -f k8s/namespace.yaml
```

### Step 2: Create Secrets

```bash
# Create secrets from .env file
kubectl create secret generic medical-chatbot-secrets \
  --from-env-file=.env \
  -n medical-chatbot

# Or apply the template (edit first!)
kubectl apply -f k8s/secret.yaml
```

### Step 3: Create ConfigMap

```bash
kubectl apply -f k8s/configmap.yaml
```

### Step 4: Create Service Account

```bash
kubectl apply -f k8s/serviceaccount.yaml
```

### Step 5: Deploy Application

```bash
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
```

### Step 6: Configure Autoscaling

```bash
kubectl apply -f k8s/hpa.yaml
```

### Step 7: Set Up Ingress

```bash
kubectl apply -f k8s/ingress.yaml
```

### Step 8: Apply Network Policies

```bash
kubectl apply -f k8s/networkpolicy.yaml
```

### Verify Deployment

```bash
# Check pods
kubectl get pods -n medical-chatbot

# Check services
kubectl get svc -n medical-chatbot

# Check logs
kubectl logs -f deployment/medical-chatbot-api -n medical-chatbot

# Check HPA status
kubectl get hpa -n medical-chatbot
```

## AWS EKS Deployment

### Step 1: Create EKS Cluster

```bash
# Using eksctl
eksctl create cluster \
  --name medical-chatbot-cluster \
  --region us-west-2 \
  --nodegroup-name standard-workers \
  --node-type t3.medium \
  --nodes 3 \
  --nodes-min 2 \
  --nodes-max 5 \
  --managed
```

### Step 2: Configure kubectl

```bash
aws eks update-kubeconfig \
  --region us-west-2 \
  --name medical-chatbot-cluster
```

### Step 3: Install AWS Load Balancer Controller

```bash
# Add Helm repo
helm repo add eks https://aws.github.io/eks-charts

# Install controller
helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
  -n kube-system \
  --set clusterName=medical-chatbot-cluster
```

### Step 4: Push Image to ECR

```bash
# Create ECR repository
aws ecr create-repository \
  --repository-name medical-chatbot \
  --region us-west-2

# Login to ECR
aws ecr get-login-password --region us-west-2 | \
  docker login --username AWS --password-stdin \
  <account-id>.dkr.ecr.us-west-2.amazonaws.com

# Tag and push
docker tag medical-chatbot:latest \
  <account-id>.dkr.ecr.us-west-2.amazonaws.com/medical-chatbot:latest

docker push <account-id>.dkr.ecr.us-west-2.amazonaws.com/medical-chatbot:latest
```

### Step 5: Deploy to EKS

```bash
# Update deployment.yaml with ECR image URL
kubectl apply -f k8s/
```

## Environment Configuration

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| SECRET_KEY | JWT signing key | Random 32+ char string |
| MONGODB_URI | MongoDB connection string | mongodb://localhost:27017 |
| PINECONE_API_KEY | Pinecone API key | Your Pinecone key |
| PINECONE_ENVIRONMENT | Pinecone environment | us-west1-gcp |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| ENVIRONMENT | Environment name | development |
| DEBUG | Enable debug mode | false |
| LOG_LEVEL | Logging level | INFO |
| WORKERS | Number of workers | 4 |

## Database Setup

### MongoDB Atlas (Recommended for Production)

1. Create MongoDB Atlas account
2. Create a cluster
3. Set up database user
4. Whitelist IP addresses
5. Get connection string
6. Update MONGODB_URI in environment

### MongoDB Replica Set (Self-hosted)

```bash
# docker-compose.replica.yml
version: '3.9'
services:
  mongo1:
    image: mongo:7.0
    command: mongod --replSet rs0
    ports:
      - "27017:27017"

  mongo2:
    image: mongo:7.0
    command: mongod --replSet rs0

  mongo3:
    image: mongo:7.0
    command: mongod --replSet rs0
```

## Monitoring Setup

### Prometheus and Grafana

```bash
# Start monitoring stack
docker-compose up -d prometheus grafana

# Access Grafana at http://localhost:3000
# Default credentials: admin/admin
```

### Import Dashboards

1. Open Grafana
2. Go to Dashboards > Import
3. Import dashboards from grafana/dashboards/

### Key Metrics to Monitor

- Request rate and latency
- Error rate
- LLM inference time
- Database connection pool
- Memory and CPU usage

## Security Considerations

### Production Checklist

- [ ] Use strong SECRET_KEY (32+ random characters)
- [ ] Enable HTTPS/TLS
- [ ] Set restrictive CORS origins
- [ ] Use MongoDB authentication
- [ ] Enable rate limiting
- [ ] Run as non-root user
- [ ] Use read-only filesystem where possible
- [ ] Implement network policies
- [ ] Regular security updates
- [ ] Enable audit logging

### Generate Secure Secrets

```bash
# Generate SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate MongoDB password
openssl rand -base64 32
```

## Troubleshooting

### Common Issues

#### Application won't start

```bash
# Check logs
docker-compose logs app

# Verify environment variables
docker-compose config
```

#### Database connection failed

```bash
# Test MongoDB connection
mongosh "mongodb://localhost:27017"

# Check network
docker network inspect medical-chatbot-network
```

#### Out of memory

```bash
# Increase memory limits in docker-compose
deploy:
  resources:
    limits:
      memory: 8G
```

#### Slow LLM inference

- Use quantized model (4-bit)
- Increase max_tokens gradually
- Consider GPU acceleration

### Health Check Endpoints

```bash
# Liveness
curl http://localhost:8080/api/v1/live

# Readiness
curl http://localhost:8080/api/v1/ready

# Full health
curl http://localhost:8080/api/v1/health
```

### Getting Help

1. Check application logs
2. Review documentation
3. Search existing GitHub issues
4. Create new issue with details
