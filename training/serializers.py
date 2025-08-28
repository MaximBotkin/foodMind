from rest_framework import serializers

from .models import Training


class TrainingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Training
        fields = ['id', 'type', 'duration', 'intensity', 'callories', 'created_at']
        read_only_fields = ['callories', 'created_at']

    def validate(self, data):
        if data['type'] == 'manual':
            if 'callories' not in data:
                raise serializers.ValidationError("For manual training, callories is required.")
        else:
            if 'duration' not in data or 'intensity' not in data:
                raise serializers.ValidationError("For non-manual training, duration and intensity are required.")
        return data
