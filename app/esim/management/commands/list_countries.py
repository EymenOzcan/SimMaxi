# management/commands/list_countries.py
from django.core.management.base import BaseCommand
from app.esim.services import eSIMService
from app.esim.models import Country

class Command(BaseCommand):
    help = 'Desteklenen ülkeleri listeler'

    def add_arguments(self, parser):
        parser.add_argument(
            '--provider',
            type=str,
            choices=['esimaccess', 'esimgo', 'database'],
            default='database',
            help='Hangi kaynaktan ülkeler listelenecek'
        )

    def handle(self, *args, **options):
        provider = options['provider']
        
        self.stdout.write(
            self.style.SUCCESS(f'🌍 {provider.upper()} desteklenen ülkeler:')
        )

        try:
            if provider == 'database':
                countries = Country.objects.all().order_by('name')
                for country in countries:
                    self.stdout.write(f'  {country.code} - {country.name}')
                self.stdout.write(f'\nToplam: {countries.count()} ülke')
                
            elif provider == 'esimgo':
                service = eSIMService()
                countries = service.esim_go.get_countries()
                for country in countries:
                    self.stdout.write(f'  {country}')
                self.stdout.write(f'\nToplam: {len(countries)} ülke')
                
            else:
                self.stdout.write(
                    self.style.WARNING('eSIM Access API\'sinde ülke listesi endpoint\'i yok.')
                )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Hata oluştu: {str(e)}')
            )



