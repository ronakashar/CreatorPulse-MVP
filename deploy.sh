#!/bin/bash
set -e

# CreatorPulse Production Deployment Script
# This script handles the complete deployment process for production

echo "🚀 CreatorPulse Production Deployment"
echo "======================================"

# Configuration
APP_NAME="creatorpulse"
DOCKER_COMPOSE_FILE="docker-compose.prod.yml"
BACKUP_DIR="/backups"
LOG_FILE="deployment.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a $LOG_FILE
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a $LOG_FILE
    exit 1
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a $LOG_FILE
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   error "This script should not be run as root"
fi

# Check required tools
check_requirements() {
    log "Checking requirements..."
    
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed"
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose is not installed"
    fi
    
    if ! command -v git &> /dev/null; then
        error "Git is not installed"
    fi
    
    log "All requirements satisfied"
}

# Check environment variables
check_environment() {
    log "Checking environment variables..."
    
    required_vars=(
        "SUPABASE_URL"
        "SUPABASE_KEY"
        "GROQ_API_KEY"
        "RESEND_API_KEY"
        "STRIPE_SECRET_KEY"
        "SENTRY_DSN"
    )
    
    missing_vars=()
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var}" ]]; then
            missing_vars+=("$var")
        fi
    done
    
    if [[ ${#missing_vars[@]} -gt 0 ]]; then
        error "Missing required environment variables: ${missing_vars[*]}"
    fi
    
    log "Environment variables validated"
}

# Create backup
create_backup() {
    log "Creating backup..."
    
    BACKUP_TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    BACKUP_PATH="$BACKUP_DIR/backup_$BACKUP_TIMESTAMP"
    
    mkdir -p "$BACKUP_PATH"
    
    # Backup database
    if command -v supabase &> /dev/null; then
        log "Backing up database..."
        supabase db dump --file "$BACKUP_PATH/database.sql" || warning "Database backup failed"
    fi
    
    # Backup uploaded files
    if [[ -d "uploads" ]]; then
        log "Backing up uploaded files..."
        cp -r uploads "$BACKUP_PATH/" || warning "File backup failed"
    fi
    
    # Backup configuration
    if [[ -f ".env" ]]; then
        cp .env "$BACKUP_PATH/" || warning "Config backup failed"
    fi
    
    # Compress backup
    tar -czf "$BACKUP_PATH.tar.gz" -C "$BACKUP_DIR" "backup_$BACKUP_TIMESTAMP"
    rm -rf "$BACKUP_PATH"
    
    log "Backup created: $BACKUP_PATH.tar.gz"
}

# Pull latest code
update_code() {
    log "Updating code..."
    
    # Stash any local changes
    git stash || true
    
    # Pull latest changes
    git pull origin main || error "Failed to pull latest code"
    
    log "Code updated successfully"
}

# Build and deploy
deploy() {
    log "Building and deploying application..."
    
    # Stop existing containers
    docker-compose -f $DOCKER_COMPOSE_FILE down || warning "Failed to stop existing containers"
    
    # Build new images
    docker-compose -f $DOCKER_COMPOSE_FILE build --no-cache || error "Build failed"
    
    # Start services
    docker-compose -f $DOCKER_COMPOSE_FILE up -d || error "Deployment failed"
    
    log "Application deployed successfully"
}

# Run database migrations
run_migrations() {
    log "Running database migrations..."
    
    # Wait for services to be ready
    sleep 30
    
    # Run migrations
    docker-compose -f $DOCKER_COMPOSE_FILE exec -T creatorpulse python -c "
from services.supabase_client import get_client
try:
    client = get_client()
    print('Database connection successful')
except Exception as e:
    print(f'Database connection failed: {e}')
    exit(1)
" || error "Database migration failed"
    
    log "Database migrations completed"
}

# Health check
health_check() {
    log "Performing health check..."
    
    # Wait for services to start
    sleep 60
    
    # Check if application is responding
    for i in {1..10}; do
        if curl -f http://localhost:8501/_stcore/health &> /dev/null; then
            log "Health check passed"
            return 0
        fi
        log "Health check attempt $i/10 failed, retrying in 10 seconds..."
        sleep 10
    done
    
    error "Health check failed after 10 attempts"
}

# Cleanup old backups
cleanup_backups() {
    log "Cleaning up old backups..."
    
    # Keep only last 10 backups
    cd "$BACKUP_DIR"
    ls -t backup_*.tar.gz | tail -n +11 | xargs -r rm
    cd - > /dev/null
    
    log "Old backups cleaned up"
}

# Send notification
send_notification() {
    local status=$1
    local message=$2
    
    # This would integrate with your notification system
    # For example, Slack, Discord, email, etc.
    
    if [[ "$status" == "success" ]]; then
        log "✅ Deployment successful!"
        log "Application is now live at: https://yourdomain.com"
    else
        error "❌ Deployment failed: $message"
    fi
}

# Main deployment process
main() {
    log "Starting deployment process..."
    
    # Pre-deployment checks
    check_requirements
    check_environment
    
    # Create backup before deployment
    create_backup
    
    # Update and deploy
    update_code
    deploy
    run_migrations
    
    # Post-deployment checks
    health_check
    
    # Cleanup
    cleanup_backups
    
    # Success notification
    send_notification "success" "Deployment completed successfully"
    
    log "🎉 CreatorPulse deployment completed successfully!"
}

# Error handling
trap 'error "Deployment failed at line $LINENO"' ERR

# Run main function
main "$@"
