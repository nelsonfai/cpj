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
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from .models import Item,CollaborativeList

class ItemRetrieveUpdateDestroyViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email='testuser@example.com',  # Use the email field for authentication
            password='testpassword'
        )
        self.client.force_authenticate(user=self.user)

        # Create a CollaborativeList for testing
        self.collaborative_list = CollaborativeList.objects.create(
            user=self.user, title='Test List',color='red',description = 'adjad'
        )

        # Create an item for testing
        self.item = Item.objects.create(
            list=self.collaborative_list, text='Test Item', done=False
        )

    def test_update_item(self):
        url = f'/items/{self.item.pk}/'
        data = {'text': 'Updated Text', 'done': True}

        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.item.refresh_from_db()
        self.assertEqual(self.item.text, 'Updated Text')
        self.assertEqual(self.item.done, True)

