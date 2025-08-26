from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.utils.timezone import now
from django.utils.crypto import get_random_string
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import UserUpdateSerializer, ProfileSerializer
from .tma import extract_user_from_init_data, TMAValidationError, TMATokenExpired

User = get_user_model()


def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {"access": str(refresh.access_token), "refresh": str(refresh)}


class TMAAuthView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        auth_header = request.headers.get("Authorization", "")
        print(auth_header)
        if not auth_header.startswith("tma "):
            return Response({"detail": "Authorization header must start with 'tma '"},
                            status=status.HTTP_400_BAD_REQUEST)

        init_data_raw = auth_header[4:].strip()
        if not init_data_raw:
            return Response({"detail": "Empty init_data in Authorization header"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user_data = extract_user_from_init_data(init_data_raw)
            telegram_id = user_data.get("id")
            if not telegram_id:
                return Response({"detail": "User ID is required"}, status=status.HTTP_400_BAD_REQUEST)

            try:
                user = User.objects.get(telegram_id=telegram_id)
                created = False
            except User.DoesNotExist:
                user = None
                created = True

            if created:
                random_password = get_random_string(50)
                username = user_data.get("username") or f"tg_{telegram_id}"

                with transaction.atomic():
                    try:
                        user = User.objects.create_user(username=username, password=random_password,
                                                        telegram_id=telegram_id,
                                                        telegram_username=user_data.get("username"),
                                                        first_name=user_data.get("first_name") or "",
                                                        last_name=user_data.get("last_name") or "",
                                                        language_code=user_data.get("language_code", "ru"),
                                                        is_bot=user_data.get("is_bot", False), )
                    except TypeError:
                        user = User.objects.create(username=username, telegram_id=telegram_id,
                                                   telegram_username=user_data.get("username"),
                                                   first_name=user_data.get("first_name") or "",
                                                   last_name=user_data.get("last_name") or "",
                                                   language_code=user_data.get("language_code", "ru"),
                                                   is_bot=user_data.get("is_bot", False), password=random_password, )
                        user.set_password(random_password)
                        user.save(update_fields=["password"])

                    except IntegrityError:
                        try:
                            user = User.objects.get(telegram_id=telegram_id)
                        except User.DoesNotExist:
                            raise

            else:
                changed = False
                if user.telegram_username != user_data.get("username"):
                    user.telegram_username = user_data.get("username")
                    changed = True
                if user.first_name != (user_data.get("first_name") or ""):
                    user.first_name = user_data.get("first_name") or ""
                    changed = True
                if user.last_name != (user_data.get("last_name") or ""):
                    user.last_name = user_data.get("last_name") or ""
                    changed = True
                if getattr(user, "language_code", None) != user_data.get("language_code", "ru"):
                    user.language_code = user_data.get("language_code", "ru")
                    changed = True
                if getattr(user, "is_bot", False) != user_data.get("is_bot", False):
                    user.is_bot = user_data.get("is_bot", False)
                    changed = True

                if changed:
                    user.save()

            tokens = get_tokens_for_user(user)
            trial_status = user.check_trial_status()

            return Response({
                "user": {"id": user.id, "telegram_id": user.telegram_id, "username": user.telegram_username,
                         "first_name": user.first_name, "last_name": user.last_name,
                         "is_premium": getattr(user, "is_premium", False), "premium_end_date": user.premium_end_date,
                         "language_code": getattr(user, "language_code", "ru"), "trial_status": trial_status,
                         "trial_end_date": user.trial_end_date}, "tokens": tokens}, status=status.HTTP_200_OK)

        except TMATokenExpired:
            return Response({"detail": "init_data expired"}, status=status.HTTP_401_UNAUTHORIZED)
        except TMAValidationError as e:
            return Response({"detail": f"Validation error: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"detail": f"Server error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserUpdateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request):
        user = request.user

        serializer = UserUpdateSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user

        serializer = ProfileSerializer(user)
        return Response(serializer.data)


class TrialStatusView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        if hasattr(user, 'trial_end_date') and user.trial_end_date:
            if user.trial_end_date > now():
                return Response({"trial_active": True, "trial_ends": user.trial_end_date}, status=status.HTTP_200_OK)
            else:
                return Response({"trial_active": False, "trial_ended": user.trial_end_date}, status=status.HTTP_200_OK)
        return Response({"trial_active": False, "trial_ended": None}, status=status.HTTP_200_OK)


class TrialStartView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        if hasattr(user, 'trial_end') and user.trial_end_date and user.trial_end_date > now():
            return Response({"detail": "Trial already active", "trial_ends": user.trial_end_date},
                            status=status.HTTP_400_BAD_REQUEST)

        if hasattr(user, 'trial_status') and user.trial_status == 'ENDED':
            return Response({"detail": "Trial has already ended", "trial_status": user.trial_status},
                            status=status.HTTP_400_BAD_REQUEST)

        user.start_trial()

        return Response({"detail": "Trial started", "trial_ends": user.trial_end_date}, status=status.HTTP_201_CREATED)
