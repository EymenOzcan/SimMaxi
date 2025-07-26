from datetime import timezone
from decimal import Decimal
from typing import Dict, List, Optional

from app.esim.models import Country, Provider, eSIMPackage



def sync_esim_packages(self, packages: List[Dict], provider: Provider, target_country: Optional[str] = None):
    created, updated = 0, 0

    if not packages:
        print("[WARNING] Gelen paket listesi boş!")
        return

    for pkg in packages:
        try:
            print(f"İşleniyor: {pkg.get('name') or pkg.get('title')}")
            name = pkg.get("name", "Unnamed Package")
            price_raw = pkg.get("price", 0)
            price = Decimal(str(price_raw)) if price_raw else Decimal(0)
            validity = int(pkg.get("duration", 0) or 0)
            raw_data = pkg
            data_mb = self._parse_data_amount(raw_data)

            # Burada paket benzersiz id varsa ona göre yap
            external_id = pkg.get("id") or pkg.get("external_id")

            # Modelde external_id yoksa, sadece name ve provider ile devam
            filter_kwargs = {"provider": provider}
            if external_id:
                filter_kwargs["external_id"] = external_id
            else:
                filter_kwargs["name"] = name
            breakpoint()
            obj, is_created = eSIMPackage.objects.update_or_create(
                defaults={
                    "name": name,
                    "price": price,
                    "validity_days": validity,
                    "data_amount_mb": data_mb,
                    "detail": pkg,
                    "is_active": True,
                    "updated_at": timezone.now(),
                },
                **filter_kwargs
            )

            country_codes = pkg.get("country_codes", [])
            if country_codes:
                countries_objs = Country.objects.filter(code__in=country_codes)
                obj.countries.set(countries_objs)

            if is_created:
                print(f"[INFO] Paket oluşturuldu: {name}")
                created += 1
            else:
                print(f"[INFO] Paket güncellendi: {name}")
                updated += 1

        except Exception as e:
            print(f"[ERROR] Paket kaydedilirken hata: {e} - Paket: {pkg}")

    print(f"[✓] Toplam {created} paket oluşturuldu, {updated} paket güncellendi.")
