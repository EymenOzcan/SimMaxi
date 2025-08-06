from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import eSIMPackage, OfferedPackage


@receiver(post_save, sender=eSIMPackage)
def create_offered_package(sender, instance, created, **kwargs):
    if instance.is_offered:
        OfferedPackage.objects.get_or_create(
            esim=instance,
            defaults={
                "title": instance.name[:50],
                "explanation": (
                    getattr(instance, "explanation", "")[:70]
                    if hasattr(instance, "explanation")
                    else ""
                ),
                "end_user_sales": True,
                "dealer_sale": True,
                "status": True,
            },
        )
    else:
        # Eğer işaret kaldırıldıysa, ilgili OfferedPackage varsa sil
        OfferedPackage.objects.filter(esim=instance).delete()
