from __future__ import annotations

from django.contrib.auth import authenticate, login, logout
from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from users.api.serializers import LoginSerializer, ProfileSerializer, RegisterSerializer


class RegisterAPIView(APIView):
    permission_classes = (AllowAny,)
    authentication_classes = tuple()

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(ProfileSerializer(user).data, status=status.HTTP_201_CREATED)


class LoginAPIView(APIView):
    permission_classes = (AllowAny,)
    authentication_classes = tuple()

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = authenticate(
            request,
            email=serializer.validated_data["email"],
            password=serializer.validated_data["password"],
        )
        if user is None:
            raise AuthenticationFailed("Niepoprawny email lub haslo.")

        login(request, user)
        return Response(ProfileSerializer(user).data, status=status.HTTP_200_OK)


class LogoutAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProfileAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        return Response(ProfileSerializer(request.user).data, status=status.HTTP_200_OK)

    def patch(self, request):
        serializer = ProfileSerializer(instance=request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

