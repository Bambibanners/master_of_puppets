#!/usr/bin/env bash
# Master of Puppets - Universal Installer (v1.0) - Linux/macOS
# Usage:
#   curl -sSL https://server:8001/api/installer.sh | bash -s -- --token "eyJ..."
#   ./install_universal.sh --token "eyJ..." --count 3
#   ./install_universal.sh --platform docker  # Force Docker

set -euo pipefail

# --- Defaults ---
ROLE="node"
TOKEN=""
SERVER_URL="https://localhost:8001"
COUNT=1
PLATFORM=""

# --- Color Helpers ---
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

log() {
    echo -e "${CYAN}[Installer]${NC} $1"
}

log_green() {
    echo -e "${GREEN}[Installer]${NC} $1"
}

log_error() {
    echo -e "${RED}[Error]${NC} $1" >&2
    exit 1
}

# --- Argument Parsing ---
while [[ $# -gt 0 ]]; do
    case $1 in
        --role)
            ROLE="$2"
            shift 2
            ;;
        --token)
            TOKEN="$2"
            shift 2
            ;;
        --server)
            SERVER_URL="$2"
            shift 2
            ;;
        --count)
            COUNT="$2"
            shift 2
            ;;
        --platform)
            PLATFORM="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# --- Platform Detection ---
HAS_DOCKER=$(command -v docker &>/dev/null && echo 1 || echo 0)
HAS_PODMAN=$(command -v podman &>/dev/null && echo 1 || echo 0)

if [[ -z "$PLATFORM" ]]; then
    # Auto-detect
    if [[ $HAS_DOCKER -eq 0 && $HAS_PODMAN -eq 0 ]]; then
        log_error "Neither Docker nor Podman found. Please install one first."
    elif [[ $HAS_DOCKER -eq 1 && $HAS_PODMAN -eq 1 ]]; then
        echo ""
        echo -e "${YELLOW}Both Docker and Podman detected. Please choose:${NC}"
        echo -e "  ${CYAN}[1] Docker${NC}"
        echo -e "  ${CYAN}[2] Podman${NC}"
        read -p "Select runtime [1/2]: " CHOICE
        if [[ "$CHOICE" == "2" ]]; then
            PLATFORM="podman"
        else
            PLATFORM="docker"
        fi
    elif [[ $HAS_DOCKER -eq 1 ]]; then
        PLATFORM="docker"
        log_green "Auto-detected: Docker"
    else
        PLATFORM="podman"
        log_green "Auto-detected: Podman"
    fi
else
    log "Using specified platform: $PLATFORM"
fi

# Normalize to lowercase
PLATFORM=$(echo "$PLATFORM" | tr '[:upper:]' '[:lower:]')

log "Initializing Universal Installer ($ROLE on $PLATFORM)..."

# --- Validate Platform ---
if [[ "$PLATFORM" == "podman" ]]; then
    if [[ $HAS_PODMAN -eq 0 ]]; then
        log_error "Podman is not installed."
    fi
    # Check for podman-compose
    if ! command -v podman-compose &>/dev/null; then
        log_error "podman-compose is not installed. Install with: pip install podman-compose"
    fi
elif [[ "$PLATFORM" == "docker" ]]; then
    if [[ $HAS_DOCKER -eq 0 ]]; then
        log_error "Docker is not installed."
    fi
    # Check for docker compose (plugin) or docker-compose
    if ! docker compose version &>/dev/null && ! command -v docker-compose &>/dev/null; then
        log_error "Docker Compose is not found (checked 'docker compose' and 'docker-compose')."
    fi
fi

# --- Token Handling (Node Role) ---
if [[ "$ROLE" == "node" ]]; then
    if [[ -z "$TOKEN" ]]; then
        read -p "Enter Join Token: " TOKEN
    fi

    log "Parsing Token..."
    # Decode Base64 token and extract CA
    JSON_PAYLOAD=$(echo "$TOKEN" | base64 -d 2>/dev/null || echo "")
    if [[ -z "$JSON_PAYLOAD" ]]; then
        log_error "Invalid Token Format. Ensure you are using a v0.8+ Token."
    fi

    # Extract CA using jq if available, otherwise grep/sed
    if command -v jq &>/dev/null; then
        CA_CONTENT=$(echo "$JSON_PAYLOAD" | jq -r '.ca // empty')
    else
        # Fallback: simple grep (fragile)
        CA_CONTENT=$(echo "$JSON_PAYLOAD" | grep -o '"ca":"[^"]*"' | cut -d'"' -f4 | sed 's/\\n/\n/g')
    fi

    if [[ -z "$CA_CONTENT" ]]; then
        log_error "Could not extract CA from token."
    fi

    echo "$CA_CONTENT" > bootstrap_ca.crt
    log_green "✅ Trust Root extracted to bootstrap_ca.crt"
fi

# --- Fetch Configuration ---
if [[ "$ROLE" == "node" ]]; then
    log "Fetching Node Configuration..."
    COMPOSE_URL="${SERVER_URL}/api/node/compose?token=${TOKEN}&platform=${PLATFORM}"
    
    curl -sSfL --cacert bootstrap_ca.crt "$COMPOSE_URL" -o node-compose.yaml || \
        curl -sSfLk "$COMPOSE_URL" -o node-compose.yaml  # Fallback insecure if CA fails
    
    log_green "✅ node-compose.yaml downloaded."

    log "Fetching Validation Key..."
    KEY_URL="${SERVER_URL}/api/verification-key"
    curl -sSfL --cacert bootstrap_ca.crt "$KEY_URL" -o verification.key || \
        curl -sSfLk "$KEY_URL" -o verification.key || echo "Warning: Could not fetch verification key."
    
    if [[ -s verification.key ]]; then
        log_green "✅ Verification Key downloaded."
    fi
elif [[ "$ROLE" == "agent" ]]; then
    log "Agent (Server) deployment not yet fully automated via script (Use git clone + compose)."
    exit 0
fi

# --- Deployment ---
log "Starting Containers (x$COUNT) using $PLATFORM..."

if [[ "$PLATFORM" == "podman" ]]; then
    podman-compose -f node-compose.yaml up -d --scale node="$COUNT"
elif [[ "$PLATFORM" == "docker" ]]; then
    # Prefer 'docker compose' (plugin)
    if docker compose version &>/dev/null; then
        docker compose -f node-compose.yaml up -d --scale node="$COUNT"
    else
        docker-compose -f node-compose.yaml up -d --scale node="$COUNT"
    fi
fi

if [[ $? -eq 0 ]]; then
    log_green "🚀 Deployment Complete!"
    if [[ "$PLATFORM" == "podman" ]]; then
        log "Run 'podman logs -f <container_name>' to view status."
    else
        log "Run 'docker logs -f <container_name>' to view status."
    fi
else
    log_error "Deployment failed."
fi
