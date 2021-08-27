from django.core.exceptions import ValidationError
from rest_framework import serializers
from rest_framework import viewsets, status
from rest_auth.registration.serializers import RegisterSerializer
from datetime import timedelta
import datetime

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
        action = self.context['action']
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
        self.validate_portfolio_actions(portfolio, actions)

        # set the earliest portfolio action date
        portfolio.started_at = portfolio.actions.order_by(
            'completed_at').first().completed_at

        total_value,  records = self.calculate_portfolio_records(
            portfolio, portfolio.actions.all(), True)

        PortfolioRecord.objects.bulk_create(records)
        total_cost = self.save_portfolio_holdings(portfolio)
        portfolio.total_value = total_value
        portfolio.total_cost = total_cost
        portfolio.save()
        return portfolio

    def update(self, instance, validated_data):
        if 'actions' in validated_data:
            records_to_delete = instance.records.all()
            holdings_to_delete = instance.holdings.all()
            actions_pks_to_delete = list(instance.actions.all().values_list(
                'pk', flat=True))
            self.validate_portfolio_actions(
                instance, validated_data['actions'])

            new_actions = instance.actions.exclude(
                pk__in=actions_pks_to_delete)
            # set the earliest portfolio action date
            instance.started_at = new_actions.order_by('completed_at')[
                0].completed_at

            total_value, new_records = self.calculate_portfolio_records(
                instance, new_actions, False)
            if new_records:
                # delete old records and actions if everything is valid
                PortfolioAction.objects.filter(
                    pk__in=actions_pks_to_delete).delete()
                holdings_to_delete.delete()
                records_to_delete.delete()
                total_cost = self.save_portfolio_holdings(instance)
                instance.total_cost = total_cost
                PortfolioRecord.objects.bulk_create(new_records)

            instance.total_value = total_value
        if 'name' in validated_data:
            instance.name = validated_data['name']
        if 'is_shared' in validated_data:
            instance.is_shared = validated_data['is_shared']

        instance.save()
        return instance

    def save_portfolio_holdings(self, portfolio):
        actions = portfolio.actions.all()
        holdings = {}
        total_cost = 0
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
                holding.portfolio = portfolio
                holding.asset = action.asset
                holding.quantity = action.quantity
                holding.total_cost = action.total_cost
                holding.cost_basis = holding.total_cost / holding.quantity
                holding.total_value = holding.calculate_total_value()
                holdings[action.asset] = holding

            if action.type == 'SELL':
                total_cost -= action.total_cost
            else:
                total_cost += action.total_cost
        portfolio.realized_gain = realized_gain
        Holding.objects.bulk_create(list(holdings.values()))
        return total_cost

    def validate_portfolio_actions(self, portfolio, actions):
        valid_serializers = []
        for action in actions:
            action['asset_id'] = action['asset_id'].pk
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

    def calculate_portfolio_records(self, portfolio, actions, is_create=True, old_actions=[]):
        records = {}
        exchange_rate = ExchangeRate.objects.get(from_currency="ILS").rate

        dates_delta = (datetime.date.today() - portfolio.started_at).days
        portfolio_records = []
        current_assets = {}
        # Iterate through all dates between the portfolio
        # started_at date (set as first record completion date)
        # till today.
        for i in range(dates_delta + 1):
            curr_date = portfolio.started_at + timedelta(i)
            new_actions = actions.filter(completed_at=curr_date)
            #  add new holding if a new Action is found
            # { Asset : Quantity } Dictionary
            if new_actions.count() > 0:
                for action in new_actions:
                    is_buy = 1
                    if action.type == 'SELL':
                        is_buy = -1
                    # calculate gain/loss on SELL order
                    if action.asset in current_assets:
                        current_assets[action.asset] += is_buy * \
                            action.quantity
                        if current_assets[action.asset] < 0:
                            # negative quantity of stock (portfolio cannot exist)
                            if is_create:
                                portfolio.delete()
                            else:
                                actions.delete()
                            raise serializers.ValidationError(
                                # {'message': f'{action.type} at {action.completed_at} cannot be completed. (Negative Quantity)'})
                                {'message': 'Action changes made are not possible. (Negative Quantity)'})

                    else:
                        current_assets[action.asset] = is_buy * action.quantity
                        if current_assets[action.asset] < 0:
                            if is_create:
                                portfolio.delete()
                            else:
                                actions.delete()
                            raise serializers.ValidationError(
                                {'message': 'Action changes made are not possible. (Negative Quantity)'})

            # iterate through every asset and get its price at the
            # curr_date
            for asset in current_assets:
                # try to get the AssetRecord with the same date
                # except if not found
                try:
                    asset_record = AssetRecord.objects.get(asset=asset,
                                                           date=curr_date)
                except:
                    # find the asset record in the curr_date - NOT EFFICIENT
                    # Looking for range of dates because the date may
                    # not be found the records (different trading days/holidays)
                    asset_record = AssetRecord.objects.filter(
                        asset=asset,
                        date__range=[curr_date - timedelta(31), curr_date])
                    if asset_record.count() > 0:
                        asset_record = asset_record.last()
                    else:
                        if is_create:
                            portfolio.delete()
                        else:
                            actions.delete()
                        raise serializers.ValidationError(
                            {'message': f'{asset.id} price not found at {curr_date}'})

                # add the asset_price * quantity to the total value
                # of the portfolio at the curr_date
                asset_obj = Asset.objects.get_subclass(id=asset.id)
                if str(curr_date) in records:
                    records[str(curr_date)] += asset_record.price * \
                        current_assets[asset] / \
                        (exchange_rate if asset_obj.currency == "ILS" else 1)
                else:
                    records[str(curr_date)] = asset_record.price * \
                        current_assets[asset] / \
                        (exchange_rate if asset_obj.currency == "ILS" else 1)
            portfolio_records.append(PortfolioRecord(
                portfolio=portfolio, date=curr_date, price=records[str(curr_date)]))
        last_price = records[str(curr_date)]
        return (last_price, portfolio_records)


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
