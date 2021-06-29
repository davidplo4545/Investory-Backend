from rest_framework import serializers

from api.models import User, Asset, USPaper, IsraelPaper, Crypto, AssetRecord


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ['id', 'email', 'is_superuser']


class AssetSerializer(serializers.ModelSerializer):

    def to_representation(self, instance):
        if isinstance(instance, IsraelPaper):
            data = IsraeliPaperSerializer(instance=instance).data
            data['asset'] = 'ISR'
            return data
        elif isinstance(instance, USPaper):
            data = USPaperSerializer(instance=instance).data
            data['asset'] = 'US'
            return data
        elif isinstance(instance, Crypto):
            data = CryptoSerializer(instance=instance).data
            data['asset'] = 'Crypto'
            return data

    class Meta:
        model = Asset
        fields = '__all__'


class IsraeliPaperSerializer(serializers.ModelSerializer):
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
