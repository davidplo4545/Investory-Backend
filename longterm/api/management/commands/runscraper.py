from django.core.management.base import BaseCommand, CommandError
from api.scraper import USPapersScraper, IsraeliPaperScraper, Updater
from api.models import AssetRecord, USPaper


class Command(BaseCommand):
    help = 'Scraping all assets.'

    def handle(self, *args, **options):
        us_scraper = USPapersScraper()
        # scrape us stocks
        # print('Scraping us stocks')
        # us_scraper.scrape_to_database()

        isr_scraper = IsraeliPaperScraper()

        print('Scraping israeli stocks')
        # scrape israeli stocks
        isr_scraper.scrape_to_database()

        print('Scraping cryptos')
        # scrape crypto
        us_scraper.scrape_cryptos_to_database()
        self.stdout.write(self.style.SUCCESS(
            'Successfully finished running scraper'))
