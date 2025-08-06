from decimal import Decimal
from django.utils import timezone
from django.db import models


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Country(models.Model):
    name = models.CharField(max_length=190)
    code = models.CharField(max_length=20)
    flag = models.URLField()
    is_active = models.BooleanField(default=True)
    is_regional = models.BooleanField(default=False)
    is_global = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} ({self.code})"

    class Meta:
        verbose_name = "Ülke"
        verbose_name_plural = "Ülkeler"
        ordering = ["name"]


class Provider(TimeStampedModel):
    name = models.CharField(max_length=255)
    slug = models.CharField(max_length=100)
    api_key = models.CharField(max_length=500)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Sağlayıcı"
        verbose_name_plural = "Sağlayıcılar"
        ordering = ["name"]


class eSIMPackage(TimeStampedModel):
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    validity_days = models.PositiveIntegerField()
    data_amount_mb = models.PositiveIntegerField()
    slug = models.TextField(max_length=90)
    detail = models.JSONField()
    is_active = models.BooleanField(default=False)
    provider = models.ForeignKey(Provider, on_delete=models.CASCADE)
    countries = models.ManyToManyField(Country)
    external_id = models.CharField(max_length=255, blank=True, null=True, unique=True)
    is_offered = models.BooleanField(
        default=False, verbose_name="Sunulan Paket olarak işaretle"
    )

    def __str__(self):
        return f"{self.name} - ${self.price}"

    @property
    def data_display(self):
        if self.data_amount_mb >= 1024:
            gb = self.data_amount_mb / 1024
            return f"{gb:.1f} GB"
        return f"{self.data_amount_mb} MB"

    @property
    def countries_count(self):
        return self.countries.count()

    class Meta:
        verbose_name = "eSIM Paketi"
        verbose_name_plural = "eSIM Paketleri"
        ordering = ["-updated_at"]


class OfferedPackage(models.Model):
    esim = models.ForeignKey(eSIMPackage, on_delete=models.CASCADE)
    title = models.CharField(max_length=50)
    explanation = models.CharField(max_length=70)
    end_user_sales = models.BooleanField(default=True)
    dealer_sale = models.BooleanField(default=True)
    status = models.BooleanField(default=True)

    cost_multiplier = models.DecimalField(
        "Maliyet Çarpanı", max_digits=5, decimal_places=2, default=Decimal("1.00")
    )
    sales_multiplier = models.DecimalField(
        "Satış Çarpanı", max_digits=5, decimal_places=2, default=Decimal("1.00")
    )
    cost_price = models.DecimalField(
        "Maliyet Fiyatı (API'den Gelen)",
        max_digits=12,
        decimal_places=2,
        editable=False,
    )
    sale_price = models.DecimalField(
        "Satış Fiyatı", max_digits=12, decimal_places=2, editable=False
    )

    def save(self, *args, **kwargs):
        # esim paketinden fiyatı çek
        if self.esim and self.esim.price is not None:
            self.cost_price = self.esim.price

        # satış fiyatını otomatik hesapla
        self.sale_price = (
            (self.cost_price or Decimal("0.00"))
            * (self.cost_multiplier or Decimal("1.00"))
            * (self.sales_multiplier or Decimal("1.00"))
        )

        super().save(*args, **kwargs)
