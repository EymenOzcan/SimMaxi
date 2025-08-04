from django.db import models
from phonenumber_field.modelfields import PhoneNumberField

# Create your models here.

class Dealer(models.Model):
    dealer_name = models.TextField(max_length=100)
    is_active = models.BooleanField(default=True)
    commission_rate = models.DecimalField(
        max_digits=5,      # örn. 100.00'e kadar destekler
        decimal_places=2,  # 2 basamak (örn. 5.50 = %5,5)
        help_text="Komisyon oranını yüzde olarak giriniz. (Örn: 5.00 = %5)"
    )
    email = models.EmailField()
    phone_number = PhoneNumberField(unique=True, region='TR')
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