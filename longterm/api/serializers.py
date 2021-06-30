from rest_framework import serializers

from api.models import User, Profile, Asset, USPaper, IsraelPaper, Crypto, AssetRecord, \
    Portfolio, PortfolioAction, PortfolioRecord


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


class PortfolioActionSerializer(serializers.ModelSerializer):
    asset = serializers.PrimaryKeyRelatedField(
        queryset=Asset.objects.select_subclasses())

    class Meta:
        model = PortfolioAction
        fields = '__all__'


class PortfolioRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = PortfolioRecord
        fields = '__all__'


class PortfolioCreateSerializer(serializers.ModelSerializer):
    actions = PortfolioActionSerializer(many=True)

    class Meta:
        model = Portfolio
        fields = ['name', 'actions']

    def validate(self, data):
        print(data)
        print('sdsadsad')
        # foo = data.pop("foo", None)
        # # Do what you want with your value
        return super().validate(data)

    def create(self, validated_data):
        print(validated_data)
        portfolio = Portfolio(name=validated_data['name'])
        # actions = Portfolio
        # user.set_password(validated_data['password'])
        # user.save()
        # profile = Profile(user=user)
        # profile.save()
        # return user


class PortfolioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Portfolio
        fields = '__all__'
