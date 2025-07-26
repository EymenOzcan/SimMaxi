from decimal import Decimal
import wave
import requests
from requests.exceptions import RequestException, Timeout
from typing import Optional, List, Dict, Any
import time

from app.esim.models import Country, Provider, eSIMPackage
from django.utils import timezone


class BaseService:
    def __init__(self, base_url, headers=None, timeout=10):
        self.base_url = base_url.rstrip("/")
        self.headers = headers or {}
        self.timeout = timeout

    def _handle_response(self, response):
        try:
            response.raise_for_status()
            json_data = response.json()
            print(f"[DEBUG] Response JSON: {json_data}")  # EKLENDİ
            return json_data
        except requests.exceptions.HTTPError as e:
            print(f"[!] HTTP error: {e} | Status: {response.status_code} | Response: {response.text}")
        except ValueError:
            print("[!] Response is not valid JSON.")
        return None


    def get(self, endpoint="", params=None, headers=None):
        try:
            response = requests.get(
                f"{self.base_url}/{endpoint.lstrip('/')}",
                headers={**self.headers, **(headers or {})},
                params=params,
                timeout=self.timeout
            )
            return self._handle_response(response)
        except Timeout:
            print("[!] GET request timed out.")
        except RequestException as e:
            print(f"[!] GET request failed: {e}")
        return None

    def post(self, endpoint="", data=None, json=None, headers=None):
        try:
            response = requests.post(
                f"{self.base_url}/{endpoint.lstrip('/')}",
                headers={**self.headers, **(headers or {})},
                data=data,
                json=json,
                timeout=self.timeout
            )
            return self._handle_response(response)
        except Timeout:
            print("[!] POST request timed out.")
        except RequestException as e:
            print(f"[!] POST request failed: {e}")
        return None

    def put(self, endpoint="", data=None, json=None, headers=None):
        try:
            response = requests.put(
                f"{self.base_url}/{endpoint.lstrip('/')}",
                headers={**self.headers, **(headers or {})},
                data=data,
                json=json,
                timeout=self.timeout
            )
            return self._handle_response(response)
        except Timeout:
            print("[!] PUT request timed out.")
        except RequestException as e:
            print(f"[!] PUT request failed: {e}")
        return None

    def delete(self, endpoint="", headers=None):
        try:
            response = requests.delete(
                f"{self.base_url}/{endpoint.lstrip('/')}",
                headers={**self.headers, **(headers or {})},
                timeout=self.timeout
            )
            return self._handle_response(response)
        except Timeout:
            print("[!] DELETE request timed out.")
        except RequestException as e:
            print(f"[!] DELETE request failed: {e}")
        return None

class Esimgo:
    """eSIM Go API Service - Tüm bundles/countries endpoint'leri ile"""
    
    def __init__(self):
        self.service = BaseService(
            base_url="https://api.esim-go.com/v2.4",
            headers={"X-API-Key": "NuzAFxpBhLUHQ7HNaN4sF63NlfYSs7IRxc-CszQp"}
        )
        self.provider_slug = "esimgo"
        self.provider_name = "eSIM Go"
        self.api_key = "NuzAFxpBhLUHQ7HNaN4sF63NlfYSs7IRxc-CszQp"

    def get_all_esim(self):
        """Tüm eSIM Go paketlerini tüm sayfalardan çeker"""
        print("[INFO] eSIM Go - Tüm bundles (tüm sayfalar) çekiliyor...")
        all_bundles = []
        page = 1
        page_size = 50  # eSIM Go API maksimumu

        while True:
            params = {"page": page, "pageSize": page_size}
            data = self.service.get(endpoint="catalogue", params=params)
            if isinstance(data, dict) and "bundles" in data:
                bundles = data["bundles"]
            elif isinstance(data, list):
                bundles = data
            else:
                print(f"[ERROR] eSIM Go - Beklenmeyen yanıt formatı: {data}")
                break

            if not bundles:
                break

            all_bundles.extend(bundles)
            print(f"[INFO] Sayfa {page} - {len(bundles)} kayıt alındı.")

            # Son sayfadaysak çık
            if len(bundles) < page_size:
                break
            page += 1

        provider = self._get_or_create_provider()
        self.sync_esim_packages(all_bundles, provider)
    def get_countries(self):
        """Desteklenen ülkelerin listesini çeker"""
        print("[INFO] eSIM Go - Desteklenen ülkeler çekiliyor...")
        data = self.service.get(endpoint="countries")
        
        if isinstance(data, list):
            return data
        else:
            print(f"[ERROR] eSIM Go - Ülkeler listesi alınamadı: {data}")
            return []

    def get_esim_by_country(self, country_code: str):
        """
        Belirli bir ülke için paketleri çeker.
        eSIM Go'da ülke bazlı filtreleme yok, tüm paketleri çekip filtreleriz.
        """
        # Tüm bundles'ı çek
        all_bundles = self.service.get(endpoint="catalogue")
        
        if isinstance(all_bundles, list):
            # Belirli ülke için filtrele
            country_bundles = self._filter_bundles_by_country(all_bundles, country_code)
            
            if country_bundles:
                provider = self._get_or_create_provider()
                self.sync_esim_packages(country_bundles, provider, target_country=country_code)
            else:
                print(f"[WARNING] eSIM Go - {country_code} için paket bulunamadı")
        else:
            print(f"[ERROR] eSIM Go - Bundles alınamadı: {all_bundles}")

    def update_country_packages(self, country_code: str):
        """Belirli bir ülkenin paketlerini günceller"""
        print(f"[INFO] eSIM Go - {country_code} ülkesi paketleri güncelleniyor...")
        
        # Önce mevcut paketleri pasif hale getir
        self._deactivate_country_packages(country_code)
        
        # Yeni paketleri çek ve güncelle
        self.get_esim_by_country(country_code)

    def update_all_packages(self):
        """Tüm paketleri günceller - bundles değişikliklerini takip eder"""
        print("[INFO] eSIM Go - Tüm paketler güncelleniyor...")
        
        # Mevcut tüm aktif paketleri pasif hale getir
        provider = self._get_or_create_provider()
        eSIMPackage.objects.filter(provider=provider, is_active=True).update(
            is_active=False, 
            updated_at=timezone.now()
        )
        
        # Tüm paketleri yeniden çek
        self.get_all_esim()

    def _get_or_create_provider(self):
        """Provider'ı oluştur veya getir"""
        provider, created = Provider.objects.get_or_create(
            slug=self.provider_slug,
            defaults={
                "name": self.provider_name,
                "api_key": self.api_key,
            }
        )
        if created:
            print(f"[INFO] Yeni provider oluşturuldu: {self.provider_name}")
        return provider

    def _filter_bundles_by_country(self, bundles: List[Dict], country_code: str) -> List[Dict]:
        """Bundles'ları belirli ülke koduna göre filtreler"""
        filtered = []
        for bundle in bundles:
            countries = bundle.get("countries", [])
            if countries and isinstance(countries[0], dict):
                country_codes = [c.get("iso") for c in countries if "iso" in c]
            else:
                country_codes = countries
            if country_code in country_codes:
                filtered.append(bundle)
        return filtered

    def _deactivate_country_packages(self, country_code: str):
        """Belirli ülke için mevcut paketleri pasif hale getirir"""
        try:
            country = Country.objects.get(code=country_code)
            provider = Provider.objects.get(slug=self.provider_slug)
            
            packages = eSIMPackage.objects.filter(
                provider=provider,
                countries=country,
                is_active=True
            )
            
            count = packages.update(is_active=False, updated_at=timezone.now())
            print(f"[INFO] {count} adet {country_code} paketi pasif hale getirildi")
            
        except Country.DoesNotExist:
            print(f"[WARNING] {country_code} ülkesi bulunamadı")
        except Provider.DoesNotExist:
            print(f"[WARNING] {self.provider_slug} provider'ı bulunamadı")

    def sync_esim_packages(self, packages: List[Dict], provider: Provider, target_country: Optional[str] = None):
        """eSIM paketlerini veritabanı ile senkronize eder"""
        created, updated = 0, 0

        for pkg in packages:
            try:
                name = pkg.get("description") or pkg.get("title") or "Unnamed Package"
                price = Decimal(str(pkg.get("price") or 0))
                validity = int(pkg.get("validity_days") or pkg.get("validity") or pkg.get("duration") or 0)

                # eSIM Go için veri miktarı doğrudan integer (MB) geliyor olabilir
                data_mb = 0
                if "dataAmount" in pkg and isinstance(pkg["dataAmount"], (int, float)):
                    data_mb = int(pkg["dataAmount"]) if pkg["dataAmount"] and pkg["dataAmount"] > 0 else 0
                else:
                    # Yedek olarak eski yöntemi de dene
                    raw_data = (pkg.get("data") or pkg.get("data_amount") or pkg.get("size") or "").upper().strip()
                    data_mb = self._parse_data_amount(raw_data)
                # Negatif veya None değerleri sıfıra çek
                if not data_mb or data_mb < 0:
                    data_mb = 0

                # Benzersiz anahtar için external_id kullanımı (modelde varsa)
                external_id = pkg.get("id") or pkg.get("external_id")

                filter_kwargs = {"provider": provider}
                if external_id:
                    filter_kwargs["external_id"] = external_id
                else:
                    filter_kwargs["name__iexact"] = name.strip()

                obj, is_created = eSIMPackage.objects.update_or_create(
                    defaults={
                        "name": name,
                        "price": price,
                        "validity_days": validity,
                        "data_amount_mb": data_mb,
                        "detail": pkg,
                        "is_active": True,
                        "updated_at": timezone.now(),
                        "external_id": external_id if external_id else None,
                    },
                    **filter_kwargs
                )

                # Ülke eşleştirmeleri
                coverage = pkg.get("coverage") or []
                countries = pkg.get("countries") or []
                country_codes = pkg.get("country_codes") or []

                # Eğer countries dict listesi ise, iso kodlarını çek
                if countries and isinstance(countries[0], dict):
                    countries = [c.get("iso") for c in countries if "iso" in c]

                all_country_codes = list(set(coverage + countries + country_codes))
                if all_country_codes:
                    countries_qs = Country.objects.filter(code__in=all_country_codes)
                    obj.countries.set(countries_qs)

                if is_created:
                    created += 1
                else:
                    updated += 1

            except Exception as e:
                print(f"[ERROR] Paket işlenirken hata: {e} - Paket: {pkg}")

        print(f"[✓] {provider.name} - {created} paket oluşturuldu, {updated} paket güncellendi.")


    def _parse_data_amount(self, raw_data: str) -> int:
        """Veri miktarını MB'ye çevirir"""
        if not raw_data:
            return 0
            
        if raw_data.endswith("GB"):
            return int(float(raw_data.replace("GB", "")) * 1024)
        elif raw_data.endswith("MB"):
            return int(float(raw_data.replace("MB", "")))
        return 0
class EsimMaxi:
    """eSIM Access API Service - Country-based filtering supported"""
    
    def __init__(self):
        self.service = BaseService(
            base_url="https://api.esimaccess.com/api/v1/open",
            headers={"RT-AccessCode": "2ee5c03386c54f7696d6a1391329730e"}
        )
        self.provider_slug = "esimaccess"
        self.provider_name = "eSIM Access"
        self.api_key = "2ee5c03386c54f7696d6a1391329730e"

    def get_all_esim(self):
        """Tüm eSIM paketlerini çeker"""
        print("[INFO] eSIM Access - Tüm paketler çekiliyor...")
        data = self.service.post(endpoint="package/list", json={})
        provider = self._get_or_create_provider()
        self.sync_esim_packages(data["obj"]["packageList"], provider)


    def get_esim_by_country(self, country_code: str):
        """Belirli bir ülke için eSIM paketlerini çeker"""
        print(f"[INFO] eSIM Access - {country_code} ülkesi için paketler çekiliyor...")
        payload = {"locationCode": country_code}
        data = self.service.post(endpoint="package/list", json=payload)
        print(f"[DEBUG] API response for country {country_code}: {data}")

        provider = self._get_or_create_provider()
        # Ülke kodunu paketlere ekle ki sadece bu ülke için güncelleme yapılsın
        filtered_packages = self._filter_packages_by_country(data["data"], country_code)
        self.sync_esim_packages(filtered_packages, provider, target_country=country_code)

    def update_country_packages(self, country_code: str):
        """Belirli bir ülkenin paketlerini günceller"""
        print(f"[INFO] eSIM Access - {country_code} ülkesi paketleri güncelleniyor...")
        
        # Önce mevcut paketleri pasif hale getir
        self._deactivate_country_packages(country_code)
        
        # Yeni verileri çek ve güncelle
        self.get_esim_by_country(country_code)

    def _get_or_create_provider(self):
        """Provider'ı oluştur veya getir"""
        provider, created = Provider.objects.get_or_create(
            slug=self.provider_slug,
            defaults={
                "name": self.provider_name,
                "api_key": self.api_key,
            }
        )
        if created:
            print(f"[INFO] Yeni provider oluşturuldu: {self.provider_name}")
        return provider

    def _filter_packages_by_country(self, packages: List[Dict], country_code: str) -> List[Dict]:
        """Paketleri belirli ülke koduna göre filtreler"""
        filtered = []
        for pkg in packages:
            country_codes = pkg.get("locationNetworkList", ["locationName"])
            if country_code in country_codes:
                filtered.append(pkg)
        return filtered

    def _deactivate_country_packages(self, country_code: str):
        """Belirli ülke için mevcut paketleri pasif hale getirir"""
        try:
            country = Country.objects.get(code=country_code)
            provider = Provider.objects.get(slug=self.provider_slug)
            
            packages = eSIMPackage.objects.filter(
                provider=provider,
                countries=country,
                is_active=True
            )
            
            packages.update(is_active=False, updated_at=timezone.now())
            print(f"[INFO] {packages.count()} adet {country_code} paketi pasif hale getirildi")
            
        except Country.DoesNotExist:
            print(f"[WARNING] {country_code} ülkesi bulunamadı")
        except Provider.DoesNotExist:
            print(f"[WARNING] {self.provider_slug} provider'ı bulunamadı")

    def sync_esim_packages(self, packages: List[Dict], provider: Provider, target_country: Optional[str] = None):
        """eSIM paketlerini veritabanı ile senkronize eder"""
        created, updated = 0, 0
        
        for pkg in packages:
            try:
                name = pkg.get("name", "Unnamed Package")
                price = Decimal(str(pkg.get("price", 0)))
                validity = int(pkg.get("duration", 0))
                raw_data = pkg.get("data", "").upper().strip()
                
                # Veri miktarını MB'ye çevir
                data_mb = 0
                
                if "volume" in pkg and isinstance(pkg["volume"], (int, float)) and pkg["volume"] > 0:
                    data_mb = int(pkg["volume"] / (1024 * 1024))  # Byte'tan MB'ye çevir
                    print(f"[DEBUG] Volume'den veri: {pkg['volume']} bytes = {data_mb} MB")
                else:
                    raw_data = pkg.get("data", "").upper().strip()
                    data_mb = self._parse_data_amount(raw_data)

                # Paket oluştur veya güncelle
                obj, is_created = eSIMPackage.objects.update_or_create(
                    name=name,
                    provider=provider,
                    defaults={
                        "price": price,
                        "validity_days": validity,
                        "data_amount_mb": data_mb,
                        "detail": pkg,
                        "is_active": True,
                        "updated_at": timezone.now(),
                    }
                )

                # Ülke ilişkilerini ayarla
                country_codes = pkg.get("country_codes", [])
                if country_codes:
                    countries = Country.objects.filter(code__in=country_codes)
                    obj.countries.set(countries)

                if is_created:
                    created += 1
                else:
                    updated += 1
                    
            except Exception as e:
                print(f"[ERROR] Paket işlenirken hata: {e} - Paket: {pkg}")

        print(f"[✓] eSIM Access - {created} paket oluşturuldu, {updated} paket güncellendi.")

    



class eSIMService:
    """Ana eSIM servisi - tüm provider'ları yönetir"""
    
    def __init__(self):
        self.esim_access = EsimMaxi()
        self.esim_go = Esimgo()
    
    def sync_all_providers(self):
        """Tüm provider'lardan paketleri çeker"""
        print("[INFO] Tüm provider'lar senkronize ediliyor...")
        
        # eSIM Access - tüm paketleri çek
        self.esim_access.get_all_esim()
        
        # eSIM Go - tüm paketleri çek
        self.esim_go.get_all_esim()
        
        print("[✓] Tüm provider'lar senkronize edildi")
    
    def sync_country_packages(self, country_code: str):
        """Belirli bir ülke için tüm provider'lardan paketleri çeker"""
        print(f"[INFO] {country_code} ülkesi için tüm provider'lar senkronize ediliyor...")
        
        # eSIM Access - ülke bazlı çekme
        self.esim_access.get_esim_by_country(country_code)
        
        # eSIM Go - ülke bazlı filtreleme
        self.esim_go.get_esim_by_country(country_code)
        
        print(f"[✓] {country_code} ülkesi için tüm provider'lar senkronize edildi")
    
    def update_country_packages(self, country_code: str):
        """Belirli bir ülke için paketleri günceller"""
        print(f"[INFO] {country_code} ülkesi paketleri güncelleniyor...")
        
        # Her iki provider için de güncelleme yap
        self.esim_access.update_country_packages(country_code)
        self.esim_go.update_country_packages(country_code)
        
        print(f"[✓] {country_code} ülkesi paketleri güncellendi")
    
    def get_supported_countries(self):
        """Her iki provider'ın desteklediği ülkeleri listeler"""
        print("[INFO] Desteklenen ülkeler çekiliyor...")
        
        # eSIM Go'dan ülke listesini çek
        esim_go_countries = self.esim_go.get_countries()
        
        # Veritabanındaki ülkeler
        db_countries = list(Country.objects.values_list('code', flat=True))
        
        return {
            'esim_go_countries': esim_go_countries,
            'database_countries': db_countries
        }