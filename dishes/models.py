# dishes/models.py
from django.conf import settings
from django.db import models


class Dish(models.Model):
    name = models.CharField(max_length=255, verbose_name='Название блюда')
    callories = models.PositiveIntegerField(verbose_name='Калории')
    fats = models.FloatField(verbose_name='Жиры')
    proteins = models.FloatField(verbose_name='Протеин')
    carbohydrates = models.FloatField(verbose_name='Углеводы')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')

    def save(self, *args, **kwargs):
        if not self.callories:
            self.callories = round(
                (float(self.proteins) * 4) + (float(self.carbohydrates) * 4) + (float(self.fats) * 9))
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class SavedDish(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    dish = models.ForeignKey(Dish, on_delete=models.CASCADE)
    is_saved = models.BooleanField(default=True)

    class Meta:
        unique_together = ('user', 'dish')
