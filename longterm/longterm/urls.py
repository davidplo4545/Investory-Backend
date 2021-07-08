from .scraper import USPapersScraper, IsraeliPaperScraper, Updater
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth.models import User
from rest_framework import serializers, viewsets, routers
from api import views


# Routers provide a way of automatically determining the URL conf.
router = routers.DefaultRouter()
router.register(r'users', views.UserViewSet, basename='Username')
router.register(r'assets', views.AssetViewSet, basename='Asset')
router.register(r'portfolios', views.PortfolioViewSet, basename='Portfolio')
router.register(r'portfolio-comparisons',
                views.PortfolioComparisonViewSet, basename='Comparisons')

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns = [
    path("admin/", admin.site.urls),
    path('api/', include(router.urls)),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('api/', include('rest_auth.urls')),  # login / logout / user
    path('api/register/', include('rest_auth.registration.urls')),
]


is_scrape = False
is_updater = False
if is_updater:
    u = Updater()
    u.update_all_portfolios()
    print('Finished updating portfolios')

# Scrapers
if is_scrape:
    us_scraper = USPapersScraper()
    # scrape us stocks
    print('Scraping us stocks')
    us_scraper.scrape_to_database()

    isr_scraper = IsraeliPaperScraper()

    print('Scraping israeli stocks')
    # scrape israeli stocks
    isr_scraper.scrape_to_database()

    print('Scraping cryptos')
    # scrape crypto
    us_scraper.scrape_cryptos_to_database()
