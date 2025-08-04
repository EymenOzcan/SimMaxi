# app/dealers/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path("join/", views.join_dealer, name="join_dealer"),
    path("<int:dealer_id>/add-user/", views.add_user_to_dealer, name="add_user_to_dealer"),
]
