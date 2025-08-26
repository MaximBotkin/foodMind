from rest_framework import serializers

from .models import User


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'gender', 'birth_date', 'height', 'weight', 'meta']
        extra_kwargs = {'id': {'read_only': False, 'required': False}}
