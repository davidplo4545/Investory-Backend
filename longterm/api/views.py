from django.shortcuts import render

from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Asset, IsraelPaper, USPaper, Crypto, AssetRecord
from .serializers import AssetSerializer
from .scraper import IsraeliPaperScraper, USPapersScraper


class AssetViewSet(viewsets.ViewSet):
    """
    A simple ViewSet for listing retreiving assets.
    """
    serializer_class = AssetSerializer
    queryset = Asset.objects.select_subclasses()

    def list(self, request):
        serializer = self.serializer_class(self.queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        paper = get_object_or_404(self.queryset, pk=pk)
        serializer = self.serializer_class(paper)
        return Response(serializer.data)


@api_view(['GET', 'POST'])
def run_script_isr(request):
    scraper = IsraeliPaperScraper()
    print('running script')
    scraper.scrape_to_database()
    return Response({'status': 'ended script'})


@api_view(['GET', 'POST'])
def run_script_us(request):
    scraper = USPapersScraper()
    print('running us script')
    scraper.scrape_to_database()
    return Response({'status': 'ended us script'})


# @api_view(['GET', 'POST'])
# def run_script_crypto(request):
#     scraper = USPapersScraper()
#     print('running crypto script')
#     scraper.scrape_cryptos_to_database()
#     return Response({'status': 'ended crypto script'})
