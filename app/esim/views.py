from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
import json
from rest_framework import viewsets, permissions

from app.esim.serializers import CountryEsimSerializer, eSIMPackageSerializer

from .services import eSIMService, EsimMaxi, Esimgo
from .models import  eSIMPackage, Country, Provider
from .tasks import (
    sync_all_esim_packages,
    sync_country_esim_packages,
    update_country_esim_packages,
    batch_sync_countries,
    batch_update_countries,
    cleanup_old_packages,
    validate_package_data,
)


@api_view(["POST"])

def sync_all_packages(request):
    """Tüm eSIM paketlerini senkronize eder"""
    try:
        task = sync_all_esim_packages.delay()
        return Response(
            {
                "status": "success",
                "message": "Tüm paket senkronizasyonu başlatıldı",
                "task_id": task.id,
            },
            status=status.HTTP_202_ACCEPTED,
        )
    except Exception as e:
        return Response(
            {"status": "error", "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])

def sync_country_packages(request):
    """Belirli bir ülke için paketleri senkronize eder"""
    country_code = request.data.get("country_code")

    if not country_code:
        return Response(
            {"status": "error", "message": "country_code parametresi gerekli"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        task = sync_country_esim_packages.delay(country_code)
        return Response(
            {
                "status": "success",
                "message": f"{country_code} ülkesi senkronizasyonu başlatıldı",
                "task_id": task.id,
            },
            status=status.HTTP_202_ACCEPTED,
        )
    except Exception as e:
        return Response(
            {"status": "error", "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])

def update_country_packages(request):
    """Belirli bir ülke için paketleri günceller"""
    country_code = request.data.get("country_code")

    if not country_code:
        return Response(
            {"status": "error", "message": "country_code parametresi gerekli"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        task = update_country_esim_packages.delay(country_code)
        return Response(
            {
                "status": "success",
                "message": f"{country_code} ülkesi güncellemesi başlatıldı",
                "task_id": task.id,
            },
            status=status.HTTP_202_ACCEPTED,
        )
    except Exception as e:
        return Response(
            {"status": "error", "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])

def batch_sync_countries_view(request):
    """Birden fazla ülke için toplu senkronizasyon"""
    country_codes = request.data.get("country_codes", [])

    if not country_codes or not isinstance(country_codes, list):
        return Response(
            {"status": "error", "message": "country_codes listesi gerekli"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        task = batch_sync_countries.delay(country_codes)
        return Response(
            {
                "status": "success",
                "message": f"{len(country_codes)} ülke için toplu senkronizasyon başlatıldı",
                "task_id": task.id,
                "countries": country_codes,
            },
            status=status.HTTP_202_ACCEPTED,
        )
    except Exception as e:
        return Response(
            {"status": "error", "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])

def batch_update_countries_view(request):
    """Birden fazla ülke için toplu güncelleme"""
    country_codes = request.data.get("country_codes", [])

    if not country_codes or not isinstance(country_codes, list):
        return Response(
            {"status": "error", "message": "country_codes listesi gerekli"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        task = batch_update_countries.delay(country_codes)
        return Response(
            {
                "status": "success",
                "message": f"{len(country_codes)} ülke için toplu güncelleme başlatıldı",
                "task_id": task.id,
                "countries": country_codes,
            },
            status=status.HTTP_202_ACCEPTED,
        )
    except Exception as e:
        return Response(
            {"status": "error", "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["DELETE"])

def cleanup_old_packages_view(request):
    """Eski paketleri temizler"""
    days = request.data.get("days", 30)

    try:
        days = int(days)
        if days < 1:
            return Response(
                {
                    "status": "error",
                    "message": "days parametresi pozitif bir sayı olmalı",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        task = cleanup_old_packages.delay(days)
        return Response(
            {
                "status": "success",
                "message": f"{days} gün önceki paketler temizleniyor",
                "task_id": task.id,
            },
            status=status.HTTP_202_ACCEPTED,
        )
    except ValueError:
        return Response(
            {"status": "error", "message": "days parametresi geçerli bir sayı olmalı"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    except Exception as e:
        return Response(
            {"status": "error", "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])

def validate_package_data_view(request):
    """Paket verilerini doğrular"""
    try:
        task = validate_package_data.delay()
        return Response(
            {
                "status": "success",
                "message": "Veri doğrulaması başlatıldı",
                "task_id": task.id,
            },
            status=status.HTTP_202_ACCEPTED,
        )
    except Exception as e:
        return Response(
            {"status": "error", "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
def get_package_stats(request):
    """eSIM paket istatistiklerini döndürür"""
    try:
        
        providers_stats = []
        for provider in Provider.objects.all():
            total_packages = eSIMPackage.objects.filter(provider=provider).count()
            active_packages = eSIMPackage.objects.filter(
                provider=provider, is_active=True
            ).count()

            providers_stats.append(
                {
                    "name": provider.name,
                    "slug": provider.slug,
                    "total_packages": total_packages,
                    "active_packages": active_packages,
                    "inactive_packages": total_packages - active_packages,
                }
            )

        countries_stats = []
        for country in Country.objects.all()[:10]:
            package_count = eSIMPackage.objects.filter(
                countries=country, is_active=True
            ).count()

            if package_count > 0:
                countries_stats.append(
                    {
                        "code": country.code,
                        "name": country.name,
                        "package_count": package_count,
                    }
                )

        countries_stats.sort(key=lambda x: x["package_count"], reverse=True)

        total_packages = eSIMPackage.objects.count()
        active_packages = eSIMPackage.objects.filter(is_active=True).count()

        return Response(
            {
                "status": "success",
                "data": {
                    "general": {
                        "total_packages": total_packages,
                        "active_packages": active_packages,
                        "inactive_packages": total_packages - active_packages,
                        "total_providers": Provider.objects.count(),
                        "total_countries": Country.objects.count(),
                    },
                    "providers": providers_stats,
                    "top_countries": countries_stats[:10],
                },
            }
        )
    except Exception as e:
        return Response(
            {"status": "error", "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
def get_supported_countries(request):
    """Desteklenen ülkeleri döndürür"""
    try:
        provider = request.GET.get("provider", "all")

        if provider == "all":
            countries = Country.objects.all().order_by("name")
            country_data = [{"code": c.code, "name": c.name} for c in countries]
        elif provider == "esimgo":
            service = eSIMService()
            esim_go_countries = service.esim_go.get_countries()
            country_data = [{"code": c, "name": c} for c in esim_go_countries]
        else:
            countries = (
                Country.objects.filter(
                    esimpackage__provider__slug=provider, esimpackage__is_active=True
                )
                .distinct()
                .order_by("name")
            )
            country_data = [{"code": c.code, "name": c.name} for c in countries]

        return Response(
            {
                "status": "success",
                "provider": provider,
                "countries": country_data,
                "count": len(country_data),
            }
        )
    except Exception as e:
        return Response(
            {"status": "error", "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
def search_packages(request):
    """eSIM paketlerini arar ve filtreler"""
    try:
        country_code = request.GET.get("country")
        provider_slug = request.GET.get("provider")
        min_price = request.GET.get("min_price")
        max_price = request.GET.get("max_price")
        min_data = request.GET.get("min_data") 
        max_data = request.GET.get("max_data") 
        min_validity = request.GET.get("min_validity") 
        max_validity = request.GET.get("max_validity")
        search_term = request.GET.get("search")
        page = int(request.GET.get("page", 1))
        page_size = int(request.GET.get("page_size", 20))

        queryset = eSIMPackage.objects.filter(is_active=True)

        
        if country_code:
            queryset = queryset.filter(countries__code=country_code)

        if provider_slug:
            queryset = queryset.filter(provider__slug=provider_slug)

        if min_price:
            queryset = queryset.filter(price__gte=float(min_price))

        if max_price:
            queryset = queryset.filter(price__lte=float(max_price))

        if min_data:
            queryset = queryset.filter(data_amount_mb__gte=int(min_data))

        if max_data:
            queryset = queryset.filter(data_amount_mb__lte=int(max_data))

        if min_validity:
            queryset = queryset.filter(validity_days__gte=int(min_validity))

        if max_validity:
            queryset = queryset.filter(validity_days__lte=int(max_validity))

        if search_term:
            queryset = queryset.filter(name__icontains=search_term)

       
        total_count = queryset.count()
        start = (page - 1) * page_size
        end = start + page_size
        packages = queryset[start:end]
        package_data = []
        for pkg in packages:
            countries = [{"code": c.code, "name": c.name} for c in pkg.countries.all()]

            package_data.append(
                {
                    "id": pkg.id,
                    "name": pkg.name,
                    "provider": {"name": pkg.provider.name, "slug": pkg.provider.slug},
                    "price": float(pkg.price),
                    "data_amount_mb": pkg.data_amount_mb,
                    "data_amount_gb": (
                        round(pkg.data_amount_mb / 1024, 2)
                        if pkg.data_amount_mb != -1
                        else "Unlimited"
                    ),
                    "validity_days": pkg.validity_days,
                    "countries": countries,
                    "created_at": pkg.created_at,
                    "updated_at": pkg.updated_at,
                }
            )

        return Response(
            {
                "status": "success",
                "data": {
                    "packages": package_data,
                    "pagination": {
                        "page": page,
                        "page_size": page_size,
                        "total_count": total_count,
                        "total_pages": (total_count + page_size - 1) // page_size,
                        "has_next": end < total_count,
                        "has_previous": page > 1,
                    },
                    "filters_applied": {
                        "country_code": country_code,
                        "provider_slug": provider_slug,
                        "min_price": min_price,
                        "max_price": max_price,
                        "min_data": min_data,
                        "max_data": max_data,
                        "min_validity": min_validity,
                        "max_validity": max_validity,
                        "search_term": search_term,
                    },
                },
            }
        )
    except Exception as e:
        return Response(
            {"status": "error", "message": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@method_decorator(csrf_exempt, name="dispatch")
class eSIMSyncView(View):
    """eSIM senkronizasyon için genel endpoint"""

    def post(self, request):
        try:
            data = json.loads(request.body)
            action = data.get("action")

            if action == "sync_all":
                task = sync_all_esim_packages.delay()
                return JsonResponse(
                    {
                        "status": "success",
                        "message": "Tüm paket senkronizasyonu başlatıldı",
                        "task_id": task.id,
                    }
                )

            elif action == "sync_country":
                country_code = data.get("country_code")
                if not country_code:
                    return JsonResponse(
                        {"status": "error", "message": "country_code gerekli"},
                        status=400,
                    )

                task = sync_country_esim_packages.delay(country_code)
                return JsonResponse(
                    {
                        "status": "success",
                        "message": f"{country_code} senkronizasyonu başlatıldı",
                        "task_id": task.id,
                    }
                )

            elif action == "update_country":
                country_code = data.get("country_code")
                if not country_code:
                    return JsonResponse(
                        {"status": "error", "message": "country_code gerekli"},
                        status=400,
                    )

                task = update_country_esim_packages.delay(country_code)
                return JsonResponse(
                    {
                        "status": "success",
                        "message": f"{country_code} güncellemesi başlatıldı",
                        "task_id": task.id,
                    }
                )

            else:
                return JsonResponse(
                    {"status": "error", "message": "Geçersiz action"}, status=400
                )

        except json.JSONDecodeError:
            return JsonResponse(
                {"status": "error", "message": "Geçersiz JSON"}, status=400
            )
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)


class EsimPackageViewSet(viewsets.ReadOnlyModelViewSet):
    """Databasede Bulunan Paket Verilerini Toplar"""

    queryset = eSIMPackage.objects.all()
    serializer_class = eSIMPackageSerializer
    permission_classes = [permissions.AllowAny]

class CountryPackageViewSet(viewsets.ReadOnlyModelViewSet):
    """Databasede Bulunan paketleri Ülke Bazlı Çeker"""
    queryset = Country.objects.all()
    serializer_class= CountryEsimSerializer
    permission_classes = [permissions.AllowAny]