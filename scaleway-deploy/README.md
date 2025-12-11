# Scaleway Serverless Containers Deployment

This directory contains scripts and Terraform configurations to build, push, and deploy Docker containers to Scaleway Serverless Containers.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Scaleway Infrastructure                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   Container Registry (rg.fr-par.scw.cloud/perso)                │
│   ┌─────────────┬─────────────┬─────────────┐                   │
│   │   landing   │   backend   │  frontend   │                   │
│   │   :latest   │   :latest   │   :latest   │                   │
│   └──────┬──────┴──────┬──────┴──────┬──────┘                   │
│          │             │             │                           │
│          ▼             ▼             ▼                           │
│   Serverless Container Namespace (e10c8558-...)                 │
│   ┌─────────────┬─────────────┬─────────────┐                   │
│   │   Landing   │   Backend   │  Frontend   │                   │
│   │   :80       │   :8000     │   :80       │                   │
│   └──────┬──────┴──────┬──────┴──────┬──────┘                   │
│          │             │             │                           │
│          ▼             ▼             ▼                           │
│   Custom Domains (optional):                                    │
│   https://www.outil-immo.fr    (Landing)                       │
│   https://api.outil-immo.fr     (Backend)                       │
│   https://app.outil-immo.fr     (Frontend)                      │
│                                                                  │
│   Or default Scaleway domains:                                  │
│   https://landing-xxx.containers.scw.cloud                      │
│   https://backend-xxx.containers.scw.cloud                      │
│   https://frontend-xxx.containers.scw.cloud                     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Link Configuration

The application uses the following URL structure in production:

- **Landing Page**: `https://www.outil-immo.fr`
  - Links to frontend: `https://app.outil-immo.fr`
- **Frontend**: `https://app.outil-immo.fr`
  - API calls to: `https://api.outil-immo.fr`
- **Backend**: `https://api.outil-immo.fr`

These URLs are configured:
- **Landing page links**: Hardcoded in HTML files
- **Frontend API URL**: Set via `VITE_API_BASE_URL` build argument

## Prerequisites

1. **Scaleway Account** with:
   - Container Registry namespace `perso` created
   - Serverless Container namespace created (ID: `e10c8558-99b7-4f45-a136-554d47120af0`)
   - API credentials (Access Key + Secret Key)

2. **Tools installed**:
   - Docker
   - Terraform >= 1.0.0
   - jq (for output parsing)

3. **Environment variables**:
   ```bash
   export SCW_ACCESS_KEY="your-access-key"
   export SCW_SECRET_KEY="your-secret-key"
   export SCW_PROJECT_ID="your-project-id"
   ```

## Quick Start

### Full Deployment (Build + Push + Deploy)

```bash
# From project root
cd scaleway-deploy
./deploy.sh all
```

### Quick Update (Recommended for daily use)

```bash
# Update all services
./scaleway-deploy/update-container.sh all

# Update only backend
./scaleway-deploy/update-container.sh backend

# Redeploy without rebuilding
./scaleway-deploy/update-container.sh frontend --skip-build
```

### Step-by-Step Deployment

```bash
# 1. Build and push Docker images
./build-and-push.sh all

# 2. Configure Terraform
cp terraform/terraform.tfvars.example terraform/terraform.tfvars
# Edit terraform.tfvars with your values

# 3. Deploy with Terraform
cd terraform
terraform init
terraform plan
terraform apply
```

## Scripts

### `update-container.sh` ⭐ (Recommended)

Quick update script for daily deployments. Combines build and Terraform apply in one command with service targeting.

```bash
# Update all services (build + deploy)
./update-container.sh all

# Update single service
./update-container.sh backend
./update-container.sh frontend
./update-container.sh landing

# Redeploy without rebuilding (config changes only)
./update-container.sh backend --skip-build

# Show help
./update-container.sh --help
```

**Features:**
- Targets specific services for faster deployments
- Uses timestamp to force container redeployment
- Can skip build phase for config-only changes
- Displays container URLs after deployment

### `build-and-push.sh`

Builds and pushes Docker images to Scaleway Container Registry.

```bash
# Build all images locally (no push)
./build-and-push.sh build

# Push all images
./build-and-push.sh push

# Build and push all
./build-and-push.sh all

# Build and push single service
./build-and-push.sh single backend

# Build with specific tag
TAG=v1.0.0 ./build-and-push.sh all

# Build frontend with custom API URL
VITE_API_BASE_URL=https://api.outil-immo.fr ./build-and-push.sh all

# Show image info
./build-and-push.sh info
```

**Environment Variables:**
- `TAG` - Docker image tag (default: `latest`)
- `VITE_API_BASE_URL` - API base URL for frontend (default: `https://api.outil-immo.fr`)
- `SCW_SECRET_KEY` - Required for registry authentication

### `deploy.sh`

Full deployment workflow combining Docker build and Terraform. Best for initial deployments or major changes.

```bash
# Full deployment
./deploy.sh all

# Build images only
./deploy.sh build

# Deploy only (skip build)
./deploy.sh deploy

# Show Terraform plan
./deploy.sh plan

# Show deployment info
./deploy.sh info

# Destroy all resources
./deploy.sh destroy
```

## Script Comparison

| Script | Use Case | Build | Push | Terraform | Service Targeting |
|--------|----------|-------|------|-----------|-------------------|
| `update-container.sh` | Daily updates | ✅ | ✅ | ✅ | ✅ |
| `build-and-push.sh` | Build/push only | ✅ | ✅ | ❌ | ✅ |
| `deploy.sh` | Full deployment | ✅ | ✅ | ✅ | ❌ |

**Recommendation:** Use `update-container.sh` for most operations, `deploy.sh` for initial setup or destroy.

## Terraform Configuration

### Files

| File | Description |
|------|-------------|
| `provider.tf` | Scaleway provider configuration |
| `variables.tf` | Variable definitions |
| `main.tf` | Container resources |
| `data.tf` | Data sources |
| `outputs.tf` | Output definitions |
| `terraform.tfvars` | Your configuration values |

### Key Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `project_id` | Scaleway project ID | (required) |
| `registry_namespace` | Registry namespace name | `perso` |
| `container_namespace_id` | Existing namespace ID | `e10c8558-...` |
| `image_tag` | Docker image tag | `latest` |
| `force_redeploy` | Timestamp to force redeployment | `""` |
| `create_container_namespace` | Create new namespace | `false` |

### Container Configuration

Each container can be configured with:

```hcl
containers = {
  backend = {
    description     = "FastAPI Backend service"
    port            = 8000
    min_scale       = 0       # 0 = scale to zero
    max_scale       = 10
    memory_limit    = 512     # MB
    cpu_limit       = 280     # millicores
    timeout         = "300s"
    max_concurrency = 50
    privacy         = "public"
    deploy          = true
    environment_variables        = {}
    secret_environment_variables = {}
  }
}
```

### Environment Variables

Pass environment variables to containers:

```hcl
# Non-sensitive
backend_env_vars = {
  API_BASE_URL = "https://api.example.com"
}

# Sensitive (stored securely)
backend_secret_env_vars = {
  OPENAI_API_KEY = "sk-..."
  DATABASE_URL   = "postgresql://..."
}
```

## Docker Registry Authentication

```bash
# Login to Scaleway Container Registry
docker login rg.fr-par.scw.cloud -u nologin --password-stdin <<< "$SCW_SECRET_KEY"
```

## Outputs

After deployment, Terraform outputs:

- `container_urls` - URLs for all containers
- `landing_url` - Landing page URL
- `backend_url` - Backend API URL
- `frontend_url` - Frontend app URL

```bash
# View outputs
cd terraform
terraform output

# Get specific URL
terraform output backend_url
```

## Common Operations

### Update a Single Service (Recommended)

```bash
# Quickest way - build, push, and deploy
./update-container.sh backend
```

### Update Without Rebuild

```bash
# Just redeploy (e.g., after config change in Terraform)
./update-container.sh backend --skip-build
```

### Deploy with Specific Tag

```bash
TAG=v1.0.0 ./deploy.sh all
```

### Force Redeployment (Alternative method)

```bash
# Taint the resource to force recreation
cd terraform
terraform taint 'scaleway_container.services["backend"]'
terraform apply
```

### View Container URLs

```bash
./update-container.sh --skip-build  # Will show URLs at the end

# Or directly via Terraform
cd terraform && terraform output container_urls
```

## Troubleshooting

### Image Not Found

Ensure the image exists in the registry:
```bash
docker pull rg.fr-par.scw.cloud/perso/backend:latest
```

### Container Won't Start

Check container logs in Scaleway Console or via CLI:
```bash
scw container container logs <container-id>
```

### Authentication Issues

Verify your credentials:
```bash
scw account whoami
```

### Build Fails on macOS (ARM)

The scripts use `docker buildx` for cross-platform builds (ARM → AMD64). If buildx isn't working:
```bash
# Create/reset the multiarch builder
docker buildx create --name multiarch --use --bootstrap
```

## Cost Optimization

- Set `min_scale = 0` to scale to zero when not in use
- Adjust `memory_limit` and `cpu_limit` based on actual usage
- Use appropriate `max_scale` to control maximum costs

## Security Notes

1. Never commit `terraform.tfvars` with secrets
2. Use `secret_environment_variables` for sensitive data
3. Consider using `privacy = "private"` for internal services
4. Rotate API keys regularly

## File Structure

```
scaleway-deploy/
├── README.md              # This file
├── build-and-push.sh      # Docker build & push script
├── deploy.sh              # Full deployment script
├── update-container.sh    # Quick update script ⭐
└── terraform/
    ├── provider.tf
    ├── variables.tf
    ├── main.tf
    ├── data.tf
    ├── outputs.tf
    └── terraform.tfvars.example
```