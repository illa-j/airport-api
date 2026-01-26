from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

from user.views import (
    CreateUserView,
    ManageUserView,
    VerifyEmailAPIView,
    ConfirmPasswordChangeView,
    ChangePasswordView,
)

app_name = "user"

urlpatterns = [
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("token/verify/", TokenVerifyView.as_view(), name="token_verify"),
    path("me/", ManageUserView.as_view(), name="manage"),
    path("register/", CreateUserView.as_view(), name="register"),
    path("change-password/", ChangePasswordView.as_view(), name="change_password"),
    path("verify-email/", VerifyEmailAPIView.as_view(), name="verify_email"),
    path(
        "confirm-password-change/",
        ConfirmPasswordChangeView.as_view(),
        name="confirm_password_change",
    ),
]
