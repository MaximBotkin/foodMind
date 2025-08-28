from django.conf import settings
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class Training(models.Model):
    TYPE_CHOICES = [('run', 'Run'), ('gym', 'Gym'), ('manual', 'Manual'), ]
    INTENSITY_CHOICES = [('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='trainings', verbose_name='Пользователь')
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, verbose_name='Тип тренировки')
    duration = models.PositiveIntegerField(null=True, blank=True, help_text="Duration in minutes", validators=[MinValueValidator(1), MaxValueValidator(500)], verbose_name='Длительность')
    intensity = models.CharField(max_length=10, choices=INTENSITY_CHOICES, null=True, blank=True, verbose_name='Интенсивность')
    callories = models.PositiveIntegerField(null=True, blank=True, verbose_name='Калории')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')

    def calculate_calories(self):
        if self.type == 'manual':
            return self.callories
        if not self.duration or not self.intensity:
            return None
        weight = getattr(self.user, 'weight', None)
        if not weight:
            return None

        intensity_factors = {'low': 5, 'medium': 8, 'high': 12}
        factor = intensity_factors.get(self.intensity, 8)
        return round(factor * float(weight) * (self.duration / 60))

    def save(self, *args, **kwargs):
        if self.type != 'manual':
            self.callories = self.calculate_calories()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Тренировка от {self.user.username} - {self.type} ({self.created_at.date()})"
