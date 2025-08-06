from django.db import models
from phonenumber_field.modelfields import PhoneNumberField

from app.dealers.utils import generate_base62_id

# Create your models here.


class Dealer(models.Model):
    dealer_name = models.TextField(max_length=100)
    secure_id = models.CharField(
        max_length=12, unique=True, editable=False, default=generate_base62_id
    )
    is_active = models.BooleanField(default=True)
    commission_rate = models.DecimalField(
        max_digits=5,  # örn. 100.00'e kadar destekler
        decimal_places=2,  # 2 basamak (örn. 5.50 = %5,5)
        help_text="Komisyon oranını yüzde olarak giriniz. (Örn: 5.00 = %5)",
    )
    email = models.EmailField()
    phone_number = PhoneNumberField(unique=True, region="TR")
    adress = models.TextField()
    authorized_name = models.TextField(blank=False)
    dealer_balance = models.DecimalField(
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
        return f"{self.dealer_name} (%{self.commission_rate})"


class DealerRole(models.Model):
    ROLE_CHOICES = [
        ("admin", "Admin"),
        ("editor", "Editor"),
        ("viewer", "Viewer"),
    ]

    user = models.ForeignKey("users.CustomUser", on_delete=models.CASCADE)
    dealer = models.ForeignKey(Dealer, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

    class Meta:
        unique_together = ("user", "dealer")

    def __str__(self):
        return f"{self.user.email} -> {self.dealer.dealer_name} ({self.role})"
