import requests
from django.core.management.base import BaseCommand
from app.esim.models import Country, Provider, eSIMPackage
from django.utils.timezone import now
import json


class Command(BaseCommand):
    help = "Fetch and save eSIM packages from esimaccess"

    def handle(self, *args, **options):
        provider = Provider.objects.get(slug="esimaccess")
        url = "https://api.esimaccess.com/api/v1/open/package/list"
        headers = {"RT-AccessCode": "2ee5c03386c54f7696d6a1391329730e"}
        payload = {}
        print("GÖNDERİLEN VERİ:", json.dumps(payload, indent=2))

        resp = requests.post(url, headers=headers, json={})

        if not resp.ok:
            self.stderr.write("API yanıtı başarısız oldu.")
            return

        data = resp.json()
        if not data.get("success"):
            self.stderr.write(f"Hata: {data.get('errorMsg')}")
            return

        for package in data["obj"]["packageList"]:
            package_obj, created = eSIMPackage.objects.update_or_create(
                name=package["name"],
                provider=provider,
                defaults={
                    "price": package["retailPrice"] / 100,  # cent -> dolar
                    "validity_days": package["duration"],
                    "data_amount_mb": package["volume"] // 1024 // 1024,
                    "detail": package,
                    "is_active": True,
                    "updated_at": now(),
                },
            )

            # Country
            country_codes = []
            for loc in package.get("locationNetworkList", []):
                country, _ = Country.objects.get_or_create(
                    code=loc["locationCode"],
                    defaults={
                        "name": loc["locationName"],
                        "flag": f"https://api.esimaccess.com{loc['locationLogo']}",
                    },
                )
                country_codes.append(country)

            package_obj.countries.set(country_codes)

            self.stdout.write(
                f"{'Oluşturuldu' if created else 'Güncellendi'}: {package_obj.name}"
            )
