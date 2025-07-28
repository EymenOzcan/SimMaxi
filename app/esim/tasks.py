# app/esim/tasks.py
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
import logging

from .services import eSIMService, EsimMaxi, Esimgo
from .models import eSIMPackage, Country, Provider

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def sync_all_esim_packages(self):
    print("TASK WORKING!")
    """Tüm eSIM paketlerini senkronize eder"""
    try:
        logger.info("Tüm eSIM paketleri senkronizasyonu başlatıldı")
        service = eSIMService()
        service.sync_all_providers()
        logger.info("Tüm eSIM paketleri başarıyla senkronize edildi")
        return {"status": "success", "message": "Tüm paketler senkronize edildi"}
    except Exception as exc:
        logger.error(f"eSIM paket senkronizasyonu hatası: {exc}")
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (self.request.retries + 1))
        return {"status": "error", "message": str(exc)}


@shared_task(bind=True, max_retries=3)
def sync_country_esim_packages(self, country_code):
    """Belirli bir ülke için eSIM paketlerini senkronize eder"""
    try:
        logger.info(f"{country_code} için eSIM paket senkronizasyonu başlatıldı")
        service = eSIMService()
        service.sync_country_packages(country_code)
        logger.info(f"{country_code} ülkesi eSIM paketleri başarıyla senkronize edildi")
        return {
            "status": "success",
            "message": f"{country_code} paketleri senkronize edildi",
        }
    except Exception as exc:
        logger.error(f"{country_code} eSIM paket senkronizasyonu hatası: {exc}")
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (self.request.retries + 1))
        return {"status": "error", "message": str(exc)}

@shared_task(bind=True, max_retries=3)
def update_country_esim_packages(self, country_code):
    """Belirli bir ülke için eSIM paketlerini günceller"""
    try:
        logger.info(f"{country_code} ülkesi eSIM paketleri güncellemesi başlatıldı")
        service = eSIMService()
        service.update_country_packages(country_code)
        logger.info(f"{country_code} ülkesi eSIM paketleri başarıyla güncellendi")
        return {"status": "success", "message": f"{country_code} paketleri güncellendi"}
    except Exception as exc:
        logger.error(f"{country_code} eSIM paket güncellemesi hatası: {exc}")
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (self.request.retries + 1))
        return {"status": "error", "message": str(exc)}


@shared_task
def sync_esimaccess_packages():
    """Sadece eSIM Access paketlerini senkronize eder"""
    try:
        logger.info("eSIM Access paketleri senkronizasyonu başlatıldı")
        esim_access = EsimMaxi()
        esim_access.get_all_esim()
        logger.info("eSIM Access paketleri başarıyla senkronize edildi")
        
        return {
            "status": "success",
            "message": "eSIM Access paketleri senkronize edildi",
        }
    except Exception as exc:
        logger.error(f"eSIM Access senkronizasyon hatası: {exc}")
        return {"status": "error", "message": str(exc)}


@shared_task
def sync_esimgo_packages():
    """Sadece eSIM Go paketlerini senkronize eder"""
   
    try:
        logger.info("eSIM Go paketleri senkronizasyonu başlatıldı")
        esim_go = Esimgo()
        esim_go.get_all_esim()
        logger.info("eSIM Go paketleri başarıyla senkronize edildi")
       
        return {"status": "success", "message": "eSIM Go paketleri senkronize edildi"}
    except Exception as exc:
        logger.error(f"eSIM Go senkronizasyon hatası: {exc}")
        return {"status": "error", "message": str(exc)}


@shared_task
def update_esimgo_packages():
    """eSIM Go paketlerini günceller (önce pasif hale getirir)"""
    try:
        logger.info("eSIM Go paketleri güncellemesi başlatıldı")
        esim_go = Esimgo()
        esim_go.update_all_packages()
        logger.info("eSIM Go paketleri başarıyla güncellendi")
        return {"status": "success", "message": "eSIM Go paketleri güncellendi"}
    except Exception as exc:
        logger.error(f"eSIM Go güncelleme hatası: {exc}")
        return {"status": "error", "message": str(exc)}


@shared_task
def cleanup_old_packages(days=30):
    """Eski ve pasif paketleri temizler"""
    try:
        logger.info(f"{days} gün öncesine ait pasif paketler temizleniyor")
        cutoff_date = timezone.now() - timedelta(days=days)

        deleted_count, _ = eSIMPackage.objects.filter(
            is_active=False, updated_at__lt=cutoff_date
        ).delete()

        logger.info(f"{deleted_count} adet eski pasif paket silindi")
        return {"status": "success", "message": f"{deleted_count} paket silindi"}
    except Exception as exc:
        logger.error(f"Paket temizleme hatası: {exc}")
        return {"status": "error", "message": str(exc)}


@shared_task
def batch_sync_countries(country_codes):
    """Birden fazla ülke için toplu senkronizasyon"""
    results = []
    service = eSIMService()

    for country_code in country_codes:
        try:
            logger.info(f"Toplu senkronizasyon: {country_code}")
            service.sync_country_packages(country_code)
            results.append({"country": country_code, "status": "success"})
        except Exception as exc:
            logger.error(f"Toplu senkronizasyon hatası {country_code}: {exc}")
            results.append(
                {"country": country_code, "status": "error", "message": str(exc)}
            )

    success_count = len([r for r in results if r["status"] == "success"])
    error_count = len([r for r in results if r["status"] == "error"])

    logger.info(
        f"Toplu senkronizasyon tamamlandı. Başarılı: {success_count}, Hatalı: {error_count}"
    )

    return {
        "status": "completed",
        "success_count": success_count,
        "error_count": error_count,
        "results": results,
    }


@shared_task
def batch_update_countries(country_codes):
    """Birden fazla ülke için toplu güncelleme"""
    results = []
    service = eSIMService()

    for country_code in country_codes:
        try:
            logger.info(f"Toplu güncelleme: {country_code}")
            service.update_country_packages(country_code)
            results.append({"country": country_code, "status": "success"})
        except Exception as exc:
            logger.error(f"Toplu güncelleme hatası {country_code}: {exc}")
            results.append(
                {"country": country_code, "status": "error", "message": str(exc)}
            )

    success_count = len([r for r in results if r["status"] == "success"])
    error_count = len([r for r in results if r["status"] == "error"])

    logger.info(
        f"Toplu güncelleme tamamlandı. Başarılı: {success_count}, Hatalı: {error_count}"
    )

    return {
        "status": "completed",
        "success_count": success_count,
        "error_count": error_count,
        "results": results,
    }


@shared_task
def validate_package_data():
    """Paket verilerini doğrular ve raporlar"""
    try:
        logger.info("Paket veri doğrulaması başlatıldı")

        issues = []
        active_packages = eSIMPackage.objects.filter(is_active=True)

        for pkg in active_packages:
            pkg_issues = []

            if pkg.price <= 0:
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
                issues.append(
                    {
                        "package_id": pkg.id,
                        "package_name": pkg.name,
                        "provider": pkg.provider.name,
                        "issues": pkg_issues,
                    }
                )

        total_active = active_packages.count()
        problematic_count = len(issues)
        success_rate = (
            ((total_active - problematic_count) / total_active * 100)
            if total_active > 0
            else 0
        )

        logger.info(
            f"Veri doğrulaması tamamlandı. {problematic_count}/{total_active} pakette sorun bulundu"
        )

        return {
            "status": "success",
            "total_active": total_active,
            "problematic_count": problematic_count,
            "success_rate": round(success_rate, 2),
            "issues": issues[:50],  # İlk 50 sorunu döndür
        }

    except Exception as exc:
        logger.error(f"Veri doğrulaması hatası: {exc}")
        return {"status": "error", "message": str(exc)}


# Periodic task'lar için schedule konfigürasyonu

# settings.py veya celery.py dosyasına eklenecek
