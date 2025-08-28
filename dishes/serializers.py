from rest_framework import serializers

from .models import Dish, SavedDish


class DishSerializer(serializers.ModelSerializer):
    is_saved = serializers.SerializerMethodField()

    class Meta:
        model = Dish
        fields = ['id', 'name', 'callories', 'fats', 'proteins', 'carbohydrates', 'is_saved']
        extra_kwargs = {'callories': {'required': False}}

    def get_is_saved(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return obj.saved_by.filter(id=request.user.id).exists()

    def create(self, validated_data):
        if 'callories' not in validated_data or validated_data['callories'] is None:
            proteins = float(validated_data['proteins'])
            fats = float(validated_data['fats'])
            carbs = float(validated_data['carbohydrates'])
            calories = round(proteins * 4 + carbs * 4 + fats * 9)
            validated_data['callories'] = calories
        return super().create(validated_data)
