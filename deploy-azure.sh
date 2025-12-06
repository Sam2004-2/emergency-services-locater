#!/bin/bash
# =============================================================================
# Azure Deployment Script for ES Locator
# =============================================================================
# This script deploys the Emergency Services Locator to Azure using:
# - Azure Container Registry (ACR) for Docker images
# - Azure Database for PostgreSQL Flexible Server with PostGIS
# - Azure Container Apps for the web application
# - Azure Cache for Redis
# =============================================================================

set -e

# Configuration - CHANGE THESE
RESOURCE_GROUP="es-locator-rg"
LOCATION="northeurope"  # Choose: eastus, westeurope, northeurope, etc.
APP_NAME="eslocator"

# Generated names (based on APP_NAME)
ACR_NAME="${APP_NAME}acr"
POSTGRES_SERVER="${APP_NAME}-db"
REDIS_NAME="${APP_NAME}-redis"
CONTAINER_APP_ENV="${APP_NAME}-env"
CONTAINER_APP="${APP_NAME}-app"

# Database settings
DB_NAME="es_locator"
DB_USER="esadmin"
DB_PASS=$(openssl rand -base64 16 | tr -dc 'a-zA-Z0-9' | head -c 16)

# Django settings
DJANGO_SECRET=$(openssl rand -base64 32 | tr -dc 'a-zA-Z0-9' | head -c 50)

echo "============================================="
echo "ES Locator Azure Deployment"
echo "============================================="
echo "Resource Group: $RESOURCE_GROUP"
echo "Location: $LOCATION"
echo "App Name: $APP_NAME"
echo "============================================="

# Step 1: Create Resource Group
echo ""
echo "[1/7] Creating Resource Group..."
az group create --name $RESOURCE_GROUP --location $LOCATION --output none
echo "✓ Resource Group created"

# Step 2: Create Azure Container Registry
echo ""
echo "[2/7] Creating Container Registry..."
az acr create \
    --resource-group $RESOURCE_GROUP \
    --name $ACR_NAME \
    --sku Basic \
    --admin-enabled true \
    --output none
echo "✓ Container Registry created: $ACR_NAME.azurecr.io"

# Get ACR credentials
ACR_PASSWORD=$(az acr credential show --name $ACR_NAME --query "passwords[0].value" -o tsv)

# Step 3: Create PostgreSQL with PostGIS
echo ""
echo "[3/7] Creating PostgreSQL Server with PostGIS..."
az postgres flexible-server create \
    --resource-group $RESOURCE_GROUP \
    --name $POSTGRES_SERVER \
    --location $LOCATION \
    --admin-user $DB_USER \
    --admin-password $DB_PASS \
    --sku-name Standard_B1ms \
    --tier Burstable \
    --storage-size 32 \
    --version 16 \
    --public-access 0.0.0.0 \
    --output none
echo "✓ PostgreSQL Server created"

# Enable PostGIS extension
echo "   Enabling PostGIS extension..."
az postgres flexible-server parameter set \
    --resource-group $RESOURCE_GROUP \
    --server-name $POSTGRES_SERVER \
    --name azure.extensions \
    --value POSTGIS \
    --output none

# Create database
az postgres flexible-server db create \
    --resource-group $RESOURCE_GROUP \
    --server-name $POSTGRES_SERVER \
    --database-name $DB_NAME \
    --output none
echo "✓ Database created with PostGIS"

# Step 4: Create Redis Cache
echo ""
echo "[4/7] Creating Redis Cache..."
az redis create \
    --resource-group $RESOURCE_GROUP \
    --name $REDIS_NAME \
    --location $LOCATION \
    --sku Basic \
    --vm-size c0 \
    --output none
echo "✓ Redis Cache created (may take a few minutes to be ready)"

# Step 5: Build and Push Docker Image
echo ""
echo "[5/7] Building and pushing Docker image..."
az acr login --name $ACR_NAME

# Build in ACR (cloud build)
az acr build \
    --registry $ACR_NAME \
    --image eslocator:latest \
    --file docker/web/Dockerfile \
    . 
echo "✓ Docker image built and pushed"

# Step 6: Create Container Apps Environment
echo ""
echo "[6/7] Creating Container Apps Environment..."
az containerapp env create \
    --resource-group $RESOURCE_GROUP \
    --name $CONTAINER_APP_ENV \
    --location $LOCATION \
    --output none
echo "✓ Container Apps Environment created"

# Get connection strings
POSTGRES_HOST="${POSTGRES_SERVER}.postgres.database.azure.com"
REDIS_KEY=$(az redis list-keys --resource-group $RESOURCE_GROUP --name $REDIS_NAME --query "primaryKey" -o tsv 2>/dev/null || echo "pending")
REDIS_HOST="${REDIS_NAME}.redis.cache.windows.net"

# Step 7: Deploy Container App
echo ""
echo "[7/7] Deploying Container App..."
az containerapp create \
    --resource-group $RESOURCE_GROUP \
    --name $CONTAINER_APP \
    --environment $CONTAINER_APP_ENV \
    --image "${ACR_NAME}.azurecr.io/eslocator:latest" \
    --registry-server "${ACR_NAME}.azurecr.io" \
    --registry-username $ACR_NAME \
    --registry-password "$ACR_PASSWORD" \
    --target-port 8000 \
    --ingress external \
    --min-replicas 1 \
    --max-replicas 3 \
    --cpu 0.5 \
    --memory 1Gi \
    --env-vars \
        "DJANGO_SECRET_KEY=$DJANGO_SECRET" \
        "DJANGO_DEBUG=False" \
        "DJANGO_ALLOWED_HOSTS=*" \
        "DB_HOST=$POSTGRES_HOST" \
        "DB_NAME=$DB_NAME" \
        "DB_USER=$DB_USER" \
        "DB_PASS=$DB_PASS" \
        "DB_PORT=5432" \
        "REDIS_URL=redis://:${REDIS_KEY}@${REDIS_HOST}:6380/0?ssl=true" \
    --output none

# Get the app URL
APP_URL=$(az containerapp show --resource-group $RESOURCE_GROUP --name $CONTAINER_APP --query "properties.configuration.ingress.fqdn" -o tsv)

# Update ALLOWED_HOSTS with actual FQDN (security fix)
echo "   Updating ALLOWED_HOSTS with actual domain..."
az containerapp update \
    --resource-group $RESOURCE_GROUP \
    --name $CONTAINER_APP \
    --set-env-vars "DJANGO_ALLOWED_HOSTS=$APP_URL" "CSRF_TRUSTED_ORIGINS=https://$APP_URL" \
    --output none

echo ""
echo "============================================="
echo "Deployment Complete!"
echo "============================================="
echo ""
echo "Application URL: https://$APP_URL"
echo ""
echo "Database Connection:"
echo "  Host: $POSTGRES_HOST"
echo "  Database: $DB_NAME"
echo "  User: $DB_USER"
echo "  Password: [STORED SECURELY - retrieve with: az containerapp show -g $RESOURCE_GROUP -n $CONTAINER_APP --query 'properties.template.containers[0].env']"
echo ""
echo "Next Steps:"
echo "1. Run migrations: az containerapp exec -g $RESOURCE_GROUP -n $CONTAINER_APP --command 'python manage.py migrate'"
echo "2. Create superuser: az containerapp exec -g $RESOURCE_GROUP -n $CONTAINER_APP --command 'python manage.py createsuperuser'"
echo "3. Import data: az containerapp exec -g $RESOURCE_GROUP -n $CONTAINER_APP --command 'python manage.py import_counties'"
echo ""
echo "Save these credentials securely!"
echo "============================================="
