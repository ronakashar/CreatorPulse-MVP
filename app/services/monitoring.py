import os
import logging
import traceback
from typing import Dict, Any, Optional
from functools import wraps
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Sentry for error tracking
try:
    import sentry_sdk
    from sentry_sdk.integrations.streamlit import StreamlitIntegration
    from sentry_sdk.integrations.requests import RequestsIntegration
    from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
    
    SENTRY_DSN = os.getenv("SENTRY_DSN")
    if SENTRY_DSN:
        sentry_sdk.init(
            dsn=SENTRY_DSN,
            integrations=[
                StreamlitIntegration(),
                RequestsIntegration(),
                SqlalchemyIntegration(),
            ],
            traces_sample_rate=0.1,  # 10% of transactions for performance monitoring
            environment=os.getenv("ENVIRONMENT", "development"),
            release=os.getenv("RELEASE_VERSION", "1.0.0"),
        )
        logger.info("Sentry initialized successfully")
    else:
        logger.warning("SENTRY_DSN not set, error tracking disabled")
except ImportError:
    logger.warning("Sentry SDK not installed, error tracking disabled")
    sentry_sdk = None


class MonitoringService:
    """Production monitoring and error tracking service"""
    
    def __init__(self):
        self.logger = logger
    
    def track_error(self, error: Exception, context: Dict[str, Any] = None) -> None:
        """Track an error with Sentry"""
        if sentry_sdk:
            with sentry_sdk.push_scope() as scope:
                if context:
                    for key, value in context.items():
                        scope.set_extra(key, value)
                sentry_sdk.capture_exception(error)
        
        # Also log locally
        self.logger.error(f"Error tracked: {error}", exc_info=True)
    
    def track_event(self, event_name: str, data: Dict[str, Any] = None) -> None:
        """Track a custom event"""
        if sentry_sdk:
            sentry_sdk.capture_message(event_name, level="info")
        
        self.logger.info(f"Event tracked: {event_name} - {data}")
    
    def track_performance(self, operation: str, duration_ms: float, metadata: Dict[str, Any] = None) -> None:
        """Track performance metrics"""
        if sentry_sdk:
            with sentry_sdk.start_transaction(op="performance", name=operation) as transaction:
                transaction.set_data("duration_ms", duration_ms)
                if metadata:
                    for key, value in metadata.items():
                        transaction.set_data(key, value)
        
        self.logger.info(f"Performance tracked: {operation} - {duration_ms}ms")
    
    def set_user_context(self, user_id: str, email: str = None, workspace_id: str = None) -> None:
        """Set user context for error tracking"""
        if sentry_sdk:
            sentry_sdk.set_user({
                "id": user_id,
                "email": email,
                "workspace_id": workspace_id
            })


def error_handler(func):
    """Decorator to handle errors and track them"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            monitoring = MonitoringService()
            monitoring.track_error(e, {
                "function": func.__name__,
                "args": str(args)[:200],  # Truncate to avoid huge logs
                "kwargs": str(kwargs)[:200]
            })
            raise
    return wrapper


def performance_monitor(operation_name: str):
    """Decorator to monitor performance"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                
                monitoring = MonitoringService()
                monitoring.track_performance(operation_name, duration_ms, {
                    "function": func.__name__,
                    "success": True
                })
                
                return result
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                
                monitoring = MonitoringService()
                monitoring.track_performance(operation_name, duration_ms, {
                    "function": func.__name__,
                    "success": False,
                    "error": str(e)
                })
                
                raise
        return wrapper
    return decorator


class RateLimiter:
    """Simple in-memory rate limiter for production use"""
    
    def __init__(self):
        self.requests = {}  # In production, use Redis instead
    
    def is_allowed(self, key: str, limit: int, window_seconds: int = 60) -> bool:
        """Check if request is allowed based on rate limit"""
        now = time.time()
        window_start = now - window_seconds
        
        # Clean old requests
        if key in self.requests:
            self.requests[key] = [req_time for req_time in self.requests[key] if req_time > window_start]
        else:
            self.requests[key] = []
        
        # Check limit
        if len(self.requests[key]) >= limit:
            return False
        
        # Add current request
        self.requests[key].append(now)
        return True
    
    def get_remaining(self, key: str, limit: int, window_seconds: int = 60) -> int:
        """Get remaining requests in current window"""
        now = time.time()
        window_start = now - window_seconds
        
        if key in self.requests:
            self.requests[key] = [req_time for req_time in self.requests[key] if req_time > window_start]
            return max(0, limit - len(self.requests[key]))
        
        return limit


def rate_limit(limit: int, window_seconds: int = 60, key_func=None):
    """Decorator to apply rate limiting"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            limiter = RateLimiter()
            
            # Generate rate limit key
            if key_func:
                rate_key = key_func(*args, **kwargs)
            else:
                # Default: use function name
                rate_key = func.__name__
            
            if not limiter.is_allowed(rate_key, limit, window_seconds):
                remaining = limiter.get_remaining(rate_key, limit, window_seconds)
                raise Exception(f"Rate limit exceeded. Try again in {window_seconds} seconds. Remaining: {remaining}")
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


class SecurityValidator:
    """Input validation and security checks"""
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def validate_url(url: str) -> bool:
        """Validate URL format"""
        import re
        pattern = r'^https?://[^\s/$.?#].[^\s]*$'
        return bool(re.match(pattern, url))
    
    @staticmethod
    def sanitize_input(text: str, max_length: int = 1000) -> str:
        """Sanitize user input"""
        if not text:
            return ""
        
        # Truncate to max length
        text = text[:max_length]
        
        # Remove potentially dangerous characters
        dangerous_chars = ['<', '>', '"', "'", '&', '\x00', '\r', '\n']
        for char in dangerous_chars:
            text = text.replace(char, '')
        
        return text.strip()
    
    @staticmethod
    def validate_workspace_slug(slug: str) -> bool:
        """Validate workspace slug format"""
        import re
        pattern = r'^[a-z0-9-]+$'
        return bool(re.match(pattern, slug)) and len(slug) >= 3 and len(slug) <= 50


class HealthChecker:
    """Health check service for monitoring system status"""
    
    def __init__(self):
        self.logger = logger
    
    def check_database(self) -> Dict[str, Any]:
        """Check database connectivity"""
        try:
            from services.supabase_client import get_client
            client = get_client()
            # Simple query to test connection
            result = client.table("users").select("id").limit(1).execute()
            return {"status": "healthy", "response_time_ms": 0}
        except Exception as e:
            self.logger.error(f"Database health check failed: {e}")
            return {"status": "unhealthy", "error": str(e)}
    
    def check_external_apis(self) -> Dict[str, Any]:
        """Check external API connectivity"""
        results = {}
        
        # Check Groq API
        try:
            import requests
            groq_key = os.getenv("GROQ_API_KEY")
            if groq_key:
                # Simple test request
                response = requests.get("https://api.groq.com/openai/v1/models", 
                                      headers={"Authorization": f"Bearer {groq_key}"}, 
                                      timeout=5)
                results["groq"] = {"status": "healthy" if response.status_code == 200 else "unhealthy"}
            else:
                results["groq"] = {"status": "not_configured"}
        except Exception as e:
            results["groq"] = {"status": "unhealthy", "error": str(e)}
        
        # Check Resend API
        try:
            resend_key = os.getenv("RESEND_API_KEY")
            if resend_key:
                response = requests.get("https://api.resend.com/domains", 
                                      headers={"Authorization": f"Bearer {resend_key}"}, 
                                      timeout=5)
                results["resend"] = {"status": "healthy" if response.status_code == 200 else "unhealthy"}
            else:
                results["resend"] = {"status": "not_configured"}
        except Exception as e:
            results["resend"] = {"status": "unhealthy", "error": str(e)}
        
        return results
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system health status"""
        db_status = self.check_database()
        api_status = self.check_external_apis()
        
        overall_status = "healthy"
        if db_status["status"] != "healthy":
            overall_status = "unhealthy"
        elif any(api["status"] == "unhealthy" for api in api_status.values()):
            overall_status = "degraded"
        
        return {
            "overall_status": overall_status,
            "database": db_status,
            "external_apis": api_status,
            "timestamp": time.time()
        }


# Global instances
monitoring = MonitoringService()
rate_limiter = RateLimiter()
security_validator = SecurityValidator()
health_checker = HealthChecker()
