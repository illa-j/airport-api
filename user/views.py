from django.conf import settings
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from user.models import EmailVerificationToken
from user.serializers import (
    UserSerializer,
    VerifyEmailSerializer
)


class CreateUserView(generics.CreateAPIView):
    serializer_class = UserSerializer
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"

    def perform_create(self, serializer):
        user = serializer.save()

        token = EmailVerificationToken.objects.create(user=user)
        verify_url = (
            f"{settings.FRONTEND_URL}/verify-email"
            f"?token={token.token}"
        )

        send_mail(
            subject="Verify your email",
            message=f"Click to verify: {verify_url}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
        )

class ManageUserView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticated,)
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"

    def get_object(self):
        return self.request.user


class VerifyEmailAPIView(APIView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"

    def post(self, request):
        serializer = VerifyEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        token = serializer.validated_data["token"]

        token_obj = get_object_or_404(
            EmailVerificationToken, token=token
        )

        user = token_obj.user
        user.is_active = True
        user.save()

        token_obj.delete()

        return Response(
            {"detail": "Email verified successfully"},
            status=status.HTTP_200_OK
        )
