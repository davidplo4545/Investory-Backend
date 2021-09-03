from celery import shared_task
from .services import calculate_portfolio_records
from celery.utils.log import get_task_logger
from longterm.celery import app
from api.models import Portfolio
from .scraper import USPapersScraper, IsraeliPaperScraper, Updater
logger = get_task_logger(__name__)

'''
Tasks for the 'default' queue (main worker)
'''


@app.task
def create_portfolio_records(portfolio_id, action_pks, record_pks_to_delete):
    calculate_portfolio_records(portfolio_id, action_pks, record_pks_to_delete)
    logger.info(f'Created portfolio records.')


'''
Tasks for the 'scraper' queue (period tasks worker)
'''


@app.task
def scrape_us_stocks():
    us_scraper = USPapersScraper()
    # scrape us stocks and cryptos
    us_scraper.scrape_to_database()
    us_scraper.scrape_cryptos_to_database()
    return "Successfuly finished scraping (US)"


@app.task
def scrape_isr_stocks():
    isr_scraper = IsraeliPaperScraper()
    # scrape israeli stocks
    isr_scraper.scrape_to_database()
    return "Successfuly finished scraping (ISR)"


@app.task
def update_portfolios():
    updater = Updater()
    updater.update_all_portfolios()
    return "Successfuly updated portfolios"
