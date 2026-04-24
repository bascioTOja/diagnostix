from django.urls import path

from users.api.views import LoginAPIView, LogoutAPIView, ProfileAPIView, RegisterAPIView

urlpatterns = [
    path("register/", RegisterAPIView.as_view(), name="api-register"),
    path("login/", LoginAPIView.as_view(), name="api-login"),
    path("logout/", LogoutAPIView.as_view(), name="api-logout"),
    path("profile/", ProfileAPIView.as_view(), name="api-profile"),
]

