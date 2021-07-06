from django.core.exceptions import ValidationError
from rest_framework import serializers
from rest_framework import viewsets, status
from rest_framework.response import Response
from datetime import timedelta
import datetime

from api.models import ACTION_CHOICES, User, Profile, Asset, USPaper, IsraelPaper, Crypto, AssetRecord, \
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


class UserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer()

    class Meta:
        model = User
        fields = ['id', 'email', 'is_superuser', 'profile']

    def create(self, validated_data):
        user = User(email=validated_data['email'])
        user.set_password(validated_data['password'])
        user.save()
        profile = Profile(user=user)
        profile.save()
        return user


class AssetSerializer(serializers.ModelSerializer):
    def to_representation(self, instance):
        records_count = self.context['count']
        if isinstance(instance, IsraelPaper):
            data = IsraeliPaperSerializer(instance=instance).data
            data['asset'] = 'ISR'
            # Show model records only if one paper is shown
            if records_count == 1:
                records = AssetRecord.objects.filter(asset__id=instance.id)
                records_data = AssetRecordSerializer(records, many=True).data
                data['records'] = records_data
            return data
        elif isinstance(instance, USPaper):
            data = USPaperSerializer(instance=instance).data
            data['asset'] = 'US'
            if records_count == 1:
                records = AssetRecord.objects.filter(asset__id=instance.id)
                records_data = AssetRecordSerializer(records, many=True).data
                data['records'] = records_data
            return data

        elif isinstance(instance, Crypto):
            data = CryptoSerializer(instance=instance).data
            data['asset'] = 'Crypto'
            if records_count == 1:
                records = AssetRecord.objects.filter(asset__id=instance.id)
                records_data = AssetRecordSerializer(records, many=True).data
                data['records'] = records_data
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


class USPaperSerializer(serializers.ModelSerializer):
    class Meta:
        model = USPaper
        fields = '__all__'


class CryptoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Crypto
        fields = '__all__'


class PortfolioActionSerializer(serializers.Serializer):
    asset = serializers.PrimaryKeyRelatedField(
        queryset=Asset.objects.select_subclasses())
    id = serializers.ReadOnlyField(read_only=True)
    type = serializers.ChoiceField(choices=ACTION_CHOICES)
    quantity = serializers.FloatField()
    share_price = serializers.FloatField()
    completed_at = serializers.DateField()

    class Meta:
        fields = ['id', 'asset', 'type', 'quantity',
                  'share_price', 'completed_at']

    def create(self, validated_data):
        action = PortfolioAction()
        try:
            asset = Asset.objects.get(id=validated_data['asset'].id)
            action.asset = asset
        except:
            raise serializers.ValidationError(
                {'error': 'Actions are not valid'})
            # return Response({"status": "Profile has been updated."}, status=status.HTTP_200_OK)
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
        fields = '__all__'


class HoldingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Holding
        fields = '__all__'


class PortfolioCreateSerializer(serializers.ModelSerializer):
    actions = PortfolioActionSerializer(many=True)
    records = PortfolioRecordSerializer(many=True, read_only=True)
    holdings = HoldingSerializer(many=True, read_only=True)

    class Meta:
        model = Portfolio
        fields = ['name', 'actions', 'holdings', 'records']

    def create(self, validated_data):
        portfolio = Portfolio(name=validated_data['name'])
        portfolio.profile = self.context['profile']
        actions = validated_data['actions']

        portfolio.save()
        self.validate_portfolio_actions(portfolio, actions)

        # set the earliest portfolio action date
        portfolio.started_at = portfolio.actions.order_by(
            'completed_at').first().completed_at

        records = self.calculate_portfolio_records(
            portfolio, portfolio.actions.all(), True)

        PortfolioRecord.objects.bulk_create(records)
        portfolio.save()
        self.save_portfolio_holdings(portfolio)
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
            instance.started_at = instance.actions.order_by('completed_at')[
                0].completed_at

            new_records = self.calculate_portfolio_records(
                instance, new_actions, False)
            if new_records:
                # delete old records and actions if everything is valid
                PortfolioAction.objects.filter(
                    pk__in=actions_pks_to_delete).delete()
                holdings_to_delete.delete()
                records_to_delete.delete()
                self.save_portfolio_holdings(instance)
                PortfolioRecord.objects.bulk_create(new_records)

        if 'name' in validated_data:
            instance.name = validated_data['name']
        instance.save()
        return instance

    def save_portfolio_holdings(self, portfolio):
        actions = portfolio.actions.all()
        holdings = {}
        for action in actions:
            is_buy = 1 if action.type == "BUY" else -1
            if action.asset in holdings:
                holding = holdings[action.asset]
                holding.quantity += action.quantity * is_buy
                holding.total_value += action.total_value * is_buy
                holding.total_cost += action.total_cost * is_buy
                holding.cost_basis = holding.total_cost / holding.quantity
            else:
                holding = Holding()
                holding.portfolio = portfolio
                holding.asset = action.asset
                holding.quantity = action.quantity
                holding.total_value = action.total_value
                holding.total_cost = action.total_cost
                holding.cost_basis = holding.total_cost / holding.quantity
                holdings[action.asset] = holding
        Holding.objects.bulk_create(list(holdings.values()))

    def validate_portfolio_actions(self, portfolio, actions):
        valid_serializers = []
        for action in actions:
            action['asset'] = action['asset'].pk
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
                    if action.asset in current_assets:
                        is_buy = 1
                        if action.type == 'SELL':
                            is_buy = -1
                        current_assets[action.asset] += is_buy * \
                            action.quantity
                        if current_assets[action.asset] <= 0:
                            # negative quantity of stock (portfolio cannot exist)
                            if is_create:
                                portfolio.delete()
                            else:
                                actions.delete()
                            raise serializers.ValidationError(
                                {'message': f'{action.type} at {action.completed_at} cannot be completed. (Negative Quantity)'})
                    else:
                        current_assets[action.asset] = action.quantity
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
                        date__range=[curr_date - timedelta(5), curr_date])
                    if asset_record.count() > 0:
                        asset_record = asset_record.last()
                    else:
                        raise serializers.ValidationError(
                            {'message': f'{asset.symbol} price not found at {curr_date}'})

                # add the asset_price * quantity to the total value
                # of the portfolio at the curr_date
                if str(curr_date) in records:
                    records[str(curr_date)] += asset_record.price * \
                        current_assets[asset]
                else:
                    records[str(curr_date)] = asset_record.price * \
                        current_assets[asset]
                portfolio_records.append(PortfolioRecord(
                    portfolio=portfolio, date=curr_date, price=records[str(curr_date)]))
        return portfolio_records


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
        print(validated_data)
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
                if asset_record_at_action_date.count() > 0:
                    asset_record_at_action_date = asset_record_at_action_date.last()
                else:
                    raise serializers.ValidationError(
                        {'message': f'{asset.symbol} price not found at {action.completed_at}'})

            asset_price = asset_record_at_action_date.price
            quantity = action.total_cost / asset_price
            asset_action = {"type": action.type,
                            "asset": asset.id,
                            "quantity": quantity,
                            "share_price": asset_price,
                            "completed_at": action.completed_at}
            asset_actions.append(asset_action)

        name = f'{portfolio.name} vs {asset.symbol}'
        serializer_data = {"name": name, "actions": asset_actions}
        print(serializer_data)
        serializer = PortfolioCreateSerializer(data=serializer_data, context={
            'profile': None})
        serializer.is_valid(raise_exception=True)
        asset_portfolio = serializer.save()
        comparison = PortfolioComparison(asset_portfolio=asset_portfolio,
                                         portfolio=portfolio, asset=asset)
        comparison.save()
        return comparison


class PortfolioComparisonSerializer(serializers.ModelSerializer):
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
