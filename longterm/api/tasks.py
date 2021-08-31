from celery import shared_task
from .services import calculate_portfolio_records
from celery.utils.log import get_task_logger
from longterm.celery import app
logger = get_task_logger(__name__)


@app.task
def create_portfolio_records(portfolio_id, action_pks, record_pks_to_delete):
    logger.info(f'Created portfolio records.')
    calculate_portfolio_records(portfolio_id, action_pks, record_pks_to_delete)
    return {"status": "success"}
