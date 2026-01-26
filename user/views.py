from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.core.mail import send_mail
from django.urls import reverse
from rest_framework import generics, status
from rest_framework.generics import CreateAPIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from user.models import EmailVerificationToken, PasswordResetToken
from user.serializers import (
    UserSerializer,
    VerifyEmailSerializer,
    ConfirmPasswordChangeSerializer,
    PasswordChangeSerializer,
)


class CreateUserView(CreateAPIView):
    serializer_class = UserSerializer
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"

    def perform_create(self, serializer):
        user = serializer.save()

        token = EmailVerificationToken.objects.create(user=user)

        verify_link = (
            self.request.build_absolute_uri(reverse("user:verify_email"))
            + f"?token={token.token}"
        )

        send_mail(
            subject="Verify your email",
            message=f"Click to verify: {verify_link}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
        )


class ChangePasswordView(CreateAPIView):
    serializer_class = PasswordChangeSerializer
    permission_classes = (IsAuthenticated,)
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            user = get_user_model().objects.get(email=request.data["email"])
            raw_password = serializer.validated_data["password"]
            password_hash = make_password(raw_password)

            token = PasswordResetToken.objects.create(
                user=user,
                password_hash=password_hash,
            )

            confirm_link = (
                request.build_absolute_uri(reverse("user:confirm_password_change"))
                + f"?token={token.token}"
            )

            send_mail(
                subject="Confirm password change",
                message=f"Click to confirm password change: {confirm_link}",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
            )
        except get_user_model().DoesNotExist:
            pass

        return Response(
            {"detail": "If the email exists, a confirmation email has been sent"},
            status=status.HTTP_200_OK,
        )


class ManageUserView(generics.RetrieveAPIView):
    serializer_class = UserSerializer
    permission_classes = (IsAuthenticated,)
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"

    def get_object(self):
        return self.request.user


class VerifyEmailAPIView(APIView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "token_verification"

    def get(self, request):
        serializer = VerifyEmailSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        serializer.save()

        return Response(
            {"detail": "Email verified successfully"}, status=status.HTTP_200_OK
        )


class ConfirmPasswordChangeView(APIView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "token_verification"

    def get(self, request):
        serializer = ConfirmPasswordChangeSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        serializer.save()

        return Response(
            {"detail": "Password changed successfully"},
            status=status.HTTP_200_OK,
        )
