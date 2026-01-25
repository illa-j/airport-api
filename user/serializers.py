from django.contrib.auth import get_user_model
from rest_framework import serializers

from user.models import (
    PasswordResetToken,
    EmailVerificationToken
)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ("id", "email", "password", "is_staff")
        read_only_fields = ("is_staff",)
        extra_kwargs = {"password": {"write_only": True, "min_length": 5}}

    def create(self, validated_data):
        return get_user_model().objects.create_user(**validated_data, is_active=False)


class VerifyEmailSerializer(serializers.Serializer):
    token = serializers.UUIDField()

    def validate_token(self, value):
        try:
            token_obj = EmailVerificationToken.objects.get(token=value)
        except EmailVerificationToken.DoesNotExist:
            raise serializers.ValidationError("Invalid token")

        if token_obj.is_expired():
            raise serializers.ValidationError("Token has expired")

        self.token_obj = token_obj
        return value

    def save(self):
        user = self.token_obj.user
        user.is_active = True
        user.save(update_fields=["is_active"])
        self.token_obj.delete()
        return user


class ConfirmPasswordChangeSerializer(serializers.Serializer):
    token = serializers.UUIDField()

    def validate_token(self, value):
        try:
            token_obj = PasswordResetToken.objects.get(token=value, is_used=False)
        except PasswordResetToken.DoesNotExist:
            raise serializers.ValidationError("Invalid or already used token")

        if token_obj.is_expired():
            raise serializers.ValidationError("Token has expired")

        self.token_obj = token_obj
        return value

    def save(self):
        user = self.token_obj.user
        user.password = self.token_obj.password_hash
        user.save(update_fields=["password"])

        self.token_obj.is_used = True
        self.token_obj.save(update_fields=["is_used"])
        return user


class PasswordChangeSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=5)
