from django.urls import path

from .views import TMAAuthView, UserUpdateView, TrialStartView, TrialStatusView

urlpatterns = [
    path('auth/tma/', TMAAuthView.as_view(), name='tma-auth'),
    path('update-profile/', UserUpdateView.as_view(), name='user-update'),
    path('subscription/trial/status/', TrialStatusView.as_view(), name='trial-status'),
    path('subscription/trial/start/', TrialStartView.as_view(), name='trial-start'),
]
