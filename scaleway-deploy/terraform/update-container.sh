#!/bin/bash
set -e

# =============================================================================
# Scaleway Container Updater
# =============================================================================
# Usage: 
#   ./update-container.sh all       -> Builds all and updates all
#   ./update-container.sh backend   -> Builds backend and updates backend
# =============================================================================

# Configuration
REGION="fr-par"
API_URL="https://api.scaleway.com/containers/v1beta1/regions/${REGION}"
TERRAFORM_DIR="./terraform"

# List of all your services
ALL_SERVICES=("landing" "backend" "frontend")

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Check usage
if [ -z "$1" ]; then
    echo "Usage: $0 <service_name|all>"
    echo "Example: $0 all"
    echo "Example: $0 backend"
    exit 1
fi

TARGET="$1"

# Check Prerequisites
check_prerequisites() {
    local missing=()
    [ -z "$SCW_SECRET_KEY" ] && missing+=("SCW_SECRET_KEY")
    [ -z "$SCW_PROJECT_ID" ] && missing+=("SCW_PROJECT_ID")
    
    if [ ${#missing[@]} -gt 0 ]; then
        log_error "Missing environment variables: ${missing[*]}"
        echo "Please export them (e.g., export SCW_SECRET_KEY=...)"
        exit 1
    fi

    if ! command -v jq &> /dev/null; then
        log_error "jq is required but not installed. Please install jq (sudo apt install jq)."
        exit 1
    fi
}

# Get Namespace ID
get_namespace_id() {
    # Try to get from Terraform output first
    if [ -d "$TERRAFORM_DIR" ] && [ -f "$TERRAFORM_DIR/terraform.tfstate" ]; then
        NS_ID=$(cd "$TERRAFORM_DIR" && terraform output -raw container_namespace_id 2>/dev/null || echo "")
    fi

    # Fallback: Try to grep from tfvars
    if [ -z "$NS_ID" ] && [ -f "$TERRAFORM_DIR/terraform.tfvars" ]; then
        NS_ID=$(grep "container_namespace_id" "$TERRAFORM_DIR/terraform.tfvars" | cut -d'"' -f2)
    fi

    if [ -z "$NS_ID" ]; then
        log_error "Could not find Container Namespace ID."
        log_error "Please run './deploy.sh deploy' at least once or export SCW_NAMESPACE_ID manually."
        exit 1
    fi
    echo "$NS_ID"
}

# Deploy Logic for a Single Container
trigger_deploy() {
    local service_name=$1
    local ns_id=$2
    
    log_info "Finding Container ID for '$service_name'..."

    # Get Container ID by name
    CONTAINER_JSON=$(curl -s -H "X-Auth-Token: $SCW_SECRET_KEY" \
        "${API_URL}/containers?namespace_id=${ns_id}&page_size=100")

    CONTAINER_ID=$(echo "$CONTAINER_JSON" | jq -r ".containers[] | select(.name == \"$service_name\") | .id")

    if [ -z "$CONTAINER_ID" ] || [ "$CONTAINER_ID" == "null" ]; then
        log_warn "Container '$service_name' not found in namespace. Skipping."
        return
    fi

    log_info "Triggering Deploy for $service_name ($CONTAINER_ID)..."

    # Call Deploy Endpoint
    RESPONSE=$(curl -s -X POST \
        -H "X-Auth-Token: $SCW_SECRET_KEY" \
        -H "Content-Type: application/json" \
        "${API_URL}/containers/${CONTAINER_ID}/deploy" \
        -d '{}')

    STATUS=$(echo "$RESPONSE" | jq -r '.status')
    
    if [[ "$STATUS" == "pending" || "$STATUS" == "ready" || "$STATUS" == "creating" ]]; then
        log_info "✅ Deployment triggered for $service_name (Status: $STATUS)"
    else
        ERR_MSG=$(echo "$RESPONSE" | jq -r '.message // "Unknown error"')
        log_error "❌ Failed to deploy $service_name: $ERR_MSG"
    fi
}

# Main Execution Flow
check_prerequisites
NS_ID=$(get_namespace_id)

if [ "$TARGET" == "all" ]; then
    log_info "--- Processing ALL services ---"
    
    # 1. Build ALL images at once (more efficient)
    ./build-and-push.sh all
    
    # 2. Deploy ALL containers
    for SERVICE in "${ALL_SERVICES[@]}"; do
        echo "" # New line for readability
        trigger_deploy "$SERVICE" "$NS_ID"
    done

else
    log_info "--- Processing SINGLE service: $TARGET ---"
    
    # 1. Build Single image
    ./build-and-push.sh single "$TARGET"
    
    # 2. Deploy Single container
    trigger_deploy "$TARGET" "$NS_ID"
fi