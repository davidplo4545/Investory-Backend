import datetime
from datetime import timedelta
from dateutil.relativedelta import relativedelta
from django.db import models

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.db.models.fields import related
from model_utils.managers import InheritanceManager
from .managers import UserManager

from .utils import create_shortened_url

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

USD = "USD"
ILS = "ILS"
CURRENCY_CHOICS = (
    (USD, "USD"),
    (ILS, "ILS"),
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


class ExchangeRate(models.Model):
    from_currency = models.CharField(
        max_length=9, choices=CURRENCY_CHOICS)
    to_currency = models.CharField(
        max_length=9, choices=CURRENCY_CHOICS)
    rate = models.FloatField(null=True)


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
        self.one_year_return = self.get_return(records, last_record, 12)
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
        self.one_year_return = self.get_return(records, last_record, 12)
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
    is_shared = models.BooleanField(default=False)
    created_at = models.DateField(auto_now_add=True)
    started_at = models.DateField(blank=True, null=True)
    realized_gain = models.FloatField(default=0)
    total_value = models.FloatField(blank=True, default=0, editable=False)
    total_cost = models.FloatField(blank=True, default=0, editable=False)
    short_url = models.CharField(max_length=15, unique=True, blank=True)

    class Meta:
        ordering = ('started_at',)

    def create_portfolio_holdings(self):
        actions = self.actions.all()
        holdings = {}
        realized_gain = 0
        for action in actions:
            if action.asset in holdings:
                is_buy = 1 if action.type == "BUY" else -1
                holding = holdings[action.asset]
                if is_buy == 1:
                    holding.quantity += action.quantity * is_buy
                    holding.total_cost += action.total_cost * is_buy
                    holding.cost_basis = holding.total_cost / holding.quantity
                    holding.total_value = holding.calculate_total_value()
                else:
                    realized_gain += action.quantity * (action.share_price
                                                        - holding.cost_basis)
                    if holding.quantity - action.quantity <= 0:
                        holdings.pop(action.asset)
                    else:
                        holding.quantity += action.quantity * is_buy
                        holding.total_cost -= holding.cost_basis * action.quantity
                        holding.total_value = holding.calculate_total_value()
            else:
                holding = Holding()
                holding.portfolio = self
                holding.asset = action.asset
                holding.quantity = action.quantity
                holding.total_cost = action.total_cost
                holding.cost_basis = holding.total_cost / holding.quantity
                holding.total_value = holding.calculate_total_value()
                holdings[action.asset] = holding

        self.realized_gain = realized_gain
        Holding.objects.bulk_create(list(holdings.values()))

    def calculate_total_values(self):
        total_cost = 0
        total_value = 0
        holdings = self.holdings.all()
        for holding in holdings:
            asset = Asset.objects.get_subclass(id=holding.asset.id)
            exchange_rate = exchange_rate if asset.currency == "ILS" else 1
            total_cost += holding.total_cost / exchange_rate
            total_value += holding.total_value / exchange_rate
        return total_value, 0 if total_cost < 0 else total_cost

    def save(self, *args, **kwargs):
        # If the short url wasn't specified
        if not self.short_url:
            # We pass the model instance that is being saved
            self.short_url = create_shortened_url(self)

        super().save(*args, **kwargs)


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
