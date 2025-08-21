import json

from django.contrib.auth import get_user_model
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import UserSerializer, UserProfileSerializer
from .tma import validate_init_data, TMAValidationError, TMATokenExpired, check_telegram_auth

User = get_user_model()


def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {"access": str(refresh.access_token), "refresh": str(refresh)}


class CreateProfileView(APIView):
    def post(self, request):
        init_data = request.data.get('init_data')
        if not init_data:
            return Response({'detail': 'init_data required'}, status=status.HTTP_400_BAD_REQUEST)

        if not validate_init_data(init_data):
            return Response({'detail': 'Invalid init_data'}, status=status.HTTP_400_BAD_REQUEST)

        telegram_data = json.loads(init_data)
        user_data = telegram_data.get('user', {})

        user, created = User.objects.get_or_create(telegram_id=user_data.get('id'),
            defaults={'telegram_username': user_data.get('username'), 'first_name': user_data.get('first_name'),
                'last_name': user_data.get('last_name'), 'language_code': user_data.get('language_code', 'ru'),
                'is_bot': user_data.get('is_bot', False), 'init_data': init_data})

        extra_serializer = UserProfileSerializer(user, data=request.data, partial=True)
        if extra_serializer.is_valid():
            extra_serializer.save()
        else:
            return Response(extra_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        return Response({'id': user.id, 'telegram_id': user.telegram_id, 'telegram_username': user.telegram_username,
            'first_name': user.first_name, 'last_name': user.last_name, 'language_code': user.language_code,
            'is_bot': user.is_bot, 'gender': user.gender, 'birth_date': user.birth_date, 'height': user.height,
            'weight': user.weight, 'meta': user.meta}, status=status.HTTP_201_CREATED)


class TMAAuthView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        auth_hdr = request.headers.get("Authorization", "")
        init_data_raw = auth_hdr[4:].strip() if auth_hdr.startswith("tma ") else request.data.get("init_data", "")
        if not init_data_raw:
            return Response({"detail": "init_data required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            pairs = validate_init_data(init_data_raw)
        except TMATokenExpired:
            return Response({"detail": "init_data expired"}, status=status.HTTP_401_UNAUTHORIZED)
        except TMAValidationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_401_UNAUTHORIZED)

        user_json = pairs.get("user")
        if not user_json:
            return Response({"detail": "user field missing"}, status=status.HTTP_400_BAD_REQUEST)
        user_obj = json.loads(user_json)
        telegram_id = user_obj.get("id")
        if not telegram_id:
            return Response({"detail": "id missing in user"}, status=status.HTTP_400_BAD_REQUEST)

        user, _ = User.objects.update_or_create(telegram_id=telegram_id,
                                                defaults={"telegram_username": user_obj.get("username"),
                                                          "first_name": user_obj.get("first_name"),
                                                          "last_name": user_obj.get("last_name"),
                                                          "language_code": user_obj.get("language_code"),
                                                          "is_bot": user_obj.get("is_bot", False),
                                                          "init_data": init_data_raw,
                                                          "web_app_query_id": pairs.get("query_id"),
                                                          "is_premium": bool(user_obj.get("is_premium")), })

        tokens = get_tokens_for_user(user)
        return Response({"user": UserSerializer(user).data, "tokens": tokens})


class StartTrialView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        user.start_trial(days=3)
        return Response({"detail": f"Trial started, ends at {user.trial_end_date}", "status": user.trial_status})
