from django.contrib import admin
from django.urls import path, reverse
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from django.utils.html import format_html
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from unfold.admin import ModelAdmin
from app import dealers
from app.dealers.models import Dealer, DealerRole
from app.users.models import CustomUser
from .models import OfferedPackage, eSIMPackage, Provider, Country
from django.db.models.signals import post_save
from django.dispatch import receiver
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


@receiver(post_save, sender=eSIMPackage)
def create_offered_package(sender, instance, created, **kwargs):
    if instance.is_offered:
        OfferedPackage.objects.get_or_create(
            esim=instance,
            defaults={
                "title": instance.name[:50],
                "explanation": instance.detail.get("description", "")[
                    :70
                ],  # örnek alım
                "end_user_sales": True,
                "dealer_sale": True,
                "status": True,
            },
        )


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


class ProviderFilter(admin.SimpleListFilter):
    title = "Provider"
    parameter_name = "provider"

    def lookups(self, request, model_admin):
        providers = Provider.objects.all().order_by("name")
        return [(provider.id, provider.name) for provider in providers]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(provider__id=self.value())
        return queryset


@admin.register(Provider)
class ProviderAdmin(ModelAdmin):
    list_display = (
        "name",
        "slug",
        "package_count",
        "active_package_count",
        "view_packages_button",
        "sync_provider_button",
        "is_active",
        "created_at",
    )
    list_filter = ("is_active", "created_at")
    search_fields = ("name", "slug")
    readonly_fields = ("created_at", "updated_at")
    list_editable = ("is_active",)

    def package_count(self, obj):
        count = eSIMPackage.objects.filter(provider=obj).count()
        return format_html(
            '<span style="font-weight: bold; color: #666;">{}</span>', count
        )

    package_count.short_description = "Toplam Paket"

    def active_package_count(self, obj):
        count = eSIMPackage.objects.filter(provider=obj, is_active=True).count()
        color = "#28a745" if count > 0 else "#dc3545"
        return format_html(
            '<span style="font-weight: bold; color: {};">{}</span>', color, count
        )

    active_package_count.short_description = "Aktif Paket"

    def view_packages_button(self, obj):
        url = (
            reverse("admin:esim_esimpackage_changelist")
            + f"?provider__id__exact={obj.id}"
        )
        return format_html(
            '<a class="button" href="{}" style="background: #007cba; color: white; padding: 5px 10px; text-decoration: none; border-radius: 3px;">📦 Paketleri Görüntüle</a>',
            url,
        )

    view_packages_button.short_description = "Paketler"
    view_packages_button.allow_tags = True

    def sync_provider_button(self, obj):
        return format_html(
            '<a class="button" href="{}" style="background: #28a745; color: white; padding: 5px 10px; text-decoration: none; border-radius: 3px;">🔄 Senkronize Et</a>',
            reverse("admin:esim_provider_sync", args=[obj.pk]),
        )

    sync_provider_button.short_description = "Senkronizasyon"
    sync_provider_button.allow_tags = True

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
                f"✅ {provider.name} paketleri senkronize ediliyor. Task ID: {task.id}",
            )
        elif provider.slug == "esimgo":
            from .services import Esimgo

            esim_go = Esimgo()
            esim_go.get_all_esim()
            messages.success(
                request, f"✅ {provider.name} paketleri senkronize edildi."
            )

        return redirect("admin:esim_provider_changelist")


@admin.register(Country)
class CountryAdmin(ModelAdmin):
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
        color = "#28a745" if count > 0 else "#dc3545"
        return format_html(
            '<span style="font-weight: bold; color: {};">{}</span>', color, count
        )

    package_count.short_description = "Aktif Paket Sayısı"

    def sync_country_button(self, obj):
        return format_html(
            '<a class="button" href="{}" style="background: #28a745; color: white; padding: 5px 10px; text-decoration: none; border-radius: 3px;">🔄 Senkronize Et</a>',
            reverse("admin:esim_country_sync", args=[obj.pk]),
        )

    sync_country_button.short_description = "İşlemler"
    sync_country_button.allow_tags = True

    def view_esims_button(self, obj):
        url = (
            reverse("admin:esim_esimpackage_changelist")
            + f"?countries__id__exact={obj.id}"
        )
        return format_html(
            '<a class="button" href="{}" style="background: #007cba; color: white; padding: 5px 10px; text-decoration: none; border-radius: 3px;">📱 eSIM\'leri Görüntüle</a>',
            url,
        )

    view_esims_button.short_description = "eSIM'leri Görüntüle"
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
            f"✅ {country.name} ({country.code}) paketleri senkronize ediliyor. Task ID: {task.id}",
        )
        return redirect("admin:esim_country_changelist")


@admin.register(eSIMPackage)
class eSIMPackageAdmin(ModelAdmin):
    list_display = (
        "package_info",
        "provider_info",
        "slug",
        "price_info",
        "data_info",
        "validity_info",
        "country_info",
        "status_info",
        "is_offered",
       
    )
    list_filter = (
        ProviderFilter,
        "is_active",
        "validity_days",
        PriceRangeFilter,
        DataAmountRangeFilter,
        "created_at",
        "updated_at",
    )
    search_fields = ("name", "provider__name", "countries__name", "countries__code")
    readonly_fields = ("created_at", "updated_at")
    filter_horizontal = ("countries",)
    list_per_page = 25
    list_select_related = ("provider",)

    # Toplu işlemler
    actions = [
        "bulk_activate_packages",
        "bulk_deactivate_packages",
        "bulk_delete_packages",
        "bulk_sync_selected_providers",
    ]

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("countries")

    def package_info(self, obj):
        return format_html(
            '<div style="font-weight: bold; color: #333;">{}</div>'
            '<div style="font-size: 11px; color: #666;">ID: {}</div>',
            obj.name[:50] + ("..." if len(obj.name) > 50 else ""),
            obj.id,
        )

    package_info.short_description = "Paket Bilgisi"

    def provider_info(self, obj):
        color = "#28a745" if obj.provider.is_active else "#dc3545"
        return format_html(
            '<div style="font-weight: bold; color: {};">{}</div>'
            '<div style="font-size: 11px; color: #666;">{}</div>',
            color,
            obj.provider.name,
            obj.provider.slug,
        )

    provider_info.short_description = "Provider"

    def price_info(self, obj):
        return format_html(
            '<div style="font-weight: bold; color: #e67e22; font-size: 14px;">${}</div>',
            obj.price,
        )

    price_info.short_description = "Fiyat"

    def data_info(self, obj):
        if obj.data_amount_mb == -1:
            return format_html(
                '<div style="font-weight: bold; color: #8e44ad;">♾️ Sınırsız</div>'
            )
        elif obj.data_amount_mb >= 1024:
            gb = round(obj.data_amount_mb / 1024, 1)
            return format_html(
                '<div style="font-weight: bold; color: #3498db;">{} GB</div>', gb
            )
        else:
            return format_html(
                '<div style="font-weight: bold; color: #3498db;">{} MB</div>',
                obj.data_amount_mb,
            )

    data_info.short_description = "Veri Miktarı"

    def validity_info(self, obj):
        return format_html(
            '<div style="font-weight: bold; color: #f39c12;">📅 {} gün</div>',
            obj.validity_days,
        )

    validity_info.short_description = "Geçerlilik"

    def country_info(self, obj):
        countries = list(obj.countries.all()[:3])
        country_codes = [c.code for c in countries]

        if obj.countries.count() > 3:
            display_text = (
                f"{', '.join(country_codes)} +{obj.countries.count() - 3} daha"
            )
        else:
            display_text = ", ".join(country_codes)

        return format_html(
            '<div style="font-size: 12px; color: #34495e;">🌍 {}</div>'
            '<div style="font-size: 10px; color: #7f8c8d;">Toplam: {} ülke</div>',
            display_text,
            obj.countries.count(),
        )

    country_info.short_description = "Ülkeler"

    def status_info(self, obj):
        if obj.is_active:
            return format_html(
                '<div style="background: #d4edda; color: #155724; padding: 3px 8px; border-radius: 12px; font-size: 11px; font-weight: bold; text-align: center;">✅ AKTİF</div>'
            )
        else:
            return format_html(
                '<div style="background: #f8d7da; color: #721c24; padding: 3px 8px; border-radius: 12px; font-size: 11px; font-weight: bold; text-align: center;">❌ PASİF</div>'
            )

    status_info.short_description = "Durum"

    # Toplu işlem fonksiyonları
    def bulk_activate_packages(self, request, queryset):
        count = queryset.update(is_active=True, updated_at=timezone.now())
        self.message_user(
            request, f"✅ {count} paket aktif hale getirildi.", level=messages.SUCCESS
        )

    bulk_activate_packages.short_description = "🟢 Seçili paketleri aktif hale getir"

    def bulk_deactivate_packages(self, request, queryset):
        count = queryset.update(is_active=False, updated_at=timezone.now())
        self.message_user(
            request, f"⚠️ {count} paket pasif hale getirildi.", level=messages.WARNING
        )

    bulk_deactivate_packages.short_description = "🔴 Seçili paketleri pasif hale getir"

    def bulk_delete_packages(self, request, queryset):
        count = queryset.count()
        queryset.delete()
        self.message_user(request, f"🗑️ {count} paket silindi.", level=messages.ERROR)

    bulk_delete_packages.short_description = "🗑️ Seçili paketleri sil"

    def bulk_sync_selected_providers(self, request, queryset):
        providers = set(queryset.values_list("provider__slug", flat=True))
        for provider_slug in providers:
            if provider_slug == "esimaccess":
                task = sync_all_esim_packages.delay()
                messages.success(
                    request,
                    f"🔄 {provider_slug} senkronizasyonu başlatıldı. Task ID: {task.id}",
                )
            elif provider_slug == "esimgo":
                from .services import Esimgo

                esim_go = Esimgo()
                esim_go.get_all_esim()
                messages.success(request, f"🔄 {provider_slug} senkronize edildi.")

    bulk_sync_selected_providers.short_description = (
        "🔄 Seçili paketlerin provider'larını senkronize et"
    )

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
            path(
                "provider-catalog/",
                self.admin_site.admin_view(self.provider_catalog_view),
                name="esim_package_provider_catalog",
            ),
        ]
        return custom_urls + urls

    def provider_catalog_view(self, request):
        """Provider'lara göre paket kataloğu görünümü"""
        providers_data = []

        for provider in Provider.objects.all():
            packages = eSIMPackage.objects.filter(provider=provider)
            active_packages = packages.filter(is_active=True)

            providers_data.append(
                {
                    "provider": provider,
                    "total_packages": packages.count(),
                    "active_packages": active_packages.count(),
                    "inactive_packages": packages.filter(is_active=False).count(),
                    "packages": active_packages[:10],  # İlk 10 aktif paket
                }
            )

        return render(
            request,
            "admin/esim/provider_catalog.html",
            {
                "title": "Provider Kataloğu",
                "providers_data": providers_data,
            },
        )

    def sync_all_view(self, request):
        if request.method == "POST":
            task = sync_all_esim_packages.delay()
            messages.success(
                request, f"🔄 Tüm paket senkronizasyonu başlatıldı. Task ID: {task.id}"
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
                    f"🔄 {country_code} ülkesi {action} başlatıldı. Task ID: {task.id}",
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
                    f"🧹 {days} gün önceki paketler temizleniyor. Task ID: {task.id}",
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
                request, f"✅ Veri doğrulaması başlatıldı. Task ID: {task.id}"
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


@admin.register(CustomUser)
class CustomUserAdmin(ModelAdmin):
    list_display = ("username", "email", "balance", "currency", "is_staff")
    list_filter = ("currency",)
    search_fields = ("username", "email")


class DealerRoleInline(admin.TabularInline):
    model = DealerRole
    extra = 0
    autocomplete_fields = ["user"]
    fields = ("user", "role")


@admin.register(Dealer)
class DealerAdmin(ModelAdmin):
    list_display = (
        "dealer_name",
        "commission_rate",
        "is_active",
        "dealer_balance",
        "secure_id",
        "view_button",
        "edit_button",
    )
    inlines = [DealerRoleInline]
    search_fields = ("dealer_name",)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "<int:dealer_id>/view/",
                self.admin_site.admin_view(self.readonly_view),
                name="dealers_dealer_readonly",
            )
        ]
        return custom_urls + urls

    def readonly_view(self, request, dealer_id):
        dealer = get_object_or_404(Dealer, id=dealer_id)
        context = dict(
            self.admin_site.each_context(request),
            title=f"{dealer.dealer_name} - Görüntüle",
            dealer=dealer,
        )
        return render(request, "admin/dealers/dealer/readonly.html", context)

    def view_button(self, obj):
        url = reverse("admin:dealers_dealer_readonly", args=[obj.pk])
        return format_html(
            '<a class="button" href="{}" style="background:#007bff;color:white;padding:5px 10px;border-radius:4px;text-decoration:none;">👁 Görüntüle</a>',
            url,
        )

    view_button.short_description = "Görüntüle"

    def edit_button(self, obj):
        url = reverse("admin:dealers_dealer_change", args=[obj.pk])
        return format_html(
            '<a class="button" href="{}" style="background:#ffc107;color:black;padding:5px 10px;border-radius:4px;text-decoration:none;">✏️ Düzenle</a>',
            url,
        )

    edit_button.short_description = "Düzenle"


@admin.register(OfferedPackage)
class OfferedPackageAdmin(ModelAdmin):
    list_display = ("title", "esim", "sale_price", "status")
    readonly_fields = ("sale_price",)
    list_filter = ("end_user_sales", "dealer_sale", "status")
    search_fields = ("title", "explanation", "esim__name")


admin.site.site_header = "eSIM Yönetim Paneli"
admin.site.site_title = "eSIM Admin"
admin.site.index_title = "Simmaxi Yönetim Paneli"
