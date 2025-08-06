from django.contrib.auth.models import AbstractUser
from django.db import models

from app.dealers.models import Dealer


class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    dealer = models.ForeignKey(Dealer, blank=True, null=True, on_delete=models.CASCADE)
    balance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="Kullanıcının mevcut bakiyesi",
    )

    CURRENCY_CHOICES = [
        ("USD", "US Dollar"),
        ("EUR", "Euro"),
        ("TRY", "Turkish Lira"),
    ]
    currency = models.CharField(
        max_length=3,
        choices=CURRENCY_CHOICES,
        default="USD",
        help_text="Bakiyenin tutulduğu para birimi",
    )

    def __str__(self):
        return self.username

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    def __str__(self):
        return self.email
