from django.core.management.base import BaseCommand
from api.scraper import Updater


class Command(BaseCommand):
    help = 'Updating portfolios and portfolio records.'

    def handle(self, *args, **options):
        updater = Updater()
        updater.update_all_portfolios()
        self.stdout.write(self.style.SUCCESS(
            'Successfully updated portfolios data.'))
