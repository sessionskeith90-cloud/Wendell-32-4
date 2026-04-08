#!/usr/bin/env bash
# ============================================================
# WENDELL Core 33 — One-Button Azure Deployment
# Deploys the platform to Azure Container Apps with RabbitMQ.
# Usage: ./deploy-azure.sh
# ============================================================
set -euo pipefail

# ── Configuration ────────────────────────────────────────────
RANDOM_ID="$(openssl rand -hex 3)"
RESOURCE_GROUP="WendellCore-rg-${RANDOM_ID}"
LOCATION="eastus"
ACR_NAME="wendellcr${RANDOM_ID}"
CONTAINER_APP_ENV="wendell-env-${RANDOM_ID}"
CONTAINER_APP_NAME="wendell-core-33"
IMAGE_NAME="wendell-core-33"
TAGS="owner=wendell project=core33"

echo "╔══════════════════════════════════════════════════╗"
echo "║  WENDELL Core 33 — Azure Deployment              ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""
echo "Resource Group : $RESOURCE_GROUP"
echo "Location       : $LOCATION"
echo "ACR            : $ACR_NAME"
echo ""

# ── 1. Resource Group ────────────────────────────────────────
echo "▸ Creating resource group..."
az group create \
    --name "$RESOURCE_GROUP" \
    --location "$LOCATION" \
    --tags $TAGS \
    --output none

# ── 2. Azure Container Registry ─────────────────────────────
echo "▸ Creating container registry..."
az acr create \
    --resource-group "$RESOURCE_GROUP" \
    --name "$ACR_NAME" \
    --sku Basic \
    --admin-enabled true \
    --output none

ACR_LOGIN_SERVER=$(az acr show --name "$ACR_NAME" --query loginServer -o tsv)
ACR_PASSWORD=$(az acr credential show --name "$ACR_NAME" --query "passwords[0].value" -o tsv)

# ── 3. Build & Push Docker Image ────────────────────────────
echo "▸ Building and pushing Docker image..."
az acr build \
    --registry "$ACR_NAME" \
    --image "${IMAGE_NAME}:latest" \
    --file Dockerfile \
    . \
    --no-logs

# ── 4. Container Apps Environment ────────────────────────────
echo "▸ Creating Container Apps environment..."
az containerapp env create \
    --name "$CONTAINER_APP_ENV" \
    --resource-group "$RESOURCE_GROUP" \
    --location "$LOCATION" \
    --output none

# ── 5. Deploy Container App ─────────────────────────────────
echo "▸ Deploying WENDELL Core 33..."
az containerapp create \
    --name "$CONTAINER_APP_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --environment "$CONTAINER_APP_ENV" \
    --image "${ACR_LOGIN_SERVER}/${IMAGE_NAME}:latest" \
    --registry-server "$ACR_LOGIN_SERVER" \
    --registry-username "$ACR_NAME" \
    --registry-password "$ACR_PASSWORD" \
    --target-port 5001 \
    --ingress external \
    --min-replicas 1 \
    --max-replicas 3 \
    --cpu 1.0 \
    --memory 2.0Gi \
    --env-vars \
        "RABBITMQ_HOST=localhost" \
        "RABBITMQ_PORT=5672" \
        "WENDELL_ENVIRONMENT=production" \
    --output none

# ── 6. Get URL ───────────────────────────────────────────────
FQDN=$(az containerapp show \
    --name "$CONTAINER_APP_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --query "properties.configuration.ingress.fqdn" -o tsv)

echo ""
echo "╔══════════════════════════════════════════════════╗"
echo "║  ✓ Deployment Complete                           ║"
echo "╠══════════════════════════════════════════════════╣"
echo "  URL            : https://${FQDN}"
echo "  Resource Group : ${RESOURCE_GROUP}"
echo "  ACR            : ${ACR_LOGIN_SERVER}"
echo "╚══════════════════════════════════════════════════╝"
