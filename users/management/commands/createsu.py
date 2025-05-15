"""
Django management command to create a superuser with email and password.

This command is designed to be used in development and deployment scripts
to create an initial superuser account. It will prompt for email and password
if not provided as arguments or in environment variables.
"""

import os
import sys
from typing import Any, Optional

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db.utils import IntegrityError

User = get_user_model()


class Command(BaseCommand):
    """Create a superuser with the specified email and password."""
    
    help = 'Create a superuser with the specified email and password'
    
    def add_arguments(self, parser):
        """Add command line arguments."""
        parser.add_argument(
            '--email',
            type=str,
            help='Email address for the superuser',
            default=os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@example.com')
        )
        parser.add_argument(
            '--password',
            type=str,
            help='Password for the superuser',
            default=os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'adminpass')
        )
        parser.add_argument(
            '--phone',
            type=str,
            help='Phone number for the superuser',
            default=os.environ.get('DJANGO_SUPERUSER_PHONE', '+1234567890')
        )
        parser.add_argument(
            '--noinput',
            '--no-input',
            action='store_false',
            dest='interactive',
            help='Do NOT prompt for input of any kind',
        )
    
    def handle(self, *args: Any, **options: Any) -> Optional[str]:
        """Handle the command execution."""
        email = options['email']
        password = options['password']
        phone = options['phone']
        interactive = options['interactive']
        
        # Get email if not provided
        if not email and interactive:
            email = input('Email address (default: admin@example.com): ') or 'admin@example.com'
        
        # Validate email
        if not email:
            raise CommandError('Email address is required')
        
        # Check if user already exists
        if User.objects.filter(email=email).exists():
            self.stdout.write(self.style.SUCCESS(f'User with email {email} already exists'))
            return
        
        # Get password if not provided
        if not password and interactive:
            from getpass import getpass
            password = getpass('Password (default: adminpass): ') or 'adminpass'
            password2 = getpass('Password (again): ') or 'adminpass'
            if password != password2:
                raise CommandError('Error: Your passwords did not match.')
        
        if not password:
            raise CommandError('Password is required')
        
        # Get phone number if not provided
        if not phone and interactive:
            phone = input('Phone number (default: +1234567890): ') or '+1234567890'
        
        # Create the superuser
        try:
            user = User.objects.create_superuser(
                email=email,
                password=password,
                phone_number=phone,
                is_active=True,
                is_staff=True,
            )
            self.stdout.write(self.style.SUCCESS(f'Successfully created superuser: {user.email}'))
        except IntegrityError as e:
            self.stderr.write(self.style.ERROR(f'Error creating superuser: {e}'))
            sys.exit(1)
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Unexpected error: {e}'))
            sys.exit(1)
