from datetime import date, timedelta

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone


class User(AbstractUser):
    class Gender(models.TextChoices):
        MALE = 'M', 'Мужской'
        FEMALE = 'F', 'Женский'

    class TrialStatus(models.TextChoices):
        NOT_STARTED = 'NOT_STARTED', 'Не начат'
        IN_PROGRESS = 'IN_PROGRESS', 'В процессе'
        ENDED = 'ENDED', 'Окончен'

    username = models.CharField(max_length=150, null=True, blank=True, unique=False)

    telegram_id = models.BigIntegerField(unique=True, null=True)
    telegram_username = models.CharField(max_length=64, blank=True, null=True)
    first_name = models.CharField(max_length=64, blank=True, null=True, verbose_name='Имя')
    last_name = models.CharField(max_length=64, blank=True, null=True, verbose_name='Фамилия')
    language_code = models.CharField(max_length=10, default='ru', null=True, blank=True, verbose_name='Язык')

    # Дополнительные поля для Mini App
    init_data = models.TextField(blank=True, null=True)
    web_app_query_id = models.CharField(max_length=64, blank=True, null=True)
    is_bot = models.BooleanField(default=False, verbose_name='Бот')

    gender = models.CharField(max_length=1, choices=Gender.choices, blank=True, null=True, verbose_name='Пол')
    birth_date = models.DateField(blank=True, null=True, verbose_name='Дата рождения', validators=[
        MinValueValidator(date(1900, 1, 1), message="Дата рождения не может быть раньше 1900 года.")])
    height = models.PositiveSmallIntegerField(blank=True, null=True, verbose_name='Рост', validators=[
        MinValueValidator(50, message="Рост не может быть меньше 50 см."),
        MaxValueValidator(250, message="Рост не может быть больше 250 см.")])  # В см
    weight = models.DecimalField(max_digits=5, decimal_places=1, blank=True, null=True, verbose_name='Вес',
                                 validators=[MinValueValidator(20, message="Вес не может быть меньше 20 кг."),
                                             MaxValueValidator(300,
                                                               message="Вес не может быть больше 300 кг.")])  # В кг
    meta = models.JSONField(default=dict, blank=True, null=True, verbose_name='Дополнительная информация')

    trial_status = models.CharField(max_length=12, choices=TrialStatus.choices, default=TrialStatus.NOT_STARTED,
                                    verbose_name='Пробный период')
    trial_end_date = models.DateTimeField(blank=True, null=True, verbose_name='Конец пробного периода')
    is_premium = models.BooleanField(default=False, verbose_name='Премиум подписка')
    premium_end_date = models.DateTimeField(blank=True, null=True, verbose_name='Окончание подписки')

    created_at = models.DateTimeField(default=timezone.now, editable=False, verbose_name='Дата создания профиля')
    source = models.CharField(max_length=100, null=True, blank=True, verbose_name='Откуда узнали о приложении')

    USERNAME_FIELD = 'telegram_id'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ['-created_at']

    def start_trial(self, days=3):
        if self.trial_status == self.TrialStatus.NOT_STARTED:
            self.trial_status = self.TrialStatus.IN_PROGRESS
            self.trial_end_date = timezone.now() + timedelta(days=days)
            self.save()

    def check_trial_status(self):
        if self.trial_status == self.TrialStatus.IN_PROGRESS and self.trial_end_date <= timezone.now():
            self.trial_status = self.TrialStatus.ENDED
            self.save()
        return self.trial_status

    @classmethod
    def create_from_telegram_data(cls, telegram_data):
        user_data = telegram_data.get('user', {})
        return cls.objects.create(telegram_id=user_data.get('id'), first_name=user_data.get('first_name'),
                                  last_name=user_data.get('last_name'), username=user_data.get('telegram_username'),
                                  language_code=user_data.get('language_code'), is_bot=user_data.get('is_bot', False),
                                  init_data=str(telegram_data))

    def clean(self):
        super().clean()

        if self.birth_date:
            if self.birth_date > date.today():
                raise ValidationError({'birth_date': "Дата рождения не может быть в будущем."})
            age = date.today().year - self.birth_date.year
            if age > 120:
                raise ValidationError({'birth_date': "Возраст не может быть больше 120 лет."})

        if self.height and (self.height < 50 or self.height > 250):
            raise ValidationError({'height': "Рост должен быть между 50 и 250 см."})

        if self.weight and (self.weight < 20 or self.weight > 300):
            raise ValidationError({'weight': "Вес должен быть между 20 и 300 кг."})

    def save(self, *args, **kwargs):
        self.full_clean()
        if not self.pk:
            self.created_at = timezone.now()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.telegram_username or self.telegram_id}"
