#!/bin/bash
set -e

# =============================================================================
# Scaleway Container Registry - Build and Push Script
# =============================================================================
# This script builds Docker images for all services and pushes them to
# Scaleway Container Registry
# =============================================================================

# Configuration
REGISTRY="rg.fr-par.scw.cloud"
NAMESPACE="perso"
TAG="${TAG:-latest}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Services to build (name:context:dockerfile)
SERVICES=(
    "landing:./landing:Dockerfile"
    "backend:./backend:Dockerfile"
    "frontend:./frontend:Dockerfile"
)

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check if buildx is available
    if ! docker buildx version &> /dev/null; then
        log_error "Docker buildx is not available. Please install/enable buildx."
        log_info "On Docker Desktop, buildx is included by default."
        exit 1
    fi
    
    # Ensure buildx builder exists for cross-platform builds
    if ! docker buildx inspect multiarch &> /dev/null; then
        log_info "Creating multiarch builder..."
        docker buildx create --name multiarch --use --bootstrap
    else
        docker buildx use multiarch
    fi
    
    # Check if logged in to Scaleway Registry
    if ! docker info 2>/dev/null | grep -q "Username"; then
        log_warn "You may need to login to Scaleway Registry"
        log_info "Run: docker login ${REGISTRY} -u nologin --password-stdin <<< \"\$SCW_SECRET_KEY\""
    fi
}

login_to_registry() {
    log_info "Logging in to Scaleway Container Registry..."
    
    if [ -z "$SCW_SECRET_KEY" ]; then
        log_error "SCW_SECRET_KEY environment variable is not set"
        log_info "Please set it with: export SCW_SECRET_KEY=your-secret-key"
        exit 1
    fi
    
    echo "$SCW_SECRET_KEY" | docker login "${REGISTRY}" -u nologin --password-stdin
    
    if [ $? -eq 0 ]; then
        log_info "Successfully logged in to ${REGISTRY}"
    else
        log_error "Failed to login to registry"
        exit 1
    fi
}

build_image() {
    local service_name=$1
    local context=$2
    local dockerfile=$3
    local full_image="${REGISTRY}/${NAMESPACE}/${service_name}:${TAG}"
    
    log_info "Building image: ${full_image}"
    log_info "  Context: ${context}"
    log_info "  Dockerfile: ${dockerfile}"
    log_info "  Platform: linux/amd64"
    
    # Use buildx for cross-platform builds (macOS ARM -> Linux AMD64)
    docker buildx build \
        --platform linux/amd64 \
        -t "${full_image}" \
        -f "${context}/${dockerfile}" \
        --push \
        "${context}"
    
    if [ $? -eq 0 ]; then
        log_info "Successfully built and pushed ${full_image}"
    else
        log_error "Failed to build ${service_name}"
        exit 1
    fi
}

push_image() {
    local service_name=$1
    local full_image="${REGISTRY}/${NAMESPACE}/${service_name}:${TAG}"
    
    # With buildx --push, images are pushed during build
    # This function is kept for standalone push operations
    log_info "Pushing image: ${full_image}"
    
    docker push "${full_image}"
    
    if [ $? -eq 0 ]; then
        log_info "Successfully pushed ${full_image}"
    else
        log_error "Failed to push ${service_name}"
        exit 1
    fi
}

build_image_local() {
    # Build locally without push (for testing)
    local service_name=$1
    local context=$2
    local dockerfile=$3
    local full_image="${REGISTRY}/${NAMESPACE}/${service_name}:${TAG}"
    
    log_info "Building image locally: ${full_image}"
    log_info "  Context: ${context}"
    log_info "  Dockerfile: ${dockerfile}"
    log_info "  Platform: linux/amd64"
    
    docker buildx build \
        --platform linux/amd64 \
        -t "${full_image}" \
        -f "${context}/${dockerfile}" \
        --load \
        "${context}"
    
    if [ $? -eq 0 ]; then
        log_info "Successfully built ${full_image}"
    else
        log_error "Failed to build ${service_name}"
        exit 1
    fi
}

build_all() {
    log_info "Building all services (local only)..."
    
    for service in "${SERVICES[@]}"; do
        IFS=':' read -r name context dockerfile <<< "$service"
        build_image_local "$name" "$context" "$dockerfile"
    done
    
    log_info "All images built successfully!"
}

build_and_push_all() {
    log_info "Building and pushing all services..."
    
    for service in "${SERVICES[@]}"; do
        IFS=':' read -r name context dockerfile <<< "$service"
        build_image "$name" "$context" "$dockerfile"
    done
    
    log_info "All images built and pushed successfully!"
}

push_all() {
    log_info "Pushing all services..."
    
    for service in "${SERVICES[@]}"; do
        IFS=':' read -r name context dockerfile <<< "$service"
        push_image "$name"
    done
    
    log_info "All images pushed successfully!"
}

build_and_push_single() {
    local target_service=$1
    
    for service in "${SERVICES[@]}"; do
        IFS=':' read -r name context dockerfile <<< "$service"
        if [ "$name" == "$target_service" ]; then
            build_image "$name" "$context" "$dockerfile"
            push_image "$name"
            return 0
        fi
    done
    
    log_error "Service '${target_service}' not found. Available: landing, backend, frontend"
    exit 1
}

get_image_digest() {
    local service_name=$1
    local full_image="${REGISTRY}/${NAMESPACE}/${service_name}:${TAG}"
    
    # Get the digest after push
    docker inspect --format='{{index .RepoDigests 0}}' "${full_image}" 2>/dev/null | cut -d'@' -f2
}

print_images_info() {
    log_info "Image information:"
    echo ""
    for service in "${SERVICES[@]}"; do
        IFS=':' read -r name context dockerfile <<< "$service"
        local full_image="${REGISTRY}/${NAMESPACE}/${name}:${TAG}"
        echo "  ${name}:"
        echo "    Image: ${full_image}"
        local digest=$(get_image_digest "$name")
        if [ -n "$digest" ]; then
            echo "    Digest: ${digest}"
        fi
        echo ""
    done
}

show_help() {
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  build           Build all Docker images"
    echo "  push            Push all Docker images to registry"
    echo "  all             Build and push all images (default)"
    echo "  single <name>   Build and push a single service"
    echo "  login           Login to Scaleway Container Registry"
    echo "  info            Show image information"
    echo "  help            Show this help message"
    echo ""
    echo "Options:"
    echo "  TAG=<tag>       Set image tag (default: latest)"
    echo ""
    echo "Environment variables:"
    echo "  SCW_SECRET_KEY  Scaleway secret key for registry authentication"
    echo ""
    echo "Examples:"
    echo "  $0 all                    # Build and push all services"
    echo "  $0 single backend         # Build and push only backend"
    echo "  TAG=v1.0.0 $0 all         # Build and push with specific tag"
    echo ""
}

# Main
main() {
    local command=${1:-all}
    
    case $command in
        build)
            check_prerequisites
            build_all
            ;;
        push)
            check_prerequisites
            login_to_registry
            push_all
            ;;
        all)
            check_prerequisites
            login_to_registry
            build_and_push_all
            print_images_info
            ;;
        single)
            if [ -z "$2" ]; then
                log_error "Please specify a service name"
                show_help
                exit 1
            fi
            check_prerequisites
            login_to_registry
            build_and_push_single "$2"
            ;;
        login)
            login_to_registry
            ;;
        info)
            print_images_info
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