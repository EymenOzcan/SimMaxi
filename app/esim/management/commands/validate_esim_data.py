from django.core.management.base import BaseCommand
from app.esim.models import eSIMPackage, Country
from decimal import Decimal


class Command(BaseCommand):
    help = "eSIM paket verilerini doğrular ve hatalı olanları listeler"

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("🔍 eSIM Paket Verisi Doğrulaması"))
        self.stdout.write("=" * 50)

        issues = []

        active_packages = eSIMPackage.objects.filter(is_active=True)

        for pkg in active_packages:
            pkg_issues = []

            if pkg.price <= Decimal("0"):
                pkg_issues.append("Fiyat 0 veya negatif")

            if pkg.data_amount_mb <= 0:
                pkg_issues.append("Veri miktarı 0 veya negatif")

            if pkg.validity_days <= 0:
                pkg_issues.append("Geçerlilik süresi 0 veya negatif")

            if not pkg.name or pkg.name.strip() == "" or pkg.name == "Unnamed Package":
                pkg_issues.append("İsim boş veya varsayılan")

            if not pkg.countries.exists():
                pkg_issues.append("Hiç ülke atanmamış")

            if pkg_issues:
                issues.append({"package": pkg, "issues": pkg_issues})

        if issues:
            self.stdout.write(
                self.style.ERROR(f"❌ {len(issues)} pakette sorun bulundu:")
            )

            for item in issues[:20]:
                pkg = item["package"]
                self.stdout.write(f"\n📦 {pkg.name} ({pkg.provider.name}):")
                for issue in item["issues"]:
                    self.stdout.write(f"  ⚠️  {issue}")

            if len(issues) > 20:
                self.stdout.write(f"\n... ve {len(issues) - 20} sorun daha")
        else:
            self.stdout.write(
                self.style.SUCCESS("✅ Tüm aktif paketler geçerli veri içeriyor")
            )

        # Özet istatistikler
        total_active = active_packages.count()
        problematic_count = len(issues)
        success_rate = (
            ((total_active - problematic_count) / total_active * 100)
            if total_active > 0
            else 0
        )

        self.stdout.write(f"\n📊 Özet:")
        self.stdout.write(f"  Toplam aktif paket: {total_active}")
        self.stdout.write(f"  Sorunlu paket: {problematic_count}")
        self.stdout.write(f"  Başarı oranı: {success_rate:.1f}%")
