# management/commands/cleanup_esim_packages.py
from django.core.management.base import BaseCommand
from app.esim.models import eSIMPackage
from django.utils import timezone
from datetime import timedelta


class Command(BaseCommand):
    help = "Eski ve pasif eSIM paketlerini temizler"

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=30,
            help="Kaç gün önce güncellenen pasif paketler silinecek (varsayılan: 30)",
        )
        parser.add_argument(
            "--dry-run", action="store_true", help="Sadece göster, silme işlemi yapma"
        )

    def handle(self, *args, **options):
        days = options["days"]
        dry_run = options["dry_run"]

        cutoff_date = timezone.now() - timedelta(days=days)

        # Silinecek paketleri bul
        packages_to_delete = eSIMPackage.objects.filter(
            is_active=False, updated_at__lt=cutoff_date
        )

        count = packages_to_delete.count()

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f"🔍 DRY RUN: {count} paket silinecek (son {days} gün içinde güncellenmemiş pasif paketler)"
                )
            )

            # İlk 10 paketi göster
            for pkg in packages_to_delete[:10]:
                self.stdout.write(
                    f"  - {pkg.name} ({pkg.provider.name}) - Son güncelleme: {pkg.updated_at}"
                )

            if count > 10:
                self.stdout.write(f"  ... ve {count - 10} paket daha")
        else:
            packages_to_delete.delete()
            self.stdout.write(
                self.style.SUCCESS(f"✅ {count} adet eski pasif paket silindi")
            )
