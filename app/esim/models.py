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
    detail = models.JSONField()
    is_active = models.BooleanField(default=False)
    provider = models.ForeignKey(Provider, on_delete=models.CASCADE)
    countries = models.ManyToManyField(Country)
    external_id = models.CharField(max_length=255, blank=True, null=True, unique=True)

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

