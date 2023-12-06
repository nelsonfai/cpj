from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from datetime import datetime, timedelta
from .models import CustomUser, Team, Habit, DailyProgress

class HabitStatisticsViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = CustomUser.objects.create_user(email='test@example.com', password='testpassword')
        self.team_member1 = CustomUser.objects.create_user(email='member1@example.com', password='testpassword')
        self.team_member2 = CustomUser.objects.create_user(email='member2@example.com', password='testpassword')
        self.team = Team.objects.create(unique_id='team123', member1=self.team_member1, member2=self.team_member2)
        self.habit = Habit.objects.create(
            user=self.user,
            team=self.team,
            name='Test Habit',
            frequency='daily',
            start_date=datetime.now().date() - timedelta(days=30),
            end_date=datetime.now().date(),
            reminder_time=datetime.now().time(),
        )

    def test_habit_statistics_view(self):
        url = reverse('habit_statistics', args=[self.habit.id])
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.user.gettoken}')

        start_date = (datetime.now() - timedelta(days=15)).strftime('%Y-%m-%d')
        end_date = datetime.now().strftime('%Y-%m-%d')

        response = self.client.get(url, {'start_date': start_date, 'end_date': end_date})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # Assuming a team habit, response will have statistics for each member

        for statistics in response.data:
            self.assertIn('user_id', statistics)
            self.assertIn('user_email', statistics)
            self.assertIn('total_completed_days', statistics)
            self.assertIn('total_undone_days', statistics)
            self.assertIn('completed_days_list', statistics)
