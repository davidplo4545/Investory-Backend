from django.core.management.base import BaseCommand, CommandError
from api.scraper import USPapersScraper, IsraeliPaperScraper, Updater
from api.models import Asset, Portfolio


class Command(BaseCommand):
    help = 'Deleting portfolios and assets data.'

    def handle(self, *args, **options):
        Asset.objects.all().delete()
        Portfolio.objects.all().delete()

        self.stdout.write(self.style.SUCCESS(
            'Successfully deleted portfolios and assets data.'))
