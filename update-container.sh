#!/bin/bash
set -e

# =============================================================================
# Script de Mise à Jour Scaleway
# Doit être exécuté depuis la racine du projet
# =============================================================================

# Définition des chemins (Basé sur ta structure 'tree')
# SCRIPT_DIR est la racine du projet si ce script est à la racine
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Chemins vers les sous-dossiers
TERRAFORM_DIR="${PROJECT_ROOT}/scaleway-deploy/terraform"
BUILD_SCRIPT="${PROJECT_ROOT}/scaleway-deploy/build-and-push.sh"

# Couleurs
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

log_step() { echo -e "\n${BLUE}[STEP]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Vérification des fichiers requis
if [ ! -d "$TERRAFORM_DIR" ]; then
    log_error "Dossier Terraform introuvable : $TERRAFORM_DIR"
    exit 1
fi

if [ ! -f "$BUILD_SCRIPT" ]; then
    log_error "Script de build introuvable : $BUILD_SCRIPT"
    exit 1
fi

show_help() {
    echo "Usage: ./update.sh [SERVICE] [OPTIONS]"
    echo ""
    echo "Services:"
    echo "  all             Met à jour tous les services (défaut)"
    echo "  backend         Met à jour le backend"
    echo "  frontend        Met à jour le frontend"
    echo "  landing         Met à jour la landing page"
    echo ""
    echo "Options:"
    echo "  --skip-build    Ne reconstruit pas l'image Docker (Redeploy config uniquement)"
    echo "  -h, --help      Affiche cette aide"
}

# --- 1. Gestion des arguments ---
SERVICE="all"
SKIP_BUILD="false"

while [[ $# -gt 0 ]]; do
    case $1 in
        landing|backend|frontend) SERVICE=$1; shift ;;
        all) SERVICE="all"; shift ;;
        --skip-build) SKIP_BUILD="true"; shift ;;
        -h|--help) show_help; exit 0 ;;
        *) echo "Option inconnue: $1"; show_help; exit 1 ;;
    esac
done

# --- 2. Build & Push ---
if [ "$SKIP_BUILD" != "true" ]; then
    log_step "Construction et Push des images Docker..."
    
    # On rend le script de build exécutable au cas où
    chmod +x "$BUILD_SCRIPT"
    
    # On exécute le script de build. 
    # NOTE: On passe le relai au script existant situé dans scaleway-deploy
    "$BUILD_SCRIPT" "$SERVICE"
else
    log_step "Skip Build demandé. On passe directement au déploiement."
fi

# --- 3. Terraform Apply (Redéploiement) ---
log_step "Application des changements Terraform..."

# On se déplace dans le dossier Terraform car Terraform a besoin d'être 
# dans le dossier contenant main.tf pour gérer son .terraform/ et tfstate
cd "$TERRAFORM_DIR"

# Génération du timestamp pour forcer la mise à jour
TIMESTAMP=$(date +%s)

CMD="terraform apply -var=\"force_redeploy=$TIMESTAMP\" -auto-approve"

if [ "$SERVICE" != "all" ]; then
    echo "Ciblage du service : $SERVICE"
    # Ciblage spécifique de la ressource
    CMD="$CMD -target=\"scaleway_container.services[\\\"$SERVICE\\\"]\""
fi

# Exécution
echo "Exécution : $CMD"
eval "$CMD"

log_success "Mise à jour terminée avec succès !"