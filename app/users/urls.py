from django.urls import path
from .views import RegisterView, UserMeView, ChangePasswordView, ResetPasswordView,LogoutView
from rest_framework_simplejwt.views import TokenObtainPairView,TokenRefreshView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('me/', UserMeView.as_view(), name='user-me'),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset-password'),
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('logout/',LogoutView.as_view(),name='logout view'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
