from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from memory_app.models import UserProfile
from memory_app.forms import UserProfileForm
from django.utils import timezone
import datetime

class UserProfileTest(TestCase):
    """Tests for user profile functionality."""
    
    def setUp(self):
        """Set up a test user and profile for testing."""
        self.user = User.objects.create_user(
            username='profileuser', 
            email='profile@example.com', 
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        self.client.login(username='profileuser', password='testpass123')
    
    def test_profile_view(self):
        """Test accessing the profile view."""
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'memory_app/profile.html')
    
    def test_profile_update(self):
        """Test updating the user profile."""
        dob = timezone.now().date() - datetime.timedelta(days=365*30)  # 30 years ago
        response = self.client.post(reverse('profile'), {
            'first_name': 'Updated',
            'last_name': 'Name',
            'email': 'updated@example.com',
            'bio': 'This is my updated bio',
            'date_of_birth': dob.strftime('%Y-%m-%d'),
        })
        self.assertEqual(response.status_code, 302)  # Redirect after successful update
        
        # Refresh the user and profile from the database
        self.user.refresh_from_db()
        self.user.profile.refresh_from_db()
        
        # Check that the user and profile were updated
        self.assertEqual(self.user.first_name, 'Updated')
        self.assertEqual(self.user.last_name, 'Name')
        self.assertEqual(self.user.email, 'updated@example.com')
        self.assertEqual(self.user.profile.bio, 'This is my updated bio')
        self.assertEqual(self.user.profile.date_of_birth, dob)
    
    def test_profile_form(self):
        """Test the UserProfileForm."""
        form_data = {
            'first_name': 'Form',
            'last_name': 'Test',
            'email': 'form@example.com',
            'bio': 'Testing the form',
            'date_of_birth': '1990-01-01',
        }
        form = UserProfileForm(data=form_data, instance=self.user.profile)
        self.assertTrue(form.is_valid())
        
        profile = form.save()
        self.assertEqual(profile.bio, 'Testing the form')
        self.assertEqual(profile.user.first_name, 'Form')
        self.assertEqual(profile.user.last_name, 'Test')
        self.assertEqual(profile.user.email, 'form@example.com')
