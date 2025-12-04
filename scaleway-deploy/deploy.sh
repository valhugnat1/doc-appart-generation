#!/bin/bash
set -e

# =============================================================================
# Full Deployment Script
# =============================================================================
# This script handles the complete deployment workflow:
# 1. Build Docker images
# 2. Push to Scaleway Container Registry
# 3. Deploy to Scaleway Serverless Containers using Terraform
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TERRAFORM_DIR="${SCRIPT_DIR}/terraform"
TAG="${TAG:-latest}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_step() { echo -e "${BLUE}[STEP]${NC} $1"; }

# Check required environment variables
check_env() {
    log_step "Checking environment variables..."
    
    local missing=()
    
    [ -z "$SCW_ACCESS_KEY" ] && missing+=("SCW_ACCESS_KEY")
    [ -z "$SCW_SECRET_KEY" ] && missing+=("SCW_SECRET_KEY")
    [ -z "$SCW_PROJECT_ID" ] && missing+=("SCW_PROJECT_ID")
    
    if [ ${#missing[@]} -gt 0 ]; then
        log_error "Missing required environment variables:"
        for var in "${missing[@]}"; do
            echo "  - $var"
        done
        echo ""
        echo "Please set them with:"
        echo "  export SCW_ACCESS_KEY=your-access-key"
        echo "  export SCW_SECRET_KEY=your-secret-key"
        echo "  export SCW_PROJECT_ID=your-project-id"
        exit 1
    fi
    
    log_info "All required environment variables are set"
}

# Check required tools
check_tools() {
    log_step "Checking required tools..."
    
    local missing=()
    
    command -v docker &> /dev/null || missing+=("docker")
    command -v terraform &> /dev/null || missing+=("terraform")
    
    if [ ${#missing[@]} -gt 0 ]; then
        log_error "Missing required tools:"
        for tool in "${missing[@]}"; do
            echo "  - $tool"
        done
        exit 1
    fi
    
    log_info "All required tools are installed"
}

# Build and push Docker images
build_and_push() {
    log_step "Building and pushing Docker images..."
    
    # Go to project root (parent of script directory)
    cd "${SCRIPT_DIR}/.."
    
    # Run build and push script
    TAG="$TAG" "${SCRIPT_DIR}/build-and-push.sh" all
    
    cd "${SCRIPT_DIR}"
}

# Initialize Terraform
terraform_init() {
    log_step "Initializing Terraform..."
    
    cd "${TERRAFORM_DIR}"
    terraform init -upgrade
}

# Create terraform.tfvars if it doesn't exist
ensure_tfvars() {
    if [ ! -f "${TERRAFORM_DIR}/terraform.tfvars" ]; then
        log_warn "terraform.tfvars not found, creating from environment variables..."
        
        cat > "${TERRAFORM_DIR}/terraform.tfvars" <<EOF
# Auto-generated terraform.tfvars
project_id = "${SCW_PROJECT_ID}"
region = "fr-par"
zone = "fr-par-1"
registry_namespace = "perso"
registry_endpoint = "rg.fr-par.scw.cloud"
create_container_namespace = false
container_namespace_id = "e10c8558-99b7-4f45-a136-554d47120af0"
image_tag = "${TAG}"
EOF
        log_info "Created terraform.tfvars"
    fi
}

# Plan Terraform changes
terraform_plan() {
    log_step "Planning Terraform changes..."
    
    cd "${TERRAFORM_DIR}"
    terraform plan -out=tfplan
}

# Apply Terraform changes
terraform_apply() {
    log_step "Applying Terraform changes..."
    
    cd "${TERRAFORM_DIR}"
    
    if [ -f "tfplan" ]; then
        terraform apply tfplan
        rm -f tfplan
    else
        terraform apply -auto-approve
    fi
}

# Show deployment info
show_info() {
    log_step "Deployment Information"
    
    cd "${TERRAFORM_DIR}"
    
    echo ""
    echo "=== Container URLs ==="
    terraform output -json container_urls 2>/dev/null | jq -r 'to_entries[] | "  \(.key): \(.value)"' || echo "  (run terraform apply first)"
    echo ""
}

# Destroy deployment
destroy() {
    log_warn "This will destroy all deployed containers!"
    read -p "Are you sure? (yes/no): " confirm
    
    if [ "$confirm" == "yes" ]; then
        cd "${TERRAFORM_DIR}"
        terraform destroy
    else
        log_info "Destroy cancelled"
    fi
}

# Show help
show_help() {
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  all             Full deployment: build, push, and deploy (default)"
    echo "  build           Build and push Docker images only"
    echo "  deploy          Deploy with Terraform only (skip build)"
    echo "  plan            Show Terraform plan without applying"
    echo "  info            Show current deployment information"
    echo "  destroy         Destroy all deployed resources"
    echo "  help            Show this help message"
    echo ""
    echo "Environment variables:"
    echo "  SCW_ACCESS_KEY   Scaleway access key"
    echo "  SCW_SECRET_KEY   Scaleway secret key"
    echo "  SCW_PROJECT_ID   Scaleway project ID"
    echo "  TAG              Docker image tag (default: latest)"
    echo ""
    echo "Examples:"
    echo "  $0 all                    # Full deployment"
    echo "  $0 build                  # Build images only"
    echo "  TAG=v1.0.0 $0 all         # Deploy with specific tag"
    echo ""
}

# Main
main() {
    local command=${1:-all}
    
    case $command in
        all)
            check_env
            check_tools
            build_and_push
            ensure_tfvars
            terraform_init
            terraform_plan
            terraform_apply
            show_info
            log_info "Deployment complete!"
            ;;
        build)
            check_env
            check_tools
            build_and_push
            ;;
        deploy)
            check_env
            check_tools
            ensure_tfvars
            terraform_init
            terraform_plan
            terraform_apply
            show_info
            ;;
        plan)
            check_env
            check_tools
            ensure_tfvars
            terraform_init
            terraform_plan
            ;;
        info)
            show_info
            ;;
        destroy)
            check_env
            check_tools
            terraform_init
            destroy
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            log_error "Unknown command: $command"
            show_help
            exit 1
            ;;
    esac
}

main "$@"
