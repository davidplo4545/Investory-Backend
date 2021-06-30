from django.shortcuts import render

from rest_framework import viewsets, status
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import User, Profile, Asset, IsraelPaper, USPaper, Crypto, AssetRecord,\
    Portfolio, PortfolioRecord, PortfolioAction
from .serializers import AssetSerializer, PortfolioCreateSerializer, PortfolioSerializer, ProfileUpdateSerializer, UserSerializer
from .scraper import IsraeliPaperScraper, USPapersScraper


class UserViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    queryset = User.objects.all()

    def list(self, request):
        serializer = self.serializer_class(
            self.queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['patch'])
    def update_profile(self, request):
        print(self.request.user.id)
        profile = Profile.objects.get(user__id=self.request.user.id)
        print(profile)
        serializer = ProfileUpdateSerializer(
            profile, data=request.data, partial=True)
        serializer.is_valid()
        self.perform_update(serializer)
        return Response({"status": "Profile has been updated."}, status=status.HTTP_200_OK)


class AssetViewSet(viewsets.ViewSet):
    serializer_class = AssetSerializer

    def get_queryset(self):
        """

        """
        asset_type = self.request.query_params.get('type')
        symbol = self.request.query_params.get('symbol')
        if asset_type is not None:
            if asset_type == 'isr':
                if symbol:
                    symbol = symbol.upper()
                    try:
                        return IsraelPaper.objects.filter(paper_id=symbol)
                    except:
                        return Response({'error': 'No Israeli papers were found.'})
                else:
                    return IsraelPaper.objects.all()
            elif asset_type == 'us':
                if symbol:
                    symbol = symbol.upper()
                    try:
                        return USPaper.objects.filter(symbol=symbol)
                    except:
                        return Response({'error': 'No US papers were found.'})
                else:
                    return USPaper.objects.all()
            elif asset_type == 'crypto':
                if symbol:
                    symbol = symbol.upper()
                    try:
                        return Crypto.objects.filter(symbol=symbol)
                    except:
                        return Response({'error': 'No cryptos were found.'})
                else:
                    return Crypto.objects.all()
        else:
            return Asset.objects.select_subclasses()

    def list(self, request):
        queryset = self.get_queryset()
        serializer = self.serializer_class(
            queryset, many=True, context={'count': queryset.count()})

        if len(serializer.data) == 0:
            return Response({'error': 'No asset matching the query was found.'})
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        queryset = Asset.objects.select_subclasses()
        paper = get_object_or_404(queryset, pk=pk)
        serializer = self.serializer_class(paper, context={'count': 1})
        return Response(serializer.data)


class PortfolioViewSet(viewsets.ModelViewSet):
    serializer_class = PortfolioSerializer
    queryset = Portfolio.objects.all()

    def list(self, request):
        serializer = self.serializer_class(
            self.queryset, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        print(request.data)
        serializer = PortfolioCreateSerializer(data=request.data)
        serializer.is_valid()
        self.perform_create(serializer)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_create(self, serializer):
        # here you will send `created_by` in the `validated_data`
        serializer.save(profile=self.request.user.profile)

        # @api_view(['GET', 'POST'])
        # def run_script_isr(request):
        #     scraper = IsraeliPaperScraper()
        #     print('running script')
        #     scraper.scrape_to_database()
        #     return Response({'status': 'ended script'})

        # @api_view(['GET', 'POST'])
        # def run_script_us(request):
        #     scraper = USPapersScraper()
        #     print('running us script')
        #     scraper.scrape_to_database()
        #     return Response({'status': 'ended us script'})

        # @api_view(['GET', 'POST'])
        # def run_script_crypto(request):
        #     scraper = USPapersScraper()
        #     print('running crypto script')
        #     scraper.scrape_cryptos_to_database()
        #     return Response({'status': 'ended crypto script'})
