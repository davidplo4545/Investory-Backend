from django.contrib import admin
from django.urls import path, include
from django.contrib.auth.models import User
from rest_framework import serializers, viewsets, routers
from api import views


# Routers provide a way of automatically determining the URL conf.
router = routers.DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'assets', views.AssetViewSet, basename='Asset')
router.register(r'portfolios', views.PortfolioViewSet, basename='Portfolio')

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns = [
    path("admin/", admin.site.urls),
    path('api/', include(router.urls)),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('api/', include('rest_auth.urls')),  # login / logout / user
    path('api/register/', include('rest_auth.registration.urls')),
    path('script/isr', views.run_script_isr),
    path('script/us', views.run_script_us),
    path('script/crypto', views.run_script_crypto),
]
