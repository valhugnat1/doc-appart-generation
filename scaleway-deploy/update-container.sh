#!/bin/bash
set -e

# =============================================================================
# Script de Mise à Jour Scaleway
# Situé dans scaleway-deploy/ - peut être exécuté depuis n'importe où
# =============================================================================

# Définition des chemins
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
TERRAFORM_DIR="${SCRIPT_DIR}/terraform"
BUILD_SCRIPT="${SCRIPT_DIR}/build-and-push.sh"

# Couleurs
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_step() { echo -e "\n${BLUE}[STEP]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }

# Vérification des fichiers requis
check_prerequisites() {
    if [ ! -d "$TERRAFORM_DIR" ]; then
        log_error "Dossier Terraform introuvable : $TERRAFORM_DIR"
        exit 1
    fi

    if [ ! -f "$BUILD_SCRIPT" ]; then
        log_error "Script de build introuvable : $BUILD_SCRIPT"
        exit 1
    fi

    # Vérifier les variables d'environnement Scaleway
    if [ -z "$SCW_SECRET_KEY" ]; then
        log_error "SCW_SECRET_KEY non définie"
        echo "  export SCW_SECRET_KEY=your-secret-key"
        exit 1
    fi
}

show_help() {
    echo "Usage: $0 [SERVICE] [OPTIONS]"
    echo ""
    echo "Services:"
    echo "  all             Met à jour tous les services (défaut)"
    echo "  backend         Met à jour le backend"
    echo "  frontend        Met à jour le frontend"
    echo "  landing         Met à jour la landing page"
    echo ""
    echo "Options:"
    echo "  --skip-build    Ne reconstruit pas l'image Docker (redeploy config uniquement)"
    echo "  -h, --help      Affiche cette aide"
    echo ""
    echo "Exemples:"
    echo "  $0 all                    # Build et déploie tous les services"
    echo "  $0 backend                # Build et déploie seulement le backend"
    echo "  $0 frontend --skip-build  # Redéploie le frontend sans rebuild"
    echo ""
}

# --- Gestion des arguments ---
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
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            log_error "Option inconnue: $1"
            show_help
            exit 1
            ;;
    esac
done

# --- Main ---
main() {
    check_prerequisites

    echo ""
    echo "=========================================="
    echo "  Mise à jour Scaleway - Service: $SERVICE"
    echo "=========================================="
    echo ""

    # --- Build & Push ---
    if [ "$SKIP_BUILD" != "true" ]; then
        log_step "Construction et Push des images Docker..."

        chmod +x "$BUILD_SCRIPT"

        # Se placer à la racine du projet pour le build
        cd "$PROJECT_ROOT"

        if [ "$SERVICE" == "all" ]; then
            "$BUILD_SCRIPT" all
        else
            "$BUILD_SCRIPT" single "$SERVICE"
        fi
    else
        log_warn "Skip Build demandé. On passe directement au déploiement."
    fi

    # --- Terraform Apply (Redéploiement) ---
    log_step "Application des changements Terraform..."

    cd "$TERRAFORM_DIR"

    # Génération du timestamp pour forcer la mise à jour
    TIMESTAMP=$(date +%s)

    if [ "$SERVICE" == "all" ]; then
        echo "Déploiement de tous les services..."
        terraform apply \
            -var="force_redeploy=$TIMESTAMP" \
            -auto-approve
    else
        echo "Ciblage du service : $SERVICE"
        terraform apply \
            -var="force_redeploy=$TIMESTAMP" \
            -target="scaleway_container.services[\"$SERVICE\"]" \
            -auto-approve
    fi

    log_success "Mise à jour terminée avec succès !"

    # Afficher les URLs
    echo ""
    echo "=== URLs des containers ==="
    terraform output -json container_urls 2>/dev/null | jq -r 'to_entries[] | "  \(.key): \(.value)"' || true
    echo ""
}

main "$@"