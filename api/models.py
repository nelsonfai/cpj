from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager,PermissionsMixin
from datetime import timedelta
from django.db.models import Q
from django.utils import timezone
from cloudinary.models import CloudinaryField
from django.db.models import F
from django.core.exceptions import ValidationError
from model_utils import FieldTracker  # Assuming you are using model-utils for tracking



class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)

class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=30, blank=True,null=True)
    fullname = models.CharField(max_length=100, blank=True,null=True)
    #profile_pic = models.ImageField(upload_to='profile_pics/', null=True, blank=True)
    profile_pic = CloudinaryField('image', blank=True, null=True)
    lang = models.CharField(max_length=10,blank=True,null=True)
    team_invite_code = models.CharField(max_length=6, unique=True, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    premium = models.BooleanField(default=False)
    expo_token = models.TextField(null=True,blank=True)
    notifications = models.BooleanField(default=False)
    customerid = models.CharField(max_length=100, unique=True, null=True)  # New field for customer ID
    subscription_type = models.CharField(max_length=100, blank=True, null=True)  # Subscription type field
    store = models.CharField(max_length=100, blank=True, null=True)  # Store field
    valid_till = models.DateTimeField(blank=True, null=True)  # Valid till field
    subscription_code = models.CharField(max_length=100, blank=True, null=True)  # Subscription code field
    tourStatusSharedListDone  = models.BooleanField(default=False)
    tourStatusNotesDone = models.BooleanField(default=False)
    tourStatusHabitsDone = models.BooleanField(default=False)
    productid = models.CharField(max_length=100, blank=True, null=True)
    auto_renew_status = models.BooleanField(default=False)
    joinNewsletter = models.BooleanField(default=False)
    hasReview = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)  # Automatically set at creation

    tracker = FieldTracker()


    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    def __str__(self):
        return self.email
    @property
    def is_premium (self):
        if self.premium:
            return True
        team = Team.objects.filter(Q(member1=self) | Q(member2=self)).first()
        if team and (team.member1.premium or team.member2.premium):
            return True
        return False
    
class Team(models.Model):
    unique_id = models.CharField(max_length=20, unique=True)
    member1 = models.OneToOneField(CustomUser, related_name='team_member1', on_delete=models.CASCADE)
    member2 = models.OneToOneField(CustomUser, related_name='team_member2', on_delete=models.CASCADE, null=True, blank=True)
    ismember1sync = models.BooleanField(default=False)
    ismember2sync = models.BooleanField(default=False)
    created_at = models.DateField(auto_now_add=True)
    #team_name = models.CharField(max_length=100,blank=True,null=True)
    
    def __str__(self):
        return f"Team {self.unique_id}"

    def team_points(self):
        """
        Returns the total gamification points for both members in the team.
        """
        member1_points = 0
        member2_points = 0

        # Check if member1 has a gamification profile and calculate points
        if hasattr(self.member1, 'gamification'):
            member1_points = self.member1.gamification.calculate_total_points()

        # Check if member2 exists and has a gamification profile, then calculate points
        if self.member2 and hasattr(self.member2, 'gamification'):
            member2_points = self.member2.gamification.calculate_total_points()

        # Sum the points for both members
        total_points = member1_points + member2_points
        return total_points
    
class CollaborativeList(models.Model):
    team = models.ForeignKey('Team',on_delete=models.SET_NULL,null=True,blank=True)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE ,null=True,blank=True )
    title = models.CharField(max_length=255)
    color = models.CharField(max_length=40,)
    description = models.TextField( null=True,blank=True)
    dateline= models.DateField(null=True,blank=True)
    tracker = FieldTracker()

    def check_all_item_done(self):
        return not self.item_set.filter(done=False).exists()
    def check_past_dateline(self):
        undone =self.item_set.filter(done=False).exists()
        if self.dateline and undone:
            today = timezone.now().date()
            if today > self.dateline:
                return True

        return False
    def __str__(self):
        return f"List '{self.title}'"

class Item(models.Model):
    list = models.ForeignKey(CollaborativeList, on_delete=models.CASCADE)
    text = models.TextField()
    done = models.BooleanField(default=False)
    last_status_change = models.DateTimeField(null=True, blank=True)
    tracker = FieldTracker()

    def save(self, *args, **kwargs):
        # If the object is being updated, check the 'done' status
        if self.id:  # Ensure the object already exists (update case)
            previous = Item.objects.filter(pk=self.id).first()  # Safe way to get the previous instance
            if previous and previous.done != self.done:
                self.last_status_change = timezone.now()
        else:
            # If the object is being created, set the last_status_change if it's marked as done
            if self.done:
                self.last_status_change = timezone.now()

        # Call the parent class's save method to persist the changes
        super().save(*args, **kwargs)

    def __str__(self):
        return self.text
# Daily Habit  Tracker 
class Habit(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    habitidentifier = models.CharField(max_length=100 ,null=True,blank=True)
    icon =models.CharField(max_length=30,blank=True,null=True)
    team = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True, blank=True)
    color= models.CharField(max_length=255,blank=True,null=True)
    name = models.CharField(max_length=255)
    frequency = models.CharField(max_length=50)
    description = models.TextField(blank=True,null=True)
    start_date = models.DateField()
    end_date = models.DateField( blank=True,null=True)
    reminder_time = models.DateTimeField(null=True, blank=True)
    specific_days_of_week = models.CharField(max_length=255, null=True, blank=True)
    specific_day_of_month = models.CharField(max_length=255, null=True, blank=True)  # Updated field
    tracker = FieldTracker()

    def get_specific_days_as_list(self):
        if self.specific_days_of_week:
            return self.specific_days_of_week.split(',')
        return []
    def get_specific_day_of_month_as_list(self):
        if self.specific_day_of_month:
            print('LIST',self.specific_day_of_month)
            return self.specific_day_of_month.split(',')
        return []

    def set_specific_days_from_list(self, days_list):
        self.specific_days_of_week = ','.join(days_list)

    def calculate_streak(self, user_id, current_date):
        progress_instances = DailyProgress.objects.filter(
            habit=self, user_id=user_id, progress=True, date__lte=current_date
        ).order_by('-date')
        streak = 0
        has_instance_with_current_date = any(instance.date == current_date for instance in progress_instances)
        if has_instance_with_current_date:
            previous_date = current_date
        else:
            previous_date = self.set_previous_day(date=current_date)
        for progress_instance in progress_instances:
            if progress_instance.date == previous_date:
                streak += 1
                previous_date = self.set_previous_day(date=previous_date)
            else:
                break
        return streak

    def set_previous_day(self, date):
        if self.frequency == 'daily':
            previous_date = date - timedelta(days=1)
        elif self.frequency == 'weekly':
            selected_days = self.get_specific_days_as_list()
            previous_date = date - timedelta(days=1)
            while True:
                current_day_of_week = previous_date.strftime('%A')
                if current_day_of_week in selected_days:
                    return previous_date
                previous_date -= timedelta(days=1)
        elif self.frequency == 'monthly':
            specific_month_days = [int(day) for day in self.get_specific_day_of_month_as_list()]
            specific_days_of_month = self.get_specific_day_of_month_as_list()
            previous_date = date - timedelta(days=1)
            while True:
                current_day_of_month = previous_date.day
                if int(current_day_of_month) in specific_month_days:
                    print('in THE LIST')
                    return previous_date
                previous_date -= timedelta(days=1)
        return previous_date
    def __str__(self):
        return self.name

class DailyProgress(models.Model):
    habit = models.ForeignKey(Habit, on_delete=models.CASCADE)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    date = models.DateField()
    progress = models.BooleanField(default=False)
    def __str__(self):
        return f"{self.user.email}'s progress for {self.habit.name} on {self.date}"
    

class Subscription(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    plan = models.CharField(max_length=255)
    stripe_customer_id = models.CharField(max_length=255)


class Notes (models.Model):
    team = models.ForeignKey('Team',on_delete=models.SET_NULL,null=True,blank=True)
    color = models.CharField(max_length=255,null=True,blank=True)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    body = models.TextField(null=True,blank=True)
    date = models.DateTimeField(auto_now_add=True)
    tags =models.CharField(max_length=255,null=True,blank=True)
    tracker = FieldTracker()
    def __str__(self):
        return  self.title


class Gamification(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='gamification')
    xp_points = models.IntegerField(default=0)
    habits_points = models.IntegerField(default=0)
    list_points = models.IntegerField(default=0)
    notes_points = models.IntegerField(default=0)
    event_points = models.IntegerField(default=0)
    leaderboard_position = models.IntegerField(default=0)

    ICONS = {
        'xp': '🔱',
        'habits': '📈',
        'list': '📋',
        'notes': '🗒️',
        'events': '🎫',
        'total': '🏅',
    }

    def add_xp(self, points):
        self.xp_points += points
        self.save()

    def add_habits_points(self, points):
        self.habits_points += points
        self.save()

    def add_list_points(self, points):
        self.list_points += points
        self.save()

    def add_notes_points(self, points):
        self.notes_points += points
        self.save()

    def add_event_points(self, points):
        self.event_points += points
        self.save()

    def calculate_total_points(self):
        return self.xp_points + self.habits_points + self.list_points + self.notes_points + self.event_points

    def formatted_points(self):
        total_points = self.calculate_total_points()
        return (
            f"{self.ICONS['xp']} XP: {self.xp_points}, "
            f"{self.ICONS['habits']} Habits: {self.habits_points}, "
            f"{self.ICONS['list']} List: {self.list_points}, "
            f"{self.ICONS['notes']} Notes: {self.notes_points}, "
            f"{self.ICONS['events']} Events: {self.event_points}, "
            f"{self.ICONS['total']} Total: {total_points}"
        )


    def calculate_total_points(self):
        return (self.xp_points + self.habits_points + self.list_points +
                self.notes_points + self.event_points)

    @classmethod
    def leaderboard(cls):
        """
        Returns a queryset of users ordered by total points, including user details.
        """
        return cls.objects.select_related('user').annotate(
            total_points=F('xp_points') + F('habits_points') + F('list_points') + F('notes_points') + F('event_points')
        ).order_by('-total_points')


class Article(models.Model):
    LANGUAGES = [
        ('en', 'English'),
        ('fr', 'French'),
        ('de', 'German'),
    ]

    title = models.JSONField(default=dict)  # Stores translations as JSON
    subtitle = models.JSONField(default=dict, blank=True, null=True)
    body = models.JSONField(default=dict)  # Stores HTML-formatted content in multiple languages
    image = CloudinaryField('article_image', blank=True, null=True)
    author_name = models.CharField(max_length=255)
    author_profile_pic = models.ImageField(upload_to='author_pics/', default='default_profile_pic.png')
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    created_date = models.DateTimeField(auto_now_add=True)
    read_by = models.ManyToManyField('CustomUser', related_name='read_articles', blank=True)
    color = models.CharField(max_length=10, default='white')
    quiz = models.JSONField(default=dict, blank=True)  # Stores quiz in multiple languages

    class Meta:
        ordering = ['-created_date']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['created_date']),
        ]

    def clean(self):
        required_languages = {'en', 'fr', 'de'}
        for field in ['title', 'body', 'quiz']:
            field_data = getattr(self, field)
            if not isinstance(field_data, dict):
                raise ValidationError(f"{field} must be a dictionary")
            if set(field_data.keys()) != required_languages:
                raise ValidationError(f"{field} must have translations for en, fr, and de")

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.get_title('en'))
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.get_title('en')

    def get_translated_field(self, field, lang='en'):
        field_data = getattr(self, field)
        return field_data.get(lang, field_data.get('en', ''))

    def get_title(self, lang='en'):
        return self.get_translated_field('title', lang)

    def get_subtitle(self, lang='en'):
        return self.get_translated_field('subtitle', lang)

    def get_body(self, lang='en'):
        return self.get_translated_field('body', lang)

    def get_quiz(self, lang='en'):
        return self.get_translated_field('quiz', lang)

    def get_user_quiz_score(self, user):
        """Returns the quiz score for a specific user."""
        try:
            return self.quiz_scores.get(user=user).score
        except QuizScore.DoesNotExist:
            return None

    def set_user_quiz_score(self, user, score):
        """Sets or updates the quiz score for a user."""
        quiz_score, created = QuizScore.objects.update_or_create(
            user=user, article=self,
            defaults={'score': score}
        )
        return quiz_score
"""
Sample Quiz
{
    "questions": [
        {
            "question": "What is the capital of France?",
            "options": ["Berlin", "Madrid", "Paris", "Rome"],
            "correct_option": 2
        },
        {
            "question": "Who wrote '1984'?",
            "options": ["George Orwell", "Aldous Huxley", "Ray Bradbury", "Isaac Asimov"],
            "correct_option": 0
        },
        {
            "question": "What is 2 + 2?",
            "options": ["3", "4", "5", "6"],
            "correct_option": 1
        }
    ]
}

"""
class QuizScore(models.Model):
    user = models.ForeignKey('CustomUser', on_delete=models.CASCADE, related_name='quiz_scores')
    article = models.ForeignKey('Article', on_delete=models.CASCADE, related_name='quiz_scores')
    score = models.FloatField()  # Store quiz score as a float or integer, depending on your needs
    date_taken = models.DateTimeField(auto_now_add=True)
    selected_answers = models.JSONField(default=dict)  # Store the selected answers as a dictionary

    class Meta:
        unique_together = ('user', 'article')  # Ensure each user can only have one score per article

    def __str__(self):
        return f"{self.user} - {self.article.get_title()} - Score: {self.score}"


class CalendarEvent(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    team = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True, blank=True)
    event_title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    is_shared = models.BooleanField(default=False)
    color = models.CharField(max_length=7, default="#FF5733")
    type = models.CharField(max_length=50, default="event")
    recurrence = models.CharField(max_length=200, blank=True)
    reminders = models.JSONField(default=list,blank=True,null=True)
    status = models.CharField(max_length=20, default="confirmed")
    tracker = FieldTracker()

    def __str__(self):
        return self.event_title