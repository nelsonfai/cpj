from django.core.management.base import BaseCommand
from datetime import datetime, timedelta
import random
from api.models import CalendarEvent, CustomUser, Team  # Adjust model imports based on your app

class Command(BaseCommand):
    help = 'Bulk create calendar events for August to December of the current year'

    def handle(self, *args, **kwargs):
        user = CustomUser.objects.get(id=1)  # Fetch the user with a specific ID
        team = Team.objects.get(id=3)  # Fetch the team with a specific ID

        if not user or not team:
            self.stdout.write(self.style.ERROR('User or team not found!'))
            return

        months = [8, 9, 10, 11, 12]
        current_year = datetime.now().year

        def get_random_date_in_month(year, month):
            day = random.randint(1, 28)
            start_time = datetime(year, month, day, random.randint(9, 17), 0)
            end_time = start_time + timedelta(hours=random.randint(1, 4))
            return start_time, end_time

        events = []
        for i in range(20):
            month = random.choice(months)
            start_datetime, end_datetime = get_random_date_in_month(current_year, month)

            event = CalendarEvent(
                user=user,
                team=team,
                event_title=f"Event {i + 1}",
                description=f"Description for event {i + 1}",
                start_datetime=start_datetime,
                end_datetime=end_datetime,
                is_shared=bool(random.getrandbits(1)),
                color="#FF5733",
                type="event",
                recurrence="",
                reminders=[],
                status="confirmed"
            )
            events.append(event)

        CalendarEvent.objects.bulk_create(events)
        self.stdout.write(self.style.SUCCESS(f'{len(events)} events created successfully!'))
