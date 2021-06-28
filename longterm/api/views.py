from django.shortcuts import render

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .scraper import IsraeliPaperScraper, USPapersScraper


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


@api_view(['GET', 'POST'])
def run_script_crypto(request):
    scraper = USPapersScraper()
    print('running crypto script')
    scraper.scrape_cryptos_to_database()
    return Response({'status': 'ended crypto script'})
