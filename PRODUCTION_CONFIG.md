# Production Configuration for CreatorPulse

## Environment Variables

### Required for Production
```bash
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# API Keys
GROQ_API_KEY=your-groq-api-key
RESEND_API_KEY=your-resend-api-key
STRIPE_SECRET_KEY=sk_live_your-live-stripe-key
STRIPE_PUBLISHABLE_KEY=pk_live_your-live-stripe-key
STRIPE_WEBHOOK_SECRET=whsec_your-webhook-secret

# Email Configuration
RESEND_FROM=Your Brand <newsletter@yourdomain.com>

# Monitoring
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
ENVIRONMENT=production
RELEASE_VERSION=1.0.0

# Redis (for production rate limiting)
REDIS_URL=redis://localhost:6379

# Security
SECRET_KEY=your-secret-key-for-sessions
```

## Production Deployment Checklist

### 1. Database Setup
- [ ] Run all migrations: `supabase db push`
- [ ] Set up RLS policies for all tables
- [ ] Configure backup schedules
- [ ] Set up monitoring alerts

### 2. API Configuration
- [ ] Verify all API keys are live (not test keys)
- [ ] Set up webhook endpoints for Stripe
- [ ] Configure domain verification for Resend
- [ ] Set up API rate limiting

### 3. Security Hardening
- [ ] Enable HTTPS everywhere
- [ ] Set up CORS policies
- [ ] Configure CSP headers
- [ ] Enable SQL injection protection
- [ ] Set up input validation

### 4. Monitoring & Logging
- [ ] Configure Sentry for error tracking
- [ ] Set up log aggregation
- [ ] Configure performance monitoring
- [ ] Set up uptime monitoring
- [ ] Configure alerting rules

### 5. Performance Optimization
- [ ] Enable database connection pooling
- [ ] Set up Redis for caching
- [ ] Configure CDN for static assets
- [ ] Optimize database queries
- [ ] Set up load balancing

### 6. Backup & Recovery
- [ ] Set up automated database backups
- [ ] Test restore procedures
- [ ] Document disaster recovery plan
- [ ] Set up data retention policies

## Docker Configuration

### Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/
COPY supabase/ ./supabase/

# Set environment variables
ENV PYTHONPATH=/app
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0

# Expose port
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Run the application
CMD ["streamlit", "run", "app/main.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### docker-compose.yml
```yaml
version: '3.8'

services:
  creatorpulse:
    build: .
    ports:
      - "8501:8501"
    environment:
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_KEY=${SUPABASE_KEY}
      - GROQ_API_KEY=${GROQ_API_KEY}
      - RESEND_API_KEY=${RESEND_API_KEY}
      - STRIPE_SECRET_KEY=${STRIPE_SECRET_KEY}
      - SENTRY_DSN=${SENTRY_DSN}
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped
    depends_on:
      - redis

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - creatorpulse
    restart: unless-stopped

volumes:
  redis_data:
```

## Nginx Configuration

### nginx.conf
```nginx
events {
    worker_connections 1024;
}

http {
    upstream creatorpulse {
        server creatorpulse:8501;
    }

    server {
        listen 80;
        server_name yourdomain.com;
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name yourdomain.com;

        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;

        # Security headers
        add_header X-Frame-Options DENY;
        add_header X-Content-Type-Options nosniff;
        add_header X-XSS-Protection "1; mode=block";
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";

        location / {
            proxy_pass http://creatorpulse;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # WebSocket support
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
        }
    }
}
```

## Production Scripts

### deploy.sh
```bash
#!/bin/bash
set -e

echo "🚀 Deploying CreatorPulse to production..."

# Pull latest code
git pull origin main

# Build and deploy with Docker Compose
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# Run database migrations
docker-compose exec creatorpulse python -c "
from services.supabase_client import get_client
# Run any pending migrations here
"

# Health check
echo "⏳ Waiting for services to start..."
sleep 30

# Check if services are healthy
if curl -f http://localhost:8501/_stcore/health; then
    echo "✅ Deployment successful!"
else
    echo "❌ Deployment failed - health check failed"
    exit 1
fi

echo "🎉 CreatorPulse is now live!"
```

### backup.sh
```bash
#!/bin/bash
set -e

echo "📦 Creating backup..."

# Create backup directory
BACKUP_DIR="/backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p $BACKUP_DIR

# Backup database
supabase db dump --file $BACKUP_DIR/database.sql

# Backup uploaded files
cp -r ./uploads $BACKUP_DIR/

# Compress backup
tar -czf $BACKUP_DIR.tar.gz $BACKUP_DIR
rm -rf $BACKUP_DIR

echo "✅ Backup created: $BACKUP_DIR.tar.gz"
```

## Monitoring Configuration

### Health Check Endpoint
```python
# Add to app/main.py
@app.route('/health')
def health_check():
    from services.monitoring import health_checker
    status = health_checker.get_system_status()
    return jsonify(status), 200 if status['overall_status'] == 'healthy' else 503
```

### Logging Configuration
```python
# Add to app/services/logging.py
import logging
import logging.handlers
import os

def setup_logging():
    # Create logs directory
    os.makedirs('logs', exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.handlers.RotatingFileHandler(
                'logs/creatorpulse.log',
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5
            ),
            logging.StreamHandler()
        ]
    )
```

## Security Checklist

### Input Validation
- [ ] All user inputs are validated and sanitized
- [ ] SQL injection protection enabled
- [ ] XSS protection implemented
- [ ] CSRF protection enabled

### Authentication & Authorization
- [ ] Strong password requirements
- [ ] Rate limiting on login attempts
- [ ] Session management configured
- [ ] Role-based access control tested

### Data Protection
- [ ] Sensitive data encrypted at rest
- [ ] PII handling compliant with regulations
- [ ] Data retention policies implemented
- [ ] Backup encryption enabled

### Infrastructure Security
- [ ] HTTPS enforced everywhere
- [ ] Security headers configured
- [ ] Firewall rules configured
- [ ] Regular security updates scheduled

## Performance Optimization

### Database Optimization
- [ ] Indexes created for all query patterns
- [ ] Connection pooling configured
- [ ] Query performance monitored
- [ ] Slow query logging enabled

### Caching Strategy
- [ ] Redis configured for session storage
- [ ] API response caching implemented
- [ ] Static asset caching configured
- [ ] CDN configured for global distribution

### Monitoring & Alerting
- [ ] Application performance monitoring
- [ ] Database performance monitoring
- [ ] Error rate monitoring
- [ ] Uptime monitoring configured
