from django.db import models

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from model_utils.managers import InheritanceManager
from .managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(max_length=254, unique=True)
    name = models.CharField(max_length=254, null=True, blank=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    last_login = models.DateTimeField(null=True, blank=True)
    date_joined = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = 'email'
    EMAIL_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    def get_absolute_url(self):
        return "/users/%i/" % (self.pk)


class Profile(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='profile')


class Asset(models.Model):
    objects = InheritanceManager()

# class IsraelPaper(Asset):
    # company = models.CharField()


class USPaper(Asset):
    ticker = models.CharField(max_length=6)
    company = models.CharField(max_length=128)


class Crypto(Asset):
    name = models.CharField(max_length=30)


class Portfolio(models.Model):
    # link_uid
    profile = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name='portfolio')
    is_shared = models.BooleanField(default=True)


class PortfolioAction(models.Model):
    # Buy / Sell
    # action_type =
    portfolio = models.ForeignKey(
        Portfolio, on_delete=models.CASCADE, related_name='actions')
    asset = models.ForeignKey(
        Asset, on_delete=models.CASCADE, related_name='actions')
