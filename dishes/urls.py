from django.urls import path
from .views import RecentDishesView, DishSearchView, SavedDishesView, DishCreateView

urlpatterns = [
    path('/', DishCreateView.as_view(), name='dish-create'),
    path('recent/', RecentDishesView.as_view(), name='recent-dishes'),
    path('', DishSearchView.as_view(), name='dish-search'),
    path('my/', SavedDishesView.as_view(), name='saved-dishes'),
]
