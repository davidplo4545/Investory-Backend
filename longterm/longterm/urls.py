from django.contrib import admin
from django.urls import path, include
from django.contrib.auth.models import User
from rest_framework import serializers, viewsets, routers

# Routers provide a way of automatically determining the URL conf.
router = routers.DefaultRouter()
# router.register(r'users', UserViewSet)


# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns = [
    # path('', include(router.urls)),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('api/', include('rest_auth.urls')),  # login / logout / user
    path('api/register/', include('rest_auth.registration.urls')),
]
