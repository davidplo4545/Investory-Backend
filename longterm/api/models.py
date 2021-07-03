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

    def calculate_portfolio_records(self):
        # starting_date = self.started_at
        # oldest items first
        records = {}
        dates_delta = (datetime.date.today() - self.started_at).days
        portfolio_records = []
        current_assets = {}
        actions = self.actions.all()
        # create list of all dates from the starting date
        # till today's date
        for i in range(dates_delta + 1):
            curr_date = self.started_at + timedelta(i)
            new_actions = actions.filter(completed_at=curr_date)
            #  add new holding if a new Action is found
            # { Asset : Quantity } Dictionary
            if new_actions.count() > 0:
                for action in new_actions:
                    if action.asset in current_assets:
                        is_buy = 1
                        if action.type == 'SELL':
                            is_buy = -1
                        current_assets[action.asset] += is_buy * \
                            action.quantity
                    else:
                        current_assets[action.asset] = action.quantity
            for asset in current_assets:
                # try to get the AssetRecord with the same date
                # except if not found (Except not smart)
                try:
                    asset_record = AssetRecord.objects.get(asset=asset,
                                                           date=curr_date)
                except:
                    # find the asset record in the curr_date - NOT EFFICIENT
                    # Looking for range of dates because the date may
                    # not be found the records (different trading days/holidays)
                    asset_record = AssetRecord.objects.filter(
                        asset=asset,
                        date__range=[curr_date - timedelta(5), curr_date])
                    if asset_record.count() > 0:
                        asset_record = asset_record.last()
                    else:
                        return {}

                if str(curr_date) in records:
                    records[str(curr_date)] += asset_record.price * \
                        current_assets[asset]
                else:
                    records[str(curr_date)] = asset_record.price * \
                        current_assets[asset]

            portfolio_records.append(PortfolioRecord(
                portfolio=self, date=curr_date, price=records[str(curr_date)]))

        print(current_assets)
        return portfolio_records


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


class PortfolioRecord(models.Model):
    portfolio = models.ForeignKey(
        Portfolio, on_delete=models.CASCADE, related_name='records')
    date = models.DateField()
    price = models.FloatField()
