import pytest
import os
import tempfile
from unittest.mock import Mock, patch
from services.supabase_client import (
    create_workspace,
    get_user_workspaces,
    create_client_profile,
    get_client_profiles,
)
from services.groq_client import generate_draft
from services.resend_client import send_email
from services.content_fetcher import fetch_all_sources
from services.analytics_service import AnalyticsTracker
from services.monitoring import SecurityValidator, RateLimiter, HealthChecker


class TestSupabaseClient:
    """Test Supabase client functions"""
    
    @pytest.fixture
    def mock_user_id(self):
        return "test-user-123"
    
    @pytest.fixture
    def mock_workspace_data(self):
        return {
            "name": "Test Workspace",
            "slug": "test-workspace",
            "description": "Test workspace for unit tests"
        }
    
    @patch('services.supabase_client.get_client')
    def test_create_workspace(self, mock_get_client, mock_user_id, mock_workspace_data):
        """Test workspace creation"""
        # Mock Supabase response
        mock_client = Mock()
        mock_client.table.return_value.insert.return_value.execute.return_value.data = [{"id": "workspace-123"}]
        mock_get_client.return_value = mock_client
        
        workspace = create_workspace(
            name=mock_workspace_data["name"],
            slug=mock_workspace_data["slug"],
            description=mock_workspace_data["description"],
            owner_id=mock_user_id
        )
        
        assert workspace["id"] == "workspace-123"
        mock_client.table.assert_called_with("workspaces")
    
    @patch('services.supabase_client.get_client')
    def test_get_user_workspaces(self, mock_get_client, mock_user_id):
        """Test getting user workspaces"""
        mock_client = Mock()
        mock_client.table.return_value.select.return_value.eq.return_value.not_.return_value.execute.return_value.data = [
            {"workspace_id": "workspace-123", "role": "owner", "workspaces": {"name": "Test Workspace"}}
        ]
        mock_get_client.return_value = mock_client
        
        workspaces = get_user_workspaces(user_id=mock_user_id)
        
        assert len(workspaces) == 1
        assert workspaces[0]["workspace_id"] == "workspace-123"
        assert workspaces[0]["role"] == "owner"


class TestGroqClient:
    """Test Groq client functions"""
    
    @pytest.fixture
    def mock_style_samples(self):
        return [
            "This is a sample newsletter style.",
            "Another sample with different tone."
        ]
    
    @pytest.fixture
    def mock_content_items(self):
        return [
            {"title": "Test Article 1", "url": "https://example.com/1"},
            {"title": "Test Article 2", "url": "https://example.com/2"}
        ]
    
    @patch.dict(os.environ, {'GROQ_API_KEY': 'test-key'})
    @patch('services.groq_client.Groq')
    def test_generate_draft_with_api_key(self, mock_groq_class, mock_style_samples, mock_content_items):
        """Test draft generation with API key"""
        # Mock Groq client and response
        mock_client = Mock()
        mock_completion = Mock()
        mock_completion.choices = [Mock()]
        mock_completion.choices[0].message.content = "Generated newsletter draft"
        mock_completion.usage.total_tokens = 100
        mock_client.chat.completions.create.return_value = mock_completion
        mock_groq_class.return_value = mock_client
        
        draft = generate_draft(
            style_samples=mock_style_samples,
            content_items=mock_content_items,
            creator_name="Test Creator"
        )
        
        assert draft == "Generated newsletter draft"
        mock_client.chat.completions.create.assert_called_once()
    
    @patch.dict(os.environ, {}, clear=True)
    def test_generate_draft_without_api_key(self, mock_style_samples, mock_content_items):
        """Test draft generation without API key (fallback)"""
        draft = generate_draft(
            style_samples=mock_style_samples,
            content_items=mock_content_items,
            creator_name="Test Creator"
        )
        
        assert "Intro" in draft
        assert "Curated Links" in draft
        assert "Trends to Watch" in draft


class TestResendClient:
    """Test Resend client functions"""
    
    @pytest.fixture
    def mock_email_data(self):
        return {
            "to_email": "test@example.com",
            "subject": "Test Newsletter",
            "html_content": "<h1>Test Newsletter</h1>"
        }
    
    @patch.dict(os.environ, {'RESEND_API_KEY': 'test-key'})
    @patch('services.resend_client.requests.post')
    def test_send_email_success(self, mock_post, mock_email_data):
        """Test successful email sending"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        # Should not raise an exception
        send_email(**mock_email_data)
        
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[1]['json']['to'] == [mock_email_data['to_email']]
        assert call_args[1]['json']['subject'] == mock_email_data['subject']
    
    @patch.dict(os.environ, {'RESEND_API_KEY': 'test-key'})
    @patch('services.resend_client.requests.post')
    def test_send_email_failure(self, mock_post, mock_email_data):
        """Test email sending failure"""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        mock_post.return_value = mock_response
        
        with pytest.raises(RuntimeError, match="Resend error"):
            send_email(**mock_email_data)


class TestContentFetcher:
    """Test content fetching functions"""
    
    @pytest.fixture
    def mock_user_id(self):
        return "test-user-123"
    
    @pytest.fixture
    def mock_workspace_id(self):
        return "workspace-123"
    
    @patch('services.content_fetcher.list_sources')
    @patch('services.content_fetcher.save_content_items')
    def test_fetch_all_sources(self, mock_save_items, mock_list_sources, mock_user_id, mock_workspace_id):
        """Test fetching content from all sources"""
        # Mock sources
        mock_sources = [
            {"id": "source-1", "source_type": "twitter", "source_value": "@test", "boost_factor": 1.0},
            {"id": "source-2", "source_type": "rss", "source_value": "https://example.com/feed", "boost_factor": 1.0}
        ]
        mock_list_sources.return_value = mock_sources
        
        # Mock content items
        mock_content = [
            {"title": "Test Tweet", "url": "https://twitter.com/test/1"},
            {"title": "Test RSS Item", "url": "https://example.com/1"}
        ]
        
        with patch('services.content_fetcher._fetch_twitter', return_value=[mock_content[0]]), \
             patch('services.content_fetcher._fetch_rss', return_value=[mock_content[1]]):
            
            result = fetch_all_sources(user_id=mock_user_id, workspace_id=mock_workspace_id)
            
            assert result == 2  # Should return number of items saved
            mock_save_items.assert_called_once()


class TestAnalyticsService:
    """Test analytics service functions"""
    
    @pytest.fixture
    def analytics_tracker(self):
        return AnalyticsTracker()
    
    @patch('services.analytics_service.get_client')
    def test_track_event(self, mock_get_client, analytics_tracker):
        """Test event tracking"""
        mock_client = Mock()
        mock_client.table.return_value.insert.return_value.execute.return_value = None
        mock_get_client.return_value = mock_client
        
        # Should not raise an exception
        analytics_tracker.track_event(
            user_id="test-user",
            workspace_id="test-workspace",
            event_type="test_event",
            event_category="test",
            event_name="test_action"
        )
        
        mock_client.table.assert_called_with("analytics_events")
    
    def test_track_api_call(self, analytics_tracker):
        """Test API call tracking"""
        with patch.object(analytics_tracker, 'track_event') as mock_track:
            analytics_tracker.track_api_call(
                user_id="test-user",
                workspace_id="test-workspace",
                api_provider="groq",
                endpoint="chat_completions",
                tokens_used=100,
                cost_cents=5
            )
            
            mock_track.assert_called_once()
            call_args = mock_track.call_args[1]
            assert call_args['event_type'] == 'api_call'
            assert call_args['event_category'] == 'external_api'
            assert call_args['cost_cents'] == 5


class TestMonitoringService:
    """Test monitoring and security functions"""
    
    def test_security_validator_email(self):
        """Test email validation"""
        validator = SecurityValidator()
        
        assert validator.validate_email("test@example.com") == True
        assert validator.validate_email("invalid-email") == False
        assert validator.validate_email("") == False
    
    def test_security_validator_url(self):
        """Test URL validation"""
        validator = SecurityValidator()
        
        assert validator.validate_url("https://example.com") == True
        assert validator.validate_url("http://example.com") == True
        assert validator.validate_url("invalid-url") == False
    
    def test_security_validator_sanitize_input(self):
        """Test input sanitization"""
        validator = SecurityValidator()
        
        # Test basic sanitization
        result = validator.sanitize_input("  test input  ")
        assert result == "test input"
        
        # Test dangerous character removal
        result = validator.sanitize_input("test<script>alert('xss')</script>")
        assert "<script>" not in result
        assert "alert" not in result
        
        # Test length truncation
        long_input = "x" * 2000
        result = validator.sanitize_input(long_input, max_length=100)
        assert len(result) == 100
    
    def test_security_validator_workspace_slug(self):
        """Test workspace slug validation"""
        validator = SecurityValidator()
        
        assert validator.validate_workspace_slug("valid-slug") == True
        assert validator.validate_workspace_slug("valid123") == True
        assert validator.validate_workspace_slug("invalid_slug") == False  # underscore
        assert validator.validate_workspace_slug("Invalid-Slug") == False  # uppercase
        assert validator.validate_workspace_slug("ab") == False  # too short
        assert validator.validate_workspace_slug("x" * 51) == False  # too long
    
    def test_rate_limiter(self):
        """Test rate limiting functionality"""
        limiter = RateLimiter()
        
        # Test basic rate limiting
        assert limiter.is_allowed("test-key", 5, 60) == True
        assert limiter.is_allowed("test-key", 5, 60) == True
        assert limiter.is_allowed("test-key", 5, 60) == True
        assert limiter.is_allowed("test-key", 5, 60) == True
        assert limiter.is_allowed("test-key", 5, 60) == True
        assert limiter.is_allowed("test-key", 5, 60) == False  # Exceeded limit
        
        # Test different keys
        assert limiter.is_allowed("different-key", 5, 60) == True
    
    def test_health_checker(self):
        """Test health check functionality"""
        checker = HealthChecker()
        
        # Test system status
        with patch.object(checker, 'check_database') as mock_db, \
             patch.object(checker, 'check_external_apis') as mock_api:
            
            mock_db.return_value = {"status": "healthy"}
            mock_api.return_value = {"groq": {"status": "healthy"}, "resend": {"status": "healthy"}}
            
            status = checker.get_system_status()
            
            assert status["overall_status"] == "healthy"
            assert "database" in status
            assert "external_apis" in status


class TestIntegration:
    """Integration tests for critical workflows"""
    
    @patch('services.supabase_client.get_client')
    @patch('services.groq_client.Groq')
    def test_newsletter_generation_workflow(self, mock_groq_class, mock_get_client):
        """Test complete newsletter generation workflow"""
        # Mock Supabase
        mock_sb_client = Mock()
        mock_sb_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
            {"id": "user-123", "email": "test@example.com", "name": "Test User"}
        ]
        mock_get_client.return_value = mock_sb_client
        
        # Mock Groq
        mock_groq_client = Mock()
        mock_completion = Mock()
        mock_completion.choices = [Mock()]
        mock_completion.choices[0].message.content = "Generated newsletter"
        mock_completion.usage.total_tokens = 100
        mock_groq_client.chat.completions.create.return_value = mock_completion
        mock_groq_class.return_value = mock_groq_client
        
        # Test workflow
        from services.newsletter_generator import generate_and_save_draft
        
        with patch('services.newsletter_generator.list_style_files', return_value=[]), \
             patch('services.newsletter_generator.list_recent_content', return_value=[]), \
             patch('services.newsletter_generator.save_draft', return_value=None):
            
            draft = generate_and_save_draft(
                user_id="user-123",
                selected_item_ids=None,
                temperature=0.7,
                num_links=5
            )
            
            assert draft == "Generated newsletter"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
