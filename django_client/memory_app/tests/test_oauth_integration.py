from django.test import TestCase, override_settings
from django.urls import reverse
from django.contrib.auth.models import User
from unittest.mock import patch, MagicMock
import uuid
import secrets
import base64
import hashlib
from memory_app.models import OAuthToken
from django.utils import timezone
from datetime import timedelta

class OAuthFlowTest(TestCase):
    """Tests for the OAuth flow in the Django client."""
    
    def setUp(self):
        """Set up test data."""
        # Create a test user
        self.user = User.objects.create_user(
            username='oauthtestuser',
            email='oauth@example.com',
            password='testpassword'
        )
        
        # Mock OAuth client credentials
        self.client_id = str(uuid.uuid4())
        self.client_secret = secrets.token_urlsafe(32)
        self.redirect_uri = 'http://localhost:8000/oauth/callback/'
        
        # Log in the user
        self.client.login(username='oauthtestuser', password='testpassword')

    @patch('memory_app.views.secrets.token_urlsafe')
    def test_oauth_authorize_generates_state_and_pkce(self, mock_token_urlsafe):
        """Test that the OAuth authorize view generates state and PKCE parameters."""
        # Mock the token_urlsafe function to return predictable values
        mock_token_urlsafe.side_effect = ['test_state', 'test_code_verifier']
        
        # Call the OAuth authorize view
        response = self.client.get(reverse('oauth_authorize'))
        
        # Should redirect to the MCP server
        self.assertEqual(response.status_code, 302)
        
        # Check that state and code_verifier were stored in session
        self.assertEqual(self.client.session['oauth_state'], 'test_state')
        self.assertEqual(self.client.session['oauth_code_verifier'], 'test_code_verifier')
        
        # Check that the redirect URL contains the correct parameters
        redirect_url = response.url
        self.assertIn('response_type=code', redirect_url)
        self.assertIn(f'client_id=', redirect_url)  # Can't check exact value as it comes from settings
        self.assertIn('redirect_uri=', redirect_url)
        self.assertIn('scope=', redirect_url)
        self.assertIn('state=test_state', redirect_url)
        self.assertIn('code_challenge=', redirect_url)
        self.assertIn('code_challenge_method=S256', redirect_url)

    @patch('memory_app.views.requests.post')
    def test_oauth_callback_exchanges_code_for_tokens(self, mock_post):
        """Test that the OAuth callback exchanges the authorization code for tokens."""
        # Set up session with state and code_verifier
        session = self.client.session
        session['oauth_state'] = 'test_state'
        session['oauth_code_verifier'] = 'test_code_verifier'
        session.save()
        
        # Mock the token response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'access_token': 'test_access_token',
            'refresh_token': 'test_refresh_token',
            'expires_in': 3600,
            'scope': 'memories:read memories:write'
        }
        mock_post.return_value = mock_response
        
        # Call the OAuth callback view with a code and matching state
        response = self.client.get(
            reverse('oauth_callback'),
            {'code': 'test_auth_code', 'state': 'test_state'}
        )
        
        # Should redirect to dashboard
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('dashboard'))
        
        # Check that the token was stored in the database
        token = OAuthToken.objects.get(user=self.user)
        self.assertEqual(token.access_token, 'test_access_token')
        self.assertEqual(token.refresh_token, 'test_refresh_token')
        self.assertEqual(token.scope, 'memories:read memories:write')
        
        # Verify the token exchange request was made correctly
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertIn('/api/oauth/token', args[0])
        self.assertEqual(kwargs['data']['grant_type'], 'authorization_code')
        self.assertEqual(kwargs['data']['code'], 'test_auth_code')
        self.assertEqual(kwargs['data']['code_verifier'], 'test_code_verifier')

    @patch('memory_app.views.requests.post')
    def test_oauth_callback_invalid_state(self, mock_post):
        """Test that the OAuth callback rejects invalid state parameter."""
        # Set up session with state
        session = self.client.session
        session['oauth_state'] = 'correct_state'
        session.save()
        
        # Call the OAuth callback view with a code but mismatched state
        response = self.client.get(
            reverse('oauth_callback'),
            {'code': 'test_auth_code', 'state': 'wrong_state'}
        )
        
        # Should redirect to dashboard with error
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('dashboard'))
        
        # Verify no token exchange request was made
        mock_post.assert_not_called()
        
        # No token should be stored
        self.assertEqual(OAuthToken.objects.filter(user=self.user).count(), 0)

    @patch('memory_app.views.requests.post')
    def test_refresh_token(self, mock_post):
        """Test that the refresh token endpoint refreshes the access token."""
        # Create an expired token
        expired_time = timezone.now() - timedelta(hours=1)
        token = OAuthToken.objects.create(
            user=self.user,
            access_token='old_access_token',
            refresh_token='old_refresh_token',
            expires_at=expired_time,
            scope='memories:read memories:write'
        )
        
        # Mock the refresh response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'access_token': 'new_access_token',
            'refresh_token': 'new_refresh_token',
            'expires_in': 3600,
            'scope': 'memories:read memories:write'
        }
        mock_post.return_value = mock_response
        
        # Call the refresh token view
        response = self.client.get(reverse('refresh_token'))
        
        # Should redirect to dashboard
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('dashboard'))
        
        # Check that the token was updated in the database
        token.refresh_from_db()
        self.assertEqual(token.access_token, 'new_access_token')
        self.assertEqual(token.refresh_token, 'new_refresh_token')
        
        # Verify the refresh request was made correctly
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertIn('/api/oauth/token', args[0])
        self.assertEqual(kwargs['data']['grant_type'], 'refresh_token')
        self.assertEqual(kwargs['data']['refresh_token'], 'old_refresh_token')

class OAuthTokenModelTest(TestCase):
    """Tests for the OAuthToken model."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='tokenuser',
            email='token@example.com',
            password='testpassword'
        )
        
    def test_token_is_expired(self):
        """Test the is_expired property of OAuthToken."""
        # Create an expired token
        expired_time = timezone.now() - timedelta(minutes=5)
        expired_token = OAuthToken.objects.create(
            user=self.user,
            access_token='expired_token',
            refresh_token='refresh_token',
            expires_at=expired_time,
            scope='memories:read'
        )
        
        # Create a valid token
        valid_time = timezone.now() + timedelta(minutes=5)
        valid_token = OAuthToken.objects.create(
            user=self.user,
            access_token='valid_token',
            refresh_token='refresh_token2',
            expires_at=valid_time,
            scope='memories:read'
        )
        
        # Test is_expired property
        self.assertTrue(expired_token.is_expired)
        self.assertFalse(valid_token.is_expired)
        
    def test_token_get_for_user(self):
        """Test the get_for_user class method of OAuthToken."""
        # Initially no token
        self.assertIsNone(OAuthToken.get_for_user(self.user))
        
        # Create a token
        token = OAuthToken.objects.create(
            user=self.user,
            access_token='test_token',
            refresh_token='refresh_token',
            expires_at=timezone.now() + timedelta(hours=1),
            scope='memories:read'
        )
        
        # Should return the token
        self.assertEqual(OAuthToken.get_for_user(self.user), token)
        
        # Create another user with no token
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpassword'
        )
        
        # Should return None for other user
        self.assertIsNone(OAuthToken.get_for_user(other_user))
