import datetime
from datetime import timedelta
from .models import Portfolio, PortfolioRecord, PortfolioAction, \
    Asset, AssetRecord, ExchangeRate


def calculate_portfolio_records(portfolio_id, action_pks, record_pks_to_delete):
    exchange_rate = ExchangeRate.objects.get(from_currency="ILS").rate
    portfolio = Portfolio.objects.get(id=portfolio_id)
    actions = PortfolioAction.objects.filter(pk__in=action_pks)
    dates_delta = (datetime.date.today() - portfolio.started_at).days
    portfolio_records = []
    asset_quantities = {}
    # Iterate through all dates between the portfolio
    # started_at date (set as first record completion date)
    # till today.
    for i in range(dates_delta + 1):
        curr_date = portfolio.started_at + timedelta(i)
        new_actions = actions.filter(completed_at=curr_date)
        #  add new holding if a new Action is found
        # { Asset : Quantity } Dictionary
        if new_actions.count() > 0:
            for action in new_actions:
                is_buy = 1 if action.type == 'BUY' else -1
                # Sum/substract the quantity of shares
                if action.asset in asset_quantities:
                    asset_quantities[action.asset] += is_buy * \
                        action.quantity
                else:
                    asset_quantities[action.asset] = is_buy * \
                        action.quantity
        portfolio_records.append(get_record_at_date(portfolio,
                                                    asset_quantities,
                                                    curr_date,
                                                    exchange_rate))
    if record_pks_to_delete:
        PortfolioRecord.objects.filter(
            pk__in=record_pks_to_delete).delete()
    PortfolioRecord.objects.bulk_create(portfolio_records)

    portfolio.started_at = portfolio.actions.first().completed_at
    portfolio.save()


def get_record_at_date(portfolio, asset_quantities, curr_date, exchange_rate):
    '''
    Sums and returns a portfolio record with the
    total value of the portfolio are the curretn date.
    '''
    price = 0

    for asset, quantity in asset_quantities.items():
        asset_obj = Asset.objects.get_subclass(id=asset.id)
        # try to get the AssetRecord with the same date
        # except if not found
        asset_record = AssetRecord.objects.filter(
            asset=asset,
            date__lt=curr_date).last()
        exchange_rate = exchange_rate if asset_obj.currency == "ILS" else 1
        # add the asset_price * quantity to the total value
        # of the portfolio at the curr_date
        asset_obj = Asset.objects.get_subclass(id=asset.id)
        price += asset_record.price * \
            quantity / exchange_rate
    return PortfolioRecord(
        portfolio=portfolio, date=curr_date, price=price)
