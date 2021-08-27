from django.contrib import admin
from django.urls import path, include, reverse
from django.shortcuts import redirect
from django.contrib.auth.models import User
from rest_framework import routers
from api import views
from api import social_views


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
    path('rest-auth/facebook/', social_views.FacebookLogin.as_view(),
         name='facebook_login'),
    path('rest-auth/google/', social_views.GoogleLogin.as_view(), name='google_login'),
    path('accounts/', include('allauth.urls'), name='socialaccount_signup'),
    path('api/<str:short_url>', views.ShortPortfolioDetail.as_view(), name='redirect'),
]
