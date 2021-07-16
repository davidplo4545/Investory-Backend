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
    last_updated = models.DateTimeField(blank=True, null=True)


class USPaper(Asset):
    type = models.CharField(
        max_length=9, choices=PAPER_TYPE_CHOICES, default="STOCK")
    name = models.CharField(max_length=120)
    symbol = models.CharField(max_length=6)
    last_price = models.FloatField(blank=True, null=True)
    sector = models.CharField(max_length=200, blank=True, null=True)
    industry = models.CharField(max_length=200, blank=True, null=True)
    last_updated = models.DateTimeField(blank=True, null=True)


class Crypto(Asset):
    symbol = models.CharField(max_length=20)
    name = models.CharField(max_length=30)
    last_price = models.FloatField(blank=True, null=True)
    last_updated = models.DateTimeField(blank=True, null=True)


class AssetRecord(models.Model):
    asset = models.ForeignKey(
        Asset, on_delete=models.CASCADE, related_name="records")
    date = models.DateField()
    price = models.FloatField()

    class Meta:
        ordering = ('date',)


class Portfolio(models.Model):
    name = models.CharField(max_length=200)
    # link_uid
    profile = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name='portfolios', null=True)
    is_shared = models.BooleanField(default=True)
    created_at = models.DateField(auto_now_add=True)
    started_at = models.DateField(blank=True, null=True)
    realized_gain = models.FloatField(default=0)
    total_value = models.FloatField(blank=True, default=0, editable=False)
    total_cost = models.FloatField(blank=True, default=0, editable=False)

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
    total_cost = models.FloatField(blank=True, default=0, editable=False)
    completed_at = models.DateField(default=datetime.date.today)

    def save(self, *args, **kwargs):
        self.total_cost = self.share_price * self.quantity
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


class Holding(models.Model):
    portfolio = models.ForeignKey(
        Portfolio, on_delete=models.CASCADE, related_name='holdings')
    asset = models.ForeignKey(
        Asset, on_delete=models.CASCADE, related_name='holdings')
    quantity = models.FloatField()
    cost_basis = models.FloatField(blank=True)
    total_cost = models.FloatField(blank=True, default=0)
    total_value = models.FloatField(blank=True, default=0, editable=False)

    def calculate_total_value(self):
        """
        Calculates and returns latest total holding value based on the
        last asset price.
        """
        asset_id = self.asset.id
        try:
            asset = USPaper.objects.get(id=asset_id)
        except:
            try:
                asset = IsraelPaper.objects.get(id=asset_id)
            except:
                asset = Crypto.objects.get(id=asset_id)
        return asset.last_price * self.quantity


class PortfolioComparison(models.Model):
    profile = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name='portfolio_comparisons', null=True)
    portfolio = models.ForeignKey(
        Portfolio, on_delete=models.CASCADE, related_name='asset_comparisons')
    asset = models.ForeignKey(
        Asset, on_delete=models.CASCADE, related_name='comparisons')
    asset_portfolio = models.ForeignKey(
        Portfolio, on_delete=models.CASCADE, related_name='portfolio_comparisons', null=True)
