from django.urls import path

from .views import TMAAuthView, StartTrialView, CreateProfileView

urlpatterns = [
    path("auth/tma/", TMAAuthView.as_view(), name="tma-auth"),
    path("start-trial/", StartTrialView.as_view(), name="start-trial"),
    path("create-profile/", CreateProfileView.as_view(), name="create-profile"),
]
