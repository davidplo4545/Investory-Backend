import datetime
from datetime import timedelta
from django.db import models

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.db.models.fields import related
from model_utils.managers import InheritanceManager
from .managers import UserManager

ETF = "ETF"
STOCK = "STOCK"

PAPER_TYPE_CHOICES = (
    (ETF, "ETF"),
    (STOCK, "STOCK"),
)

BUY = "BUY"
SELL = "SELL"
ACTION_CHOICES = (
    (BUY, "BUY"),
    (SELL, "SELL"),
)


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
    first_name = models.CharField(max_length=125, blank=True)
    last_name = models.CharField(max_length=125, blank=True)


class Asset(models.Model):
    objects = InheritanceManager()


class IsraelPaper(Asset):
    paper_id = models.IntegerField()
    type = models.CharField(
        max_length=9, choices=PAPER_TYPE_CHOICES, default="STOCK")
    name = models.CharField(max_length=120)
    symbol = models.CharField(max_length=30, blank=True, null=True)
    last_price = models.FloatField(blank=True, null=True)


class USPaper(Asset):
    type = models.CharField(
        max_length=9, choices=PAPER_TYPE_CHOICES, default="STOCK")
    name = models.CharField(max_length=120)
    symbol = models.CharField(max_length=6)
    last_price = models.FloatField(blank=True, null=True)
    sector = models.CharField(max_length=200, blank=True, null=True)
    industry = models.CharField(max_length=200, blank=True, null=True)


class Crypto(Asset):
    symbol = models.CharField(max_length=20)
    name = models.CharField(max_length=30)
    last_price = models.FloatField(blank=True, null=True)


class AssetRecord(models.Model):
    asset = models.ForeignKey(
        Asset, on_delete=models.CASCADE, related_name="records")
    date = models.DateField()
    price = models.FloatField()


class Portfolio(models.Model):
    name = models.CharField(max_length=200, unique=True)
    # link_uid
    profile = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name='portfolio')
    is_shared = models.BooleanField(default=True)
    created_at = models.DateField(auto_now_add=True)
    started_at = models.DateField(blank=True, null=True)

    class Meta:
        ordering = ('started_at',)


class PortfolioAction(models.Model):
    type = models.CharField(
        max_length=4, choices=ACTION_CHOICES, default="BUY")
    portfolio = models.ForeignKey(
        Portfolio, on_delete=models.CASCADE, related_name='actions')
    asset = models.ForeignKey(
        Asset, on_delete=models.CASCADE, related_name='actions')
    quantity = models.FloatField(default=0)
    share_price = models.FloatField(default=0)
    total_value = models.FloatField(blank=True, default=0, editable=False)
    completed_at = models.DateField(default=datetime.date.today)

    def save(self, *args, **kwargs):
        self.total_value = self.share_price * self.quantity
        super(PortfolioAction, self).save(*args, **kwargs)

    class Meta:
        ordering = ('completed_at',)


class PortfolioRecord(models.Model):
    portfolio = models.ForeignKey(
        Portfolio, on_delete=models.CASCADE, related_name='records')
    date = models.DateField()
    price = models.FloatField()

    class Meta:
        ordering = ('date',)
