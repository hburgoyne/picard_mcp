"""Tests for the users app models."""
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

User = get_user_model()


class UserModelTests(TestCase):
    """Test cases for the custom User model."""
    
    def test_create_user(self):
        ""Test creating a regular user."""
        email = 'test@example.com'
        password = 'testpass123'
        user = User.objects.create_user(
            email=email,
            password=password,
            first_name='Test',
            last_name='User'
        )
        
        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))
        self.assertEqual(user.get_full_name(), 'Test User')
        self.assertEqual(user.get_short_name(), 'Test')
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
    
    def test_create_superuser(self):
        ""Test creating a superuser."""
        admin = User.objects.create_superuser(
            email='admin@example.com',
            password='adminpass'
        )
        
        self.assertTrue(admin.is_active)
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)
    
    def test_email_required(self):
        ""Test that email is required."""
        with self.assertRaises(ValueError):
            User.objects.create_user(email='', password='test123')
    
    def test_email_normalization(self):
        ""Test email is normalized."""
        email = 'test@EXAMPLE.COM'
        user = User.objects.create_user(email=email, password='test123')
        self.assertEqual(user.email, email.lower())
    
    def test_has_verified_email(self):
        ""Test the has_verified_email method."""
        user = User.objects.create_user(
            email='test@example.com',
            password='test123',
            is_active=True
        )
        self.assertTrue(user.has_verified_email())
    
    def test_update_last_login(self):
        ""Test updating the last login timestamp."""
        user = User.objects.create_user(
            email='test@example.com',
            password='test123'
        )
        
        # Initial last_login should be None for new users
        self.assertIsNone(user.last_login)
        
        # Update last login
        user.update_last_login()
        self.assertIsNotNone(user.last_login)
        
        # Should be recent (within 1 second)
        self.assertLess(
            timezone.now() - user.last_login,
            timedelta(seconds=1)
        )
    
    def test_string_representation(self):
        ""Test string representation of the user."""
        user = User(email='test@example.com')
        self.assertEqual(str(user), 'test@example.com')
    
    def test_full_name_property(self):
        ""Test the full_name property."""
        # Test with both names
        user1 = User(
            email='test1@example.com',
            first_name='John',
            last_name='Doe'
        )
        self.assertEqual(user1.full_name, 'John Doe')
        
        # Test with only first name
        user2 = User(email='test2@example.com', first_name='John')
        self.assertEqual(user2.full_name, 'John')
        
        # Test with only email (no names)
        user3 = User(email='test3@example.com')
        self.assertEqual(user3.full_name, 'test3@example.com')
