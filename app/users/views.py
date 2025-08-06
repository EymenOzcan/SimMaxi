from django.shortcuts import render
from rest_framework import generics, permissions
from django.contrib.auth import get_user_model
from .serializers import (
    RegisterSerializer,
    UserSerializer,
    ChangePasswordSerializer,
    ResetPasswordSerializer,
)
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from app.dealers.models import Dealer
from .forms import JoinDealerForm

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class UserMeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    def patch(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            old_password = serializer.validated_data["old_password"]
            new_password = serializer.validated_data["new_password"]

            if not request.user.check_password(old_password):
                return Response(
                    {"old_password": "Yanlış şifre"}, status=status.HTTP_400_BAD_REQUEST
                )

            request.user.set_password(new_password)
            request.user.save()
            return Response({"detail": "Şifre başarıyla değiştirildi."})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ResetPasswordView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        if serializer.is_valid():
            # İleride email gönderme eklenecek
            return Response({"detail": "Şifre reset maili gönderildi (mock)."})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    permissions_classes = IsAuthenticated

    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(
                {"detail": "Logout Başarılı"}, status=status.HTTP_205_RESET_CONTENT
            )

        except Exception as e:
            return Response(
                {"error": "Geçersiz token veya eksik parametre"},
                status=status.HTTP_400_BAD_REQUEST,
            )


@login_required
def join_dealer(request):
    if request.method == "POST":
        form = JoinDealerForm(request.POST)
        if form.is_valid():
            secure_id = form.cleaned_data["secure_id"]
            dealer = get_object_or_404(Dealer, secure_id=secure_id)
            request.user.dealer = dealer
            request.user.save()
            return redirect("dashboard")  # yönlendirilecek sayfa
    else:
        form = JoinDealerForm()

    return render(request, "join_dealer.html", {"form": form})
