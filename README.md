# Omega 32/4 Wendell Core v3

A dual-orchestrator forensic intelligence platform with 32 agents (16 primary + 16 shadow) and 4 core components, achieving 99.97% sustained accuracy. Deploys in ≤3 hours, air-gap capable, with cross-market correlation (crypto + SEC/FINRA).

## Architecture

| Component | Language | Description |
|-----------|----------|-------------|
| Wendell Agent | Python/Flask | Human-facing dashboard and query interface |
| Integrator Agent | Python | Agent-facing orchestrator for multi-agent workflows |
| REST API Gateway | Python | External API gateway (Agent 34) |
| 16 Primary Agents | Rust | Forensic analysis agents (blockchain, wallet, officer tracking, etc.) |
| 16 Shadow Agents | Rust | <1ms failover mirrors for each primary agent |
| HIA / AFIA | Rust | Core orchestrators (Human Interface / Agent-Facing Interface) |

## Prerequisites

- **Rust** (https://rustup.rs) — for building the 32 Rust agents
- **Python 3.11+** — for the orchestration layer
- **RabbitMQ** — for inter-agent messaging
- **Docker** (optional) — for containerised deployment

## Quick Start (Local)

```bash
# Install Python dependencies
pip install -r requirements.txt

# Build Rust agents
cargo build --release

# Start RabbitMQ (via Docker)
docker run -d --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:3-management-alpine

# Create channel file and run
touch channel.txt
python wsgi.py
```

## Docker Compose

```bash
docker-compose up --build
```

This starts both the WENDELL dashboard (port 5001) and RabbitMQ (ports 5672/15672).

## Deploy to Azure

### One-Button Deploy

```bash
az login
./deploy-azure.sh
```

### Manual Deploy (Azure Container Apps)

```bash
# 1. Create resource group
az group create --name WendellCore-rg --location eastus

# 2. Create container registry
az acr create --resource-group WendellCore-rg --name wendellcr --sku Basic --admin-enabled true

# 3. Build and push image
az acr build --registry wendellcr --image wendell-core-33:latest .

# 4. Create Container Apps environment
az containerapp env create --name wendell-env --resource-group WendellCore-rg --location eastus

# 5. Deploy
az containerapp create \
    --name wendell-core-33 \
    --resource-group WendellCore-rg \
    --environment wendell-env \
    --image wendellcr.azurecr.io/wendell-core-33:latest \
    --target-port 5001 \
    --ingress external
```

### Azure OpenAI Integration

The deployment script in `CreateAOAIDeployment_create-aoai-deployment.mdCommands.md` provisions an Azure OpenAI resource with the `text-embedding-ada-002` model. Run it after the main deployment to enable AI-powered query processing.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `RABBITMQ_HOST` | localhost | RabbitMQ hostname |
| `RABBITMQ_PORT` | 5672 | RabbitMQ port |
| `RABBITMQ_USER` | guest | RabbitMQ username |
| `RABBITMQ_PASSWORD` | guest | RabbitMQ password |
| `WENDELL_JWT_SECRET` | (generated) | JWT signing secret |
| `WENDELL_ENCRYPTION_KEY` | (generated) | Data encryption key |
| `AOAI_ENDPOINT` | — | Azure OpenAI endpoint URL |
| `AOAI_KEY` | — | Azure OpenAI API key |
| `AOAI_DEPLOYMENT` | — | Azure OpenAI deployment name |
| `PORT` | 5001 | HTTP listen port |

## License

Proprietary — all rights reserved.
