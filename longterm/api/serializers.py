from django.core.exceptions import ValidationError
from rest_framework import serializers
from rest_framework import viewsets, status
from rest_auth.registration.serializers import RegisterSerializer
from datetime import timedelta
from .tasks import create_portfolio_records
import time


from api.models import ACTION_CHOICES, ExchangeRate, User, Profile, Asset, USPaper, IsraelPaper, Crypto, AssetRecord, \
    Portfolio, PortfolioAction, PortfolioRecord, ACTION_CHOICES, Holding, PortfolioComparison


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = '__all__'


class ProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['first_name', 'last_name']

    def update(self, instance, validated_data):
        """
        Update profile related fields
        """
        first_name = validated_data.pop('first_name')
        last_name = validated_data.pop('last_name')

        instance.first_name = first_name
        instance.last_name = last_name
        instance.save()

        return instance


class RegisterSerializer(RegisterSerializer):
    first_name = serializers.CharField(max_length=20)
    last_name = serializers.CharField(max_length=20)

    class Meta:
        model = User
        fields = ['id', 'email', 'password1',
                  'first_name', 'last_name']

    def validate_first_name(self, first_name):
        return first_name

    def validate_last_name(self, last_name):
        return last_name

    def get_cleaned_data(self):
        return {
            'password1': self.validated_data.get('password1'),
            'email': self.validated_data.get('email'),
            'first_name': self.validated_data.get('first_name', ''),
            'last_name': self.validated_data.get('last_name', ''),
        }

    def save(self, request):
        res = super(RegisterSerializer, self).save(request)
        cleaned_data = self.get_cleaned_data()
        profile = Profile(id=res.id,
                          user=res, first_name=cleaned_data['first_name'],
                          last_name=cleaned_data['last_name'],)
        profile.save()
        return res


class UserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer()

    class Meta:
        model = User
        fields = ['id', 'email', 'profile']


class AssetSerializer(serializers.ModelSerializer):
    def to_representation(self, instance):
        records_count = self.context['count']
        if isinstance(instance, IsraelPaper):
            data = IsraeliPaperSerializer(instance=instance).data
            # Show model records only if one paper is shown
            if records_count == 1:
                records = AssetRecord.objects.filter(asset__id=instance.id)
                records_data = AssetRecordSerializer(records, many=True).data
                data['records'] = records_data

        elif isinstance(instance, USPaper):
            data = USPaperSerializer(instance=instance).data
            if records_count == 1:
                records = AssetRecord.objects.filter(asset__id=instance.id)
                records_data = AssetRecordSerializer(records, many=True).data
                data['records'] = records_data

        elif isinstance(instance, Crypto):
            data = CryptoSerializer(instance=instance).data
            if records_count == 1:
                records = AssetRecord.objects.filter(asset__id=instance.id)
                records_data = AssetRecordSerializer(records, many=True).data
                data['records'] = records_data
        # remove not neccassary data to lower load on clinet
        if records_count != 1:
            for key in ['last_updated',
                        'sector', 'forward_pe',
                        'industry', 'peg_ratio',
                        'market_cap', 'ps_ratio', 'description',
                        'business_summary', 'revenue_growth',
                        'website_url', 'three_month_return',
                        'logo_url', 'six_month_return',
                        'fulltime_employees', 'ytd_return',
                        'one_year_high', 'one_year_return',
                        'one_year_low', 'three_year_return',
                        'enterprise_value', 'num_of_analysts',
                        'book_value', 'mean_analyst_price',
                        'price_to_book',
                        'current_ratio',
                        'trailing_pe']:
                if key in data:
                    data.pop(key)
        return data

    class Meta:
        model = Asset
        fields = '__all__'


class SingleAssetSerializer(serializers.ModelSerializer):
    def to_representation(self, instance):
        try:
            obj = IsraelPaper.objects.get(id=instance.id)
            data = IsraeliPaperSerializer(instance=obj).data
        except:
            try:
                obj = USPaper.objects.get(id=instance.id)
                data = USPaperSerializer(instance=obj).data
            except:
                obj = Crypto.objects.get(id=instance.id)
                data = CryptoSerializer(instance=obj).data

        for key in ['last_updated',
                    'sector', 'forward_pe',
                    'industry', 'peg_ratio',
                    'market_cap', 'ps_ratio', 'description',
                    'business_summary', 'revenue_growth',
                    'website_url', 'three_month_return',
                    'logo_url', 'six_month_return',
                    'fulltime_employees', 'ytd_return',
                    'one_year_high', 'one_year_return',
                    'one_year_low', 'three_year_return',
                    'enterprise_value', 'num_of_analysts',
                    'book_value', 'mean_analyst_price',
                    'price_to_book',
                    'current_ratio',
                    'trailing_pe']:
            if key in data:
                data.pop(key)
        return data

    class Meta:
        model = Asset
        fields = '__all__'


class AssetRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssetRecord
        fields = '__all__'


class IsraeliPaperSerializer(serializers.ModelSerializer):
    # records = AssetRecordSerializer()
    class Meta:
        model = IsraelPaper
        fields = '__all__'

    # def to_representation(self, instance):
    #     count = self.context['count']
    #     if count == 1:
    #         return super().to_representation()


class USPaperSerializer(serializers.ModelSerializer):
    class Meta:
        model = USPaper
        fields = '__all__'


class CryptoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Crypto
        fields = '__all__'


class PortfolioActionSerializer(serializers.Serializer):
    asset_id = serializers.PrimaryKeyRelatedField(
        write_only=True,
        queryset=Asset.objects.select_subclasses())
    asset = SingleAssetSerializer(read_only=True)
    type = serializers.ChoiceField(choices=ACTION_CHOICES)
    quantity = serializers.FloatField()
    share_price = serializers.FloatField()
    completed_at = serializers.DateField()

    class Meta:
        fields = ['asset',  'type', 'quantity',
                  'share_price', 'completed_at']

    def create(self, validated_data):
        action = PortfolioAction()
        try:
            asset = Asset.objects.get(id=validated_data['asset_id'].pk)
            action.asset = asset
        except:
            raise serializers.ValidationError(
                {'error': 'Actions are not valid'})
        action.type = validated_data['type']
        action.quantity = validated_data['quantity']
        action.share_price = validated_data['share_price']
        action.completed_at = validated_data['completed_at']
        action.portfolio = self.context['portfolio']
        action.save()
        return action


class PortfolioRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = PortfolioRecord
        fields = ['date', 'price']


class HoldingSerializer(serializers.ModelSerializer):
    asset = SingleAssetSerializer(read_only=True)

    class Meta:
        model = Holding
        fields = ['id', 'quantity', 'cost_basis',
                  'total_cost', 'total_value', "asset"]


class PortfolioCreateSerializer(serializers.ModelSerializer):
    actions = PortfolioActionSerializer(many=True)
    records = PortfolioRecordSerializer(many=True, read_only=True)
    holdings = HoldingSerializer(many=True, read_only=True)

    class Meta:
        model = Portfolio
        fields = ['id', 'name', 'actions', 'holdings',
                  'records', 'is_shared', 'short_url']

    def validate(self, data):
        """
        Check that user doesn't have portfolio with same name already.
        """
        profile = self.context['profile']
        if 'name' in data:
            name = data['name']
            portfolios = Portfolio.objects.filter(profile=profile, name=name)
            if portfolios.count() > 0:
                raise serializers.ValidationError(
                    {"message": "Portoflio with this name already exists."})
            else:
                return data
        return data

    def create(self, validated_data):
        portfolio = Portfolio(name=validated_data['name'])
        portfolio.profile = self.context['profile']
        actions = validated_data['actions']

        portfolio.save()
        self.validate_and_create_portfolio_actions(portfolio, actions)
        portfolio.create_portfolio_holdings()
        portfolio.total_value, portfolio.total_cost = \
            portfolio.calculate_total_values()

        action_pks = portfolio.actions.values_list('pk', flat=True)
        # calling celery task to create the records
        create_portfolio_records.delay(
            portfolio.id, action_pks, [])

        portfolio.save()
        return portfolio

    def update(self, instance, validated_data):
        if 'actions' in validated_data:
            records_pks_to_delete = list(instance.records.all().values_list(
                'pk', flat=True))
            holdings_pks_to_delete = list(instance.holdings.all().values_list(
                'pk', flat=True))
            actions_pks_to_delete = list(instance.actions.all().values_list(
                'pk', flat=True))
            self.validate_and_create_portfolio_actions(
                instance, validated_data['actions'], False)

            action_pks = list(instance.actions.exclude(
                pk__in=actions_pks_to_delete).values_list('pk', flat=True))

            PortfolioAction.objects.filter(
                pk__in=actions_pks_to_delete).delete()

            instance.create_portfolio_holdings()

            # calling celery task to create the records
            create_portfolio_records.delay(
                instance.id, action_pks, records_pks_to_delete)

            Holding.objects.filter(
                pk__in=holdings_pks_to_delete).delete()
            instance.total_value, instance.total_cost = \
                instance.calculate_total_values()

        if 'name' in validated_data:
            instance.name = validated_data['name']
        if 'is_shared' in validated_data:
            instance.is_shared = validated_data['is_shared']
        instance.save()
        return instance

    def validate_and_create_portfolio_actions(self, portfolio, actions, is_create):
        valid_serializers = []
        asset_quantities = {}
        for action in actions:
            is_buy = 1 if action['type'] == "BUY" else -1
            asset = Asset.objects.get_subclass(id=action['asset_id'].pk)
            action['asset_id'] = asset.pk
            first_record_date = asset.records \
                .first().date
            if action['completed_at'] < first_record_date:
                raise serializers.ValidationError(
                    {'error': 'Actions are not valid (No asset data)'})
            if asset not in asset_quantities:
                asset_quantities[asset] = 0
            asset_quantities[asset] += action['quantity'] * is_buy
            # total quantity of buying/selling cannot be negative
            if asset_quantities[asset] < 0:
                if is_create:
                    portfolio.delete()
                raise serializers.ValidationError(
                    {'error': 'Actions are not valid (Negative Quantity)'})
            serializer = PortfolioActionSerializer(
                data=action, context={'portfolio': portfolio})
            if serializer.is_valid(raise_exception=True):
                valid_serializers.append(serializer)
            else:
                raise serializers.ValidationError(
                    {'error': 'Actions are not valid'})

        # create the action models through the serializers only
        # if all of them are valid
        actions = []
        if valid_serializers:
            for serializer in valid_serializers:
                serializer.save()
        else:
            raise serializers.ValidationError(
                {'error': 'Actions are not valid'})


class PortfolioRetrieveSerializer(serializers.ModelSerializer):
    actions = PortfolioActionSerializer(many=True, read_only=True)
    records = serializers.SerializerMethodField('get_records')
    holdings = HoldingSerializer(many=True, read_only=True)

    class Meta:
        model = Portfolio
        fields = '__all__'

    def get_records(self, portfolio):
        # show only Monday-Friday Portfolio Records
        queryset = portfolio.records.filter(date__week_day__in=[2, 3, 4, 5, 6])
        serializer = PortfolioRecordSerializer(instance=queryset, many=True)
        return serializer.data


class PortfolioListSerializer(serializers.ModelSerializer):
    actions = PortfolioActionSerializer(many=True, read_only=True)
    holdings = HoldingSerializer(many=True, read_only=True)

    class Meta:
        model = Portfolio
        fields = '__all__'


class PortfolioComparisonCreateSerializer(serializers.Serializer):

    asset = serializers.PrimaryKeyRelatedField(
        queryset=Asset.objects.select_subclasses())

    class Meta:
        fields = ['portfolio', 'asset']

    def create(self, validated_data):
        portfolio = self.context['portfolio']
        asset = validated_data['asset']
        asset_obj = Asset.objects.get_subclass(id=asset.id)
        exchange_rate = ExchangeRate.objects.get(from_currency="ILS").rate
        exchange_rate = exchange_rate if asset_obj.currency == "ILS" else 1
        portfolio_actions = portfolio.actions.all()
        asset_actions = []
        # Generate a list of actions for a portfolio with
        # only one Asset that's being passed to the serializer
        for action in portfolio_actions:
            try:
                asset_record_at_action_date = AssetRecord.objects.get(asset=asset,
                                                                      date=action.date)
            except:
                # find the asset record in the curr_date - NOT EFFICIENT
                # Looking for range of dates because the date may
                # not be found the records (different trading days/holidays)
                asset_record_at_action_date = AssetRecord.objects.filter(
                    asset=asset,
                    date__range=[action.completed_at - timedelta(5), action.completed_at])
                if asset_record_at_action_date.count() == 0:
                    asset_record_at_action_date = AssetRecord.objects.filter(
                        asset=asset,
                        date__range=[action.completed_at - timedelta(31), action.completed_at])
                if asset_record_at_action_date.count() > 0:
                    asset_record_at_action_date = asset_record_at_action_date.last()
                else:
                    raise serializers.ValidationError(
                        {'message': f'{asset.symbol} price not found at {action.completed_at}'})

            asset_price = asset_record_at_action_date.price / exchange_rate
            quantity = action.total_cost / asset_price
            asset_action = {"type": action.type,
                            "asset_id": asset.id,
                            "quantity": quantity,
                            "share_price": asset_price,
                            "completed_at": action.completed_at}
            asset_actions.append(asset_action)

        name = f'{portfolio.name} vs {asset.symbol}'
        serializer_data = {"name": name, "actions": asset_actions}
        serializer = PortfolioCreateSerializer(data=serializer_data, context={
            'profile': None, 'action': 'create'})
        serializer.is_valid(raise_exception=True)
        asset_portfolio = serializer.save()
        comparison = PortfolioComparison(asset_portfolio=asset_portfolio,
                                         portfolio=portfolio, asset=asset, profile=self.context['profile'])
        comparison.save()
        return comparison


class PortfolioComparisonRetrieveSerializer(serializers.ModelSerializer):
    asset_portfolio_holdings = serializers.SerializerMethodField(
        'get_asset_portfolio_holdings')
    asset_portfolio_records = serializers.SerializerMethodField(
        'get_asset_portfolio_records')

    class Meta:
        model = PortfolioComparison
        fields = '__all__'

    def get_asset_portfolio_records(self, obj):
        asset_portfolio = obj.asset_portfolio
        records = PortfolioRecord.objects.filter(portfolio=asset_portfolio)
        serializer = PortfolioRecordSerializer(instance=records, many=True)
        return serializer.data

    def get_asset_portfolio_holdings(self, obj):
        asset_portfolio = obj.asset_portfolio
        holdings = Holding.objects.filter(portfolio=asset_portfolio)
        serializer = HoldingSerializer(instance=holdings, many=True)
        return serializer.data


class PortfolioComparisonListSerializer(serializers.ModelSerializer):
    class Meta:
        model = PortfolioComparison
        fields = '__all__'
