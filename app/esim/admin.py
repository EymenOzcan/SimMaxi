from django.contrib import admin
from django.http import HttpResponseRedirect
from django.urls import path, reverse
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils.html import format_html
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from unfold.admin import ModelAdmin
from .models import eSIMPackage, Provider, Country
from .tasks import (
    sync_all_esim_packages,
    sync_country_esim_packages,
    update_country_esim_packages,
    cleanup_old_packages,
    validate_package_data,
)


class PriceRangeFilter(admin.SimpleListFilter):
    title = "Fiyat Aralığı"
    parameter_name = "price_range"

    def lookups(self, request, model_admin):
        return (
            ("0-10", "0-10 USD"),
            ("10-25", "10-25 USD"),
            ("25-50", "25-50 USD"),
            ("50-100", "50-100 USD"),
            ("100+", "100+ USD"),
        )

    def queryset(self, request, queryset):
        if self.value() == "0-10":
            return queryset.filter(price__gte=0, price__lte=10)
        elif self.value() == "10-25":
            return queryset.filter(price__gte=10, price__lte=25)
        elif self.value() == "25-50":
            return queryset.filter(price__gte=25, price__lte=50)
        elif self.value() == "50-100":
            return queryset.filter(price__gte=50, price__lte=100)
        elif self.value() == "100+":
            return queryset.filter(price__gte=100)


class DataAmountRangeFilter(admin.SimpleListFilter):
    title = "Veri Miktarı"
    parameter_name = "data_range"

    def lookups(self, request, model_admin):
        return (
            ("0-1gb", "0-1 GB"),
            ("1-5gb", "1-5 GB"),
            ("5-10gb", "5-10 GB"),
            ("10-20gb", "10-20 GB"),
            ("20gb+", "20+ GB"),
            ("unlimited", "Sınırsız"),
        )

    def queryset(self, request, queryset):
        if self.value() == "0-1gb":
            return queryset.filter(data_amount_mb__gte=0, data_amount_mb__lte=1024)
        elif self.value() == "1-5gb":
            return queryset.filter(data_amount_mb__gte=1024, data_amount_mb__lte=5120)
        elif self.value() == "5-10gb":
            return queryset.filter(data_amount_mb__gte=5120, data_amount_mb__lte=10240)
        elif self.value() == "10-20gb":
            return queryset.filter(data_amount_mb__gte=10240, data_amount_mb__lte=20480)
        elif self.value() == "20gb+":
            return queryset.filter(data_amount_mb__gte=20480)
        elif self.value() == "unlimited":
            return queryset.filter(data_amount_mb=-1)


@admin.register(Provider)
class ProviderAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "slug",
        "package_count",
        "active_package_count",
        "created_at",
    )
    list_filter = ("created_at",)
    search_fields = ("name", "slug")
    readonly_fields = ("created_at", "updated_at")

    def package_count(self, obj):
        return eSIMPackage.objects.filter(provider=obj).count()

    package_count.short_description = "Toplam Paket"

    def active_package_count(self, obj):
        return eSIMPackage.objects.filter(provider=obj, is_active=True).count()

    active_package_count.short_description = "Aktif Paket"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "<int:provider_id>/sync/",
                self.admin_site.admin_view(self.sync_provider_packages),
                name="esim_provider_sync",
            ),
        ]
        return custom_urls + urls

    def sync_provider_packages(self, request, provider_id):
        provider = Provider.objects.get(id=provider_id)

        if provider.slug == "esimaccess":
            task = sync_all_esim_packages.delay()
            messages.success(
                request,
                f"{provider.name} paketleri senkronize ediliyor. Task ID: {task.id}",
            )
        elif provider.slug == "esimgo":
            from .services import Esimgo

            esim_go = Esimgo()
            esim_go.get_all_esim()
            messages.success(request, f"{provider.name} paketleri senkronize edildi.")

        return redirect("admin:esim_provider_changelist")


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "code",
        "package_count",
        "view_esims_button",
        "sync_country_button",
    )
    list_filter = ("code",)
    search_fields = ("name", "code")
    ordering = ("name",)

    def package_count(self, obj):
        count = eSIMPackage.objects.filter(countries=obj, is_active=True).count()
        return count

    package_count.short_description = "Aktif Paket Sayısı"

    def sync_country_button(self, obj):
        return format_html(
            '<a class="button" href="{}">Senkronize Et</a>',
            reverse("admin:esim_country_sync", args=[obj.pk]),
        )

    sync_country_button.short_description = "İşlemler"
    sync_country_button.allow_tags = True

    def view_esims_button(self, obj):
        url = (
            reverse("admin:esim_esimpackage_changelist")
            + f"?countries__id__exact={obj.id}"
        )
        return format_html('<a class="button" href="{}">eSIM’leri Görüntüle</a>', url)

    view_esims_button.short_description = "eSIM’leri Görüntüle"
    view_esims_button.allow_tags = True

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "<int:country_id>/sync/",
                self.admin_site.admin_view(self.sync_country_packages),
                name="esim_country_sync",
            ),
        ]
        return custom_urls + urls

    def sync_country_packages(self, request, country_id):
        country = Country.objects.get(id=country_id)
        task = sync_country_esim_packages.delay(country.code)
        messages.success(
            request,
            f"{country.name} ({country.code}) paketleri senkronize ediliyor. Task ID: {task.id}",
        )
        return redirect("admin:esim_country_changelist")


@admin.register(eSIMPackage)
class eSIMPackageAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "provider",
        "price",
        "data_amount_gb",
        "validity_days",
        "country_list",
        "is_active",
        "updated_at",
    )
    list_filter = (
        "provider",
        "is_active",
        "validity_days",
        PriceRangeFilter,
        DataAmountRangeFilter,
        "created_at",
        "updated_at",
    )
    search_fields = ("name", "provider__name")
    readonly_fields = ("created_at", "updated_at")
    filter_horizontal = ("countries",)
    actions = ["activate_packages", "deactivate_packages", "delete_selected_packages"]

    def data_amount_gb(self, obj):
        if obj.data_amount_mb == -1:
            return "Sınırsız"
        return f"{obj.data_amount_mb / 1024:.2f} GB"

    data_amount_gb.short_description = "Veri Miktarı"

    def country_list(self, obj):
        countries = obj.countries.all()[:3]
        country_names = [c.code for c in countries]
        if obj.countries.count() > 3:
            country_names.append(f"+{obj.countries.count() - 3} daha")
        return ", ".join(country_names)

    country_list.short_description = "Ülkeler"

    def activate_packages(self, request, queryset):
        count = queryset.update(is_active=True, updated_at=timezone.now())
        self.message_user(request, f"{count} paket aktif hale getirildi.")

    activate_packages.short_description = "Seçili paketleri aktif hale getir"

    def deactivate_packages(self, request, queryset):
        count = queryset.update(is_active=False, updated_at=timezone.now())
        self.message_user(request, f"{count} paket pasif hale getirildi.")

    deactivate_packages.short_description = "Seçili paketleri pasif hale getir"

    def delete_selected_packages(self, request, queryset):
        count = queryset.count()
        queryset.delete()
        self.message_user(request, f"{count} paket silindi.")

    delete_selected_packages.short_description = "Seçili paketleri sil"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "sync-all/",
                self.admin_site.admin_view(self.sync_all_view),
                name="esim_package_sync_all",
            ),
            path(
                "sync-country/",
                self.admin_site.admin_view(self.sync_country_view),
                name="esim_package_sync_country",
            ),
            path(
                "cleanup/",
                self.admin_site.admin_view(self.cleanup_view),
                name="esim_package_cleanup",
            ),
            path(
                "validate/",
                self.admin_site.admin_view(self.validate_view),
                name="esim_package_validate",
            ),
            path(
                "stats/",
                self.admin_site.admin_view(self.stats_view),
                name="esim_package_stats",
            ),
        ]
        return custom_urls + urls

    def sync_all_view(self, request):
        if request.method == "POST":
            task = sync_all_esim_packages.delay()
            messages.success(
                request, f"Tüm paket senkronizasyonu başlatıldı. Task ID: {task.id}"
            )
            return redirect("admin:esim_esimpackage_changelist")

        return render(
            request,
            "admin/esim/sync_all.html",
            {
                "title": "Tüm Paketleri Senkronize Et",
                "subtitle": "Bu işlem tüm provider'lardan paketleri çeker ve veritabanını günceller.",
            },
        )

    def sync_country_view(self, request):
        if request.method == "POST":
            country_code = request.POST.get("country_code")
            update_mode = request.POST.get("update_mode") == "on"

            if country_code:
                if update_mode:
                    task = update_country_esim_packages.delay(country_code)
                    action = "güncellemesi"
                else:
                    task = sync_country_esim_packages.delay(country_code)
                    action = "senkronizasyonu"

                messages.success(
                    request,
                    f"{country_code} ülkesi {action} başlatıldı. Task ID: {task.id}",
                )
                return redirect("admin:esim_esimpackage_changelist")

        countries = Country.objects.all().order_by("name")
        return render(
            request,
            "admin/esim/sync_country.html",
            {
                "title": "Ülke Bazlı Senkronizasyon",
                "countries": countries,
            },
        )

    def cleanup_view(self, request):
        if request.method == "POST":
            days = int(request.POST.get("days", 30))
            confirm = request.POST.get("confirm") == "on"

            if confirm:
                task = cleanup_old_packages.delay(days)
                messages.success(
                    request,
                    f"{days} gün önceki paketler temizleniyor. Task ID: {task.id}",
                )
                return redirect("admin:esim_esimpackage_changelist")

        cutoff_date = timezone.now() - timedelta(days=30)
        packages_to_delete = eSIMPackage.objects.filter(
            is_active=False, updated_at__lt=cutoff_date
        ).count()

        return render(
            request,
            "admin/esim/cleanup.html",
            {
                "title": "Paket Temizleme",
                "packages_to_delete": packages_to_delete,
            },
        )

    def validate_view(self, request):
        if request.method == "POST":
            task = validate_package_data.delay()
            messages.success(
                request, f"Veri doğrulaması başlatıldı. Task ID: {task.id}"
            )
            return redirect("admin:esim_esimpackage_changelist")

        return render(
            request,
            "admin/esim/validate.html",
            {
                "title": "Paket Veri Doğrulaması",
                "subtitle": "Bu işlem tüm aktif paketlerin verilerini kontrol eder.",
            },
        )

    def stats_view(self, request):
        total_packages = eSIMPackage.objects.count()
        active_packages = eSIMPackage.objects.filter(is_active=True).count()

        provider_stats = []
        for provider in Provider.objects.all():
            total = eSIMPackage.objects.filter(provider=provider).count()
            active = eSIMPackage.objects.filter(
                provider=provider, is_active=True
            ).count()
            provider_stats.append(
                {
                    "provider": provider,
                    "total": total,
                    "active": active,
                    "inactive": total - active,
                }
            )

        country_stats = []
        countries_with_packages = (
            Country.objects.annotate(
                package_count=Count(
                    "esimpackage", filter=Q(esimpackage__is_active=True)
                )
            )
            .filter(package_count__gt=0)
            .order_by("-package_count")[:10]
        )

        return render(
            request,
            "admin/esim/stats.html",
            {
                "title": "eSIM Paket İstatistikleri",
                "total_packages": total_packages,
                "active_packages": active_packages,
                "inactive_packages": total_packages - active_packages,
                "provider_stats": provider_stats,
                "country_stats": countries_with_packages,
            },
        )


admin.site.site_header = "eSIM Yönetim Paneli"
admin.site.site_title = "eSIM Admin"
admin.site.index_title = "eSIM Paket Yönetimi"
