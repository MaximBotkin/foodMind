from rest_framework import status
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Dish, SavedDish
from .serializers import DishSerializer


class DishCreateView(CreateAPIView):
    queryset = Dish.objects.all()
    serializer_class = DishSerializer


class RecentDishesView(APIView):
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def get(self, request):
        dishes = Dish.objects.all().order_by('-id')[:10]
        serializer = DishSerializer(dishes, many=True)
        return Response(serializer.data)


class DishSearchView(APIView):
    def get(self, request):
        q = request.query_params.get('q', '')
        dishes = Dish.objects.filter(name__icontains=q)
        serializer = DishSerializer(dishes, many=True)
        return Response(serializer.data)


class SavedDishesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        saved_dishes_ids = SavedDish.objects.filter(user=request.user, is_saved=True).values_list('dish_id', flat=True)

        dishes = Dish.objects.filter(id__in=saved_dishes_ids)
        serializer = DishSerializer(dishes, many=True)
        return Response(serializer.data)

    def post(self, request):
        dish_id = request.data.get('id')
        is_saved = request.data.get('is_saved', False)

        try:
            dish = Dish.objects.get(id=dish_id)

            saved_dish, created = SavedDish.objects.get_or_create(user=request.user, dish=dish,
                defaults={'is_saved': is_saved})

            if not created:
                saved_dish.is_saved = is_saved
                saved_dish.save()

            return Response({"status": "updated"}, status=status.HTTP_200_OK)

        except Dish.DoesNotExist:
            return Response({"error": "Dish not found"}, status=status.HTTP_404_NOT_FOUND)
