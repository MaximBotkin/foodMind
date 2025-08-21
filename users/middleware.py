from django.utils.deprecation import MiddlewareMixin
from django.utils import timezone
from .models import User

class CheckTrialMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if request.user.is_authenticated:
            request.user.check_trial_status()
