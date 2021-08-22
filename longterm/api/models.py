import datetime
from datetime import timedelta
from dateutil.relativedelta import relativedelta
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

    def get_return(self, records, last_record, months):
        '''
        Calculates and returns the paper return over
        the 'months' period set.
        If months is -1 it returns the year to date return
        '''
        if months == -1:
            prev_date = last_record.date.replace(month=1, day=1)
        else:
            prev_date = last_record.date + relativedelta(months=-months)
        prev_records = records.filter(
            date__range=[prev_date - timedelta(31), prev_date])
        if prev_records.count() == 0:
            return None
        prev_record = prev_records.last()
        return (last_record.price / prev_record.price - 1) * 100


class IsraelPaper(Asset):
    paper_id = models.IntegerField()
    type = models.CharField(
        max_length=9, choices=PAPER_TYPE_CHOICES, default="STOCK")
    currency = models.CharField(
        default="ILS",
        max_length=9, editable=False)
    location = models.CharField(
        default="Israel",
        max_length=20, editable=False)
    name = models.CharField(max_length=120)
    symbol = models.CharField(max_length=30, blank=True, null=True)
    last_price = models.FloatField(blank=True, null=True)
    last_updated = models.DateTimeField(blank=True, null=True)

    # Returns
    three_month_return = models.FloatField(blank=True, null=True)
    six_month_return = models.FloatField(blank=True, null=True)
    ytd_return = models.FloatField(blank=True, null=True)
    one_year_return = models.FloatField(blank=True, null=True)
    three_year_return = models.FloatField(blank=True, null=True)

    def calculate_returns(self):
        records = AssetRecord.objects.filter(asset=self)
        if records.count() > 0:
            last_record = records.last()

            self.three_month_return = self.get_return(records, last_record, 3)
            self.six_month_return = self.get_return(records, last_record, 6)
            self.one_year_return = self.get_return(records, last_record, 12)
            self.ytd_return = self.get_return(records, last_record, -1)
            self.three_year_return = self.get_return(records, last_record, 36)


class USPaper(Asset):
    type = models.CharField(
        max_length=9, choices=PAPER_TYPE_CHOICES, default="STOCK")
    currency = models.CharField(
        default="USD",
        max_length=9, editable=False)
    location = models.CharField(
        default="United States",
        max_length=20, editable=False)
    name = models.CharField(max_length=120)
    symbol = models.CharField(max_length=6)
    last_price = models.FloatField(blank=True, null=True)
    last_updated = models.DateTimeField(blank=True, null=True)

    # General
    sector = models.CharField(max_length=200, blank=True, null=True)
    industry = models.CharField(max_length=200, blank=True, null=True)
    market_cap = models.FloatField(blank=True, null=True)
    business_summary = models.TextField(blank=True, null=True)
    website_url = models.URLField(blank=True, null=True)
    logo_url = models.URLField(blank=True, null=True)
    fulltime_employees = models.IntegerField(blank=True, null=True)
    one_year_high = models.FloatField(blank=True, null=True)
    one_year_low = models.FloatField(blank=True, null=True)

    # Valuation Metrics
    enterprise_value = models.FloatField(blank=True, null=True)
    book_value = models.FloatField(blank=True, null=True)
    price_to_book = models.FloatField(blank=True, null=True)
    current_ratio = models.FloatField(blank=True, null=True)
    trailing_pe = models.FloatField(blank=True, null=True)
    forward_pe = models.FloatField(blank=True, null=True)
    peg_ratio = models.FloatField(blank=True, null=True)
    ps_ratio = models.FloatField(blank=True, null=True)
    revenue_growth = models.FloatField(blank=True, null=True)

    # Returns
    three_month_return = models.FloatField(blank=True, null=True)
    six_month_return = models.FloatField(blank=True, null=True)
    ytd_return = models.FloatField(blank=True, null=True)
    one_year_return = models.FloatField(blank=True, null=True)
    three_year_return = models.FloatField(blank=True, null=True)

    # Analysts
    num_of_analysts = models.IntegerField(blank=True, null=True)
    mean_analyst_price = models.FloatField(blank=True, null=True)

    def calculate_returns(self):
        records = AssetRecord.objects.filter(asset=self)
        last_record = records.last()

        self.three_month_return = self.get_return(records, last_record, 3)
        self.six_month_return = self.get_return(records, last_record, 6)
        self.ytd_return = self.get_return(records, last_record, -1)
        self.three_year_return = self.get_return(records, last_record, 36)


class Crypto(Asset):
    type = models.CharField(
        default="Crypto",
        max_length=9, editable=False)
    currency = models.CharField(
        default="USD",
        max_length=9, editable=False)
    location = models.CharField(
        default="Global",
        max_length=9, editable=False)
    symbol = models.CharField(max_length=20)
    name = models.CharField(max_length=30)
    last_price = models.FloatField(blank=True, null=True)
    last_updated = models.DateTimeField(blank=True, null=True)

    description = models.TextField(blank=True, null=True)
    market_cap = models.FloatField(blank=True, null=True)
    one_year_high = models.FloatField(blank=True, null=True)
    one_year_low = models.FloatField(blank=True, null=True)

    # Returns
    three_month_return = models.FloatField(blank=True, null=True)
    six_month_return = models.FloatField(blank=True, null=True)
    ytd_return = models.FloatField(blank=True, null=True)
    one_year_return = models.FloatField(blank=True, null=True)
    three_year_return = models.FloatField(blank=True, null=True)

    def calculate_returns(self):
        records = AssetRecord.objects.filter(asset=self)
        last_record = records.last()

        self.three_month_return = self.get_return(records, last_record, 3)
        self.six_month_return = self.get_return(records, last_record, 6)
        self.ytd_return = self.get_return(records, last_record, -1)
        self.three_year_return = self.get_return(records, last_record, 36)


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
