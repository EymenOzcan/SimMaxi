# app/dealers/forms.py

from django import forms
from app.users.models import CustomUser
from .models import DealerRole


class JoinDealerForm(forms.Form):
    secure_id = forms.CharField(max_length=12, label="Bayi Secure ID")


class AddDealerUserForm(forms.Form):
    user = forms.ModelChoiceField(
        queryset=CustomUser.objects.filter(dealer__isnull=True)
    )
    role = forms.ChoiceField(choices=DealerRole.ROLE_CHOICES)
