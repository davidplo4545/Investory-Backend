from allauth.socialaccount.providers.github.views import GitHubOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from rest_auth.registration.views import SocialLoginView
from rest_auth.registration.serializers import SocialLoginSerializer
from allauth.socialaccount.providers.facebook.views import FacebookOAuth2Adapter
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.models import SocialAccount
from .models import Profile
import requests


class FacebookLogin(SocialLoginView):
    adapter_class = FacebookOAuth2Adapter
    client_class = OAuth2Client

    def get_serializer(self, *args, **kwargs):
        serializer_class = self.get_serializer_class()
        kwargs['context'] = self.get_serializer_context()
        return serializer_class(*args, **kwargs)


class CustomGoogleAdapter(GoogleOAuth2Adapter):
    def complete_login(self, request, app, token, **kwargs):
        resp = requests.get(
            self.profile_url,
            params={"access_token": token.token, "alt": "json"},
        )
        resp.raise_for_status()
        extra_data = resp.json()
        login = self.get_provider().sociallogin_from_response(request, extra_data)
        return login, extra_data


class GoogleSocialLoginSerializer(SocialLoginSerializer):
    def get_social_login(self, adapter, app, token, response):
        request = self._get_request()
        social_login, extra_data = adapter.complete_login(
            request, app, token, response=response)

        # create a user profile
        first_name = extra_data['given_name']
        last_name = extra_data['family_name']
        p = Profile.objects.get_or_create(user=social_login.user,
                                          first_name=first_name,
                                          last_name=last_name)
        social_login.token = token
        return social_login


class GoogleLogin(SocialLoginView):
    adapter_class = GoogleOAuth2Adapter
    client_class = OAuth2Client

    def get_serializer(self, *args, **kwargs):
        serializer_class = self.get_serializer_class()
        kwargs['context'] = self.get_serializer_context()
        return serializer_class(*args, **kwargs)

    def process_login(self):
        super().process_login()
        account = SocialAccount.objects.get(user=self.user)
        extra_data = account.extra_data
        p = Profile.objects.get_or_create(user=account.user,
                                          first_name=extra_data['given_name'],
                                          last_name=extra_data['family_name'])
