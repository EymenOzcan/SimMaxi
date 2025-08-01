from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .views import CountryPackageViewSet, EsimPackageViewSet

router = DefaultRouter()
router.register(r"packages", EsimPackageViewSet, basename="packages")
router.register(r"country", CountryPackageViewSet, basename="country")

urlpatterns = [
    path("api/", include(router.urls)),
    path("api/sync/all/", views.sync_all_packages, name="sync_all_packages"),
    path(
        "api/sync/country/", views.sync_country_packages, name="sync_country_packages"
    ),
    path(
        "api/update/country/",
        views.update_country_packages,
        name="update_country_packages",
    ),
    path(
        "api/sync/batch/", views.batch_sync_countries_view, name="batch_sync_countries"
    ),
    path(
        "api/update/batch/",
        views.batch_update_countries_view,
        name="batch_update_countries",
    ),
    path("api/cleanup/", views.cleanup_old_packages_view, name="cleanup_old_packages"),
    path(
        "api/validate/", views.validate_package_data_view, name="validate_package_data"
    ),
    path("api/stats/", views.get_package_stats, name="get_package_stats"),
    path(
        "api/countries/", views.get_supported_countries, name="get_supported_countries"
    ),
    path("api/search/", views.search_packages, name="search_packages"),
    path("api/sync/", views.eSIMSyncView.as_view(), name="esim_sync"),
]
