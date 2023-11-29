# api/tests.py

from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model

class LoginTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user_data = {
            'email': 'nelsonfai21@yahoo.com',
            'password': 'testpass'
        }
        # Create a user for testing
        self.user = get_user_model().objects.create_user(**self.user_data)

    def test_login_success(self):
        response = self.client.post('/api/login/', self.user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)
        self.assertIn('user_id', response.data)
        self.assertEqual(response.data['email'], self.user_data['email'])

    def test_login_failure(self):
        # Test with incorrect password
        invalid_data = {
            'email': self.user_data['email'],
            'password': 'wrongpassword'
        }
        response = self.client.post('/api/login/', invalid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertNotIn('token', response.data)
        self.assertNotIn('user_id', response.data)

        # Test with non-existent user
        non_existent_data = {
            'email': 'nonexistent@example.com',
            'password': 'somepassword'
        }
        response = self.client.post('/api/login/', non_existent_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertNotIn('token', response.data)
        self.assertNotIn('user_id', response.data)
