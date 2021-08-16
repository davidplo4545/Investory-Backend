from .scraper import USPapersScraper, IsraeliPaperScraper, Updater
from django.contrib import admin
from django.urls import path, include, reverse
from django.shortcuts import redirect
from django.contrib.auth.models import User
from rest_framework import routers
import urllib.parse
from api import views
from api import social_views


# class GitHubLogin(SocialLoginView):
#     adapter_class = github_views.GitHubOAuth2Adapter
#     client_class = OAuth2Client

#     @property
#     def callback_url(self):
#         # use the same callback url as defined in your GitHub app, this url must
#         # be absolute:
#         return self.request.build_absolute_uri(reverse('github_callback'))


# def github_callback(request):
#     params = urllib.parse.urlencode(request.GET)
#     return redirect(f'http://localhost:3000/auth/github?{params}')
#     # return redirect(f'https://frontend/auth/github?{params}')


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
    # path('res/github/callback/', github_callback, name='github_callback'),
    # path('auth/github/url/', github_views.oauth2_login),
]


is_scrape = False
is_updater = False


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

if is_updater:
    u = Updater()
    u.update_all_portfolios()
    print('Finished updating portfolios')
