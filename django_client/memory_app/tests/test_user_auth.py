from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from memory_app.models import UserProfile
from memory_app.forms import UserRegistrationForm

class UserRegistrationTest(TestCase):
    """Tests for the user registration functionality."""
    
    def test_registration_form_valid(self):
        """Test that a valid registration form can be submitted."""
        form_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password1': 'strongpassword123',
            'password2': 'strongpassword123',
        }
        form = UserRegistrationForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_registration_form_invalid(self):
        """Test that an invalid registration form is detected."""
        # Password mismatch
        form_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password1': 'strongpassword123',
            'password2': 'differentpassword',
        }
        form = UserRegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())
    
    def test_registration_view(self):
        """Test the registration view creates a user."""
        response = self.client.post(reverse('register'), {
            'username': 'testuser',
            'email': 'test@example.com',
            'password1': 'strongpassword123',
            'password2': 'strongpassword123',
        })
        self.assertEqual(response.status_code, 302)  # Redirects after successful registration
        self.assertTrue(User.objects.filter(username='testuser').exists())
        
    def test_user_profile_creation(self):
        """Test that a UserProfile is automatically created with a new user."""
        user = User.objects.create_user(
            username='profiletest', 
            email='profile@example.com', 
            password='testpassword'
        )
        self.assertTrue(hasattr(user, 'profile'))
        self.assertIsInstance(user.profile, UserProfile)
