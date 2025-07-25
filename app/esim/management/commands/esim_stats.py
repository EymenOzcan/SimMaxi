# management/commands/esim_stats.py
from django.core.management.base import BaseCommand
from app.esim.models import eSIMPackage, Provider, Country
from django.db.models import Count, Q

class Command(BaseCommand):
    help = 'eSIM paket istatistiklerini gösterir'

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('📊 eSIM Paket İstatistikleri')
        )
        self.stdout.write('=' * 50)

        # Provider bazlı istatistikler
        providers = Provider.objects.annotate(
            total_packages=Count('esimpackage'),
            active_packages=Count('esimpackage', filter=Q(esimpackage__is_active=True))
        )

        for provider in providers:
            self.stdout.write(f'\n🏢 {provider.name}:')
            self.stdout.write(f'  Toplam Paket: {provider.total_packages}')
            self.stdout.write(f'  Aktif Paket: {provider.active_packages}')
            self.stdout.write(f'  Pasif Paket: {provider.total_packages - provider.active_packages}')

        # Ülke bazlı istatistikler
        self.stdout.write(f'\n🌍 Ülke Bazlı İstatistikler:')
        countries_with_packages = Country.objects.annotate(
            package_count=Count('esimpackage', filter=Q(esimpackage__is_active=True))
        ).filter(package_count__gt=0).order_by('-package_count')[:10]

        for country in countries_with_packages:
            self.stdout.write(f'  {country.code} ({country.name}): {country.package_count} paket')

        # Genel istatistikler
        total_packages = eSIMPackage.objects.count()
        active_packages = eSIMPackage.objects.filter(is_active=True).count()
        
        self.stdout.write(f'\n📈 Genel İstatistikler:')
        self.stdout.write(f'  Toplam Paket: {total_packages}')
        self.stdout.write(f'  Aktif Paket: {active_packages}')
        self.stdout.write(f'  Pasif Paket: {total_packages - active_packages}')
        self.stdout.write(f'  Toplam Provider: {Provider.objects.count()}')
        self.stdout.write(f'  Paket bulunan ülke: {countries_with_packages.count()}')