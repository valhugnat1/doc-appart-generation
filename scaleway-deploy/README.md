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
│   https://landing-xxx.containers.scw.cloud                      │
│   https://backend-xxx.containers.scw.cloud                      │
│   https://frontend-xxx.containers.scw.cloud                     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Prerequisites

1. **Scaleway Account** with:
   - Container Registry namespace `perso` created
   - Serverless Container namespace created (ID: `e10c8558-99b7-4f45-a136-554d47120af0`)
   - API credentials (Access Key + Secret Key)

2. **Tools installed**:
   - Docker
   - Terraform >= 1.0.0

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

### `build-and-push.sh`

Builds and pushes Docker images to Scaleway Container Registry.

```bash
# Build all images
./build-and-push.sh build

# Push all images
./build-and-push.sh push

# Build and push all
./build-and-push.sh all

# Build and push single service
./build-and-push.sh single backend

# Build with specific tag
TAG=v1.0.0 ./build-and-push.sh all
```

### `deploy.sh`

Full deployment workflow combining Docker build and Terraform.

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

## Terraform Configuration

### Files

| File | Description |
|------|-------------|
| `provider.tf` | Scaleway provider configuration |
| `variables.tf` | Variable definitions |
| `main.tf` | Container resources |
| `outputs.tf` | Output definitions |
| `terraform.tfvars` | Your configuration values |

### Key Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `project_id` | Scaleway project ID | (required) |
| `registry_namespace` | Registry namespace name | `perso` |
| `container_namespace_id` | Existing namespace ID | `e10c8558-...` |
| `image_tag` | Docker image tag | `latest` |
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
terraform output

# Get specific URL
terraform output backend_url
```

## Common Operations

### Update a Single Service

```bash
# Rebuild and push only backend
./build-and-push.sh single backend

# Redeploy
cd terraform
terraform apply -target=scaleway_container.services[\"backend\"]
```

### Deploy with Specific Tag

```bash
TAG=v1.0.0 ./deploy.sh all
```

### Force Redeployment

The container's `deploy` attribute triggers redeployment. You can also:

```bash
# Taint the resource to force recreation
terraform taint 'scaleway_container.services["backend"]'
terraform apply
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

## Cost Optimization

- Set `min_scale = 0` to scale to zero when not in use
- Adjust `memory_limit` and `cpu_limit` based on actual usage
- Use appropriate `max_scale` to control maximum costs

## Security Notes

1. Never commit `terraform.tfvars` with secrets
2. Use `secret_environment_variables` for sensitive data
3. Consider using `privacy = "private"` for internal services
4. Rotate API keys regularly
