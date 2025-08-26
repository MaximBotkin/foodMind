from rest_framework import serializers

from .models import User


class UserUpdateSerializer(serializers.ModelSerializer):
    bmi_status = serializers.CharField(source='get_bmi_status', read_only=True)

    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'gender', 'birth_date', 'age',
                  'height', 'weight', 'bmi', 'bmi_status', 'meta']
        extra_kwargs = {'id': {'read_only': False, 'required': False},
                        'bmi': {'read_only': False, 'required': False},
                        'bmi_status': {'read_only': False, 'required': False},
                        'age': {'read_only': False, 'required': False},}

    def update(self, instance, validated_data):
        instance.weight = validated_data.get('weight', instance.weight)
        instance.height = validated_data.get('height', instance.height)
        if instance.height and instance.weight:
            instance.bmi = round(instance.weight / (instance.height ** 2), 2)
        instance.save()
        return instance

class ProfileSerializer(serializers.ModelSerializer):
    bmi_status = serializers.CharField(source='get_bmi_status', read_only=True)

    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'gender', 'birth_date', 'age', 'height', 'weight', 'bmi', 'bmi_status', 'meta', 'trial_status', 'trial_end_date', 'is_premium', '']

