from django.core.management.base import BaseCommand, CommandError
from api.scraper import USPapersScraper, IsraeliPaperScraper, Updater
from api.models import Asset, Portfolio, PortfolioComparison


class Command(BaseCommand):
    help = 'Deleting compared asset portfolios data.'

    def handle(self, *args, **options):
        asset_portfolios = Portfolio.objects.filter(profile=None)
        asset_portfolios.delete()

        self.stdout.write(self.style.SUCCESS(
            'Successfully deleted compared asset portfolios data.'))
