from rest_framework import serializers

from .models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "telegram_id", "telegram_username", "first_name", "last_name", "language_code", "trial_status",
                  "is_premium")


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['gender', 'birth_date', 'height', 'weight', 'meta', 'source']
