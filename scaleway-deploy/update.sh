#!/bin/bash
set -e

# =============================================================================
# Quick Update Script
# =============================================================================
# Use this script to update containers after code changes
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TERRAFORM_DIR="${SCRIPT_DIR}/terraform"
TAG="${TAG:-latest}"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_step() { echo -e "${BLUE}[STEP]${NC} $1"; }

show_help() {
    echo "Usage: $0 [SERVICE] [OPTIONS]"
    echo ""
    echo "Update containers after code changes"
    echo ""
    echo "Services:"
    echo "  all             Update all services (default)"
    echo "  landing         Update landing page only"
    echo "  backend         Update backend only"
    echo "  frontend        Update frontend only"
    echo ""
    echo "Options:"
    echo "  --skip-build    Skip Docker build, only redeploy"
    echo "  --help          Show this help"
    echo ""
    echo "Examples:"
    echo "  $0                    # Update all services"
    echo "  $0 backend            # Update backend only"
    echo "  $0 backend --skip-build  # Redeploy backend without rebuild"
    echo "  TAG=v1.0.1 $0 all     # Build and deploy with specific tag"
    echo ""
}

update_single() {
    local service=$1
    local skip_build=$2
    
    log_step "Updating ${service}..."
    
    # Build and push if not skipped
    if [ "$skip_build" != "true" ]; then
        log_info "Building and pushing ${service}..."
        cd "${SCRIPT_DIR}/.."
        TAG="$TAG" "${SCRIPT_DIR}/build-and-push.sh" single "$service"
    fi
    
    # Redeploy with Terraform
    log_info "Redeploying ${service}..."
    cd "${TERRAFORM_DIR}"
    
    # Use timestamp to force redeployment
    terraform apply \
        -var="force_redeploy=$(date +%s)" \
        -target="scaleway_container.services[\"${service}\"]" \
        -auto-approve
    
    log_info "${service} updated successfully!"
}

update_all() {
    local skip_build=$1
    
    log_step "Updating all services..."
    
    # Build and push if not skipped
    if [ "$skip_build" != "true" ]; then
        log_info "Building and pushing all services..."
        cd "${SCRIPT_DIR}/.."
        TAG="$TAG" "${SCRIPT_DIR}/build-and-push.sh" all
    fi
    
    # Redeploy with Terraform
    log_info "Redeploying all services..."
    cd "${TERRAFORM_DIR}"
    
    terraform apply \
        -var="force_redeploy=$(date +%s)" \
        -auto-approve
    
    log_info "All services updated successfully!"
    
    # Show URLs
    echo ""
    log_info "Container URLs:"
    terraform output container_urls
}

# Parse arguments
SERVICE="all"
SKIP_BUILD="false"

while [[ $# -gt 0 ]]; do
    case $1 in
        landing|backend|frontend)
            SERVICE=$1
            shift
            ;;
        all)
            SERVICE="all"
            shift
            ;;
        --skip-build)
            SKIP_BUILD="true"
            shift
            ;;
        --help|-h)
            show_help
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Execute
if [ "$SERVICE" == "all" ]; then
    update_all "$SKIP_BUILD"
else
    update_single "$SERVICE" "$SKIP_BUILD"
fi
