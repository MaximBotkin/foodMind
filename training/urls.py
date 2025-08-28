from django.urls import path

from .views import TrainingCreateView

urlpatterns = [path('training/', TrainingCreateView.as_view(), name='create-training'), ]
