"""Models for the users app."""
from typing import Dict, List, Optional, Type, TypeVar, Union
from uuid import UUID

from django.contrib.auth.models import AbstractUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

# Type variable for User class to support type hints in class methods
UserType = TypeVar('UserType', bound='User')


class UserManager(BaseUserManager[UserType]):
    """Custom user model manager where email is the unique identifier."""
    
    def create_user(
        self,
        email: str,
        password: Optional[str] = None,
        **extra_fields
    ) -> UserType:
        """
        Create and save a regular user with the given email and password.
        
        Args:
            email: The user's email address (used as username)
            password: The user's password (will be hashed)
            **extra_fields: Additional user attributes
            
        Returns:
            User: The newly created user instance
            
        Raises:
            ValueError: If email is not provided
        """
        if not email:
            raise ValueError(_('The Email field must be set'))
            
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        
        if password:
            user.set_password(password)
            
        user.save(using=self._db)
        return user

    def create_superuser(
        self,
        email: str,
        password: Optional[str] = None,
        **extra_fields
    ) -> UserType:
        """
        Create and save a SuperUser with the given email and password.
        
        Args:
            email: The superuser's email address
            password: The superuser's password
            **extra_fields: Additional superuser attributes
            
        Returns:
            User: The newly created superuser instance
            
        Raises:
            ValueError: If is_staff or is_superuser is not True
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
            
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser, PermissionsMixin):
    """
    Custom user model that uses email as the unique identifier.
    
    This model extends Django's built-in AbstractUser to use email as the
    primary identifier instead of username. It also adds additional fields
    and methods for user management.
    
    Attributes:
        email: The user's email address (used as username).
        phone_number: Optional phone number for the user.
        date_joined: When the user account was created.
        last_login: When the user last logged in.
        is_active: Boolean indicating if the user account is active.
        is_staff: Boolean indicating if the user can log into the admin site.
        is_superuser: Boolean indicating if the user has all permissions.
    """
    # Remove username field and make email the USERNAME_FIELD
    username = None
    email = models.EmailField(
        _('email address'),
        unique=True,
        help_text=_("The user's email address (used as username)")
    )
    
    phone_number = models.CharField(
        _('phone number'),
        max_length=20,
        blank=True,
        null=True,
        help_text=_("The user's phone number (optional)")
    )
    
    # Additional fields from AbstractUser that we want to keep
    first_name = models.CharField(
        _('first name'),
        max_length=150,
        blank=True,
        help_text=_("The user's first name (optional)")
    )
    last_name = models.CharField(
        _('last name'),
        max_length=150,
        blank=True,
        help_text=_("The user's last name (optional)")
    )
    
    # System fields
    date_joined = models.DateTimeField(
        _('date joined'),
        default=timezone.now,
        help_text=_("When the user account was created")
    )
    
    # Required fields for AbstractUser
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []  # Email & Password are required by default
    
    objects = UserManager()
    
    class Meta:
        """Metadata options for the User model."""
        verbose_name = _('user')
        verbose_name_plural = _('users')
        ordering = ['email']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['is_active']),
            models.Index(fields=['date_joined']),
        ]
    
    def __str__(self) -> str:
        """Return a string representation of the user."""
        return self.email
    
    @property
    def full_name(self) -> str:
        """Return the user's full name."""
        return f"{self.first_name} {self.last_name}".strip() or self.email
    
    def get_short_name(self) -> str:
        """Return the short name for the user (first name or email)."""
        return self.first_name or self.email
    
    def get_full_name(self) -> str:
        """Return the full name of the user."""
        return self.full_name
    
    def has_verified_email(self) -> bool:
        """Check if the user has a verified email address."""
        # This can be extended with email verification logic
        return self.is_active
    
    def update_last_login(self) -> None:
        """Update the last login time for the user."""
        self.last_login = timezone.now()
        self.save(update_fields=['last_login'])
