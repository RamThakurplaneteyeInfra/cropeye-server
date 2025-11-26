from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from .models import Role

User = get_user_model()

class PhoneNumberAuthenticationTests(TestCase):
    """Test cases for phone number authentication"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        
        # Create a role
        self.role = Role.objects.create(
            name='farmer',
            display_name='Farmer'
        )
        
        # Create a test user
        self.user = User.objects.create_user(
            phone_number='9876543210',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User',
            role=self.role,
            is_active=True
        )
    
    def test_login_with_valid_phone_number(self):
        """Test login with valid phone number and password"""
        response = self.client.post('/api/users/login/', {
            'phone_number': '9876543210',
            'password': 'testpass123'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('user', response.data)
        self.assertEqual(response.data['user']['phone_number'], '9876543210')
    
    def test_login_with_wrong_phone_number(self):
        """Test login failure with wrong phone number"""
        response = self.client.post('/api/users/login/', {
            'phone_number': '1234567890',
            'password': 'testpass123'
        })
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('detail', response.data)
        self.assertIn('Invalid phone number or password', response.data['detail'])
    
    def test_login_with_wrong_password(self):
        """Test login failure with wrong password"""
        response = self.client.post('/api/users/login/', {
            'phone_number': '9876543210',
            'password': 'wrongpassword'
        })
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('detail', response.data)
        self.assertIn('Invalid phone number or password', response.data['detail'])
    
    def test_login_with_missing_phone_number(self):
        """Test login failure when phone number is missing"""
        response = self.client.post('/api/users/login/', {
            'password': 'testpass123'
        })
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('detail', response.data)
    
    def test_login_with_invalid_phone_format(self):
        """Test login failure with invalid phone number format"""
        response = self.client.post('/api/users/login/', {
            'phone_number': '12345',  # Less than 10 digits
            'password': 'testpass123'
        })
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('detail', response.data)
        self.assertIn('10 digits', response.data['detail'])
    
    def test_login_with_phone_number_containing_non_digits(self):
        """Test that phone numbers with non-digits are cleaned"""
        response = self.client.post('/api/users/login/', {
            'phone_number': '+91-98765-43210',  # Contains non-digits
            'password': 'testpass123'
        })
        
        # Should clean to 10 digits and authenticate
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
    
    def test_phone_number_uniqueness(self):
        """Test that phone numbers must be unique"""
        with self.assertRaises(Exception):
            User.objects.create_user(
                phone_number='9876543210',  # Same as existing user
                email='test2@example.com',
                password='testpass123',
                first_name='Test2',
                last_name='User2',
                role=self.role
            )

