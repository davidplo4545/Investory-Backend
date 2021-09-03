#!/usr/bin/env python
# -*- coding: utf-8 -*-
from api.models import AssetRecord, Crypto, ExchangeRate, IsraelPaper, USPaper,\
    Portfolio, PortfolioRecord, PortfolioComparison, Asset
import django
from dateutil import parser
from dateutil.parser import parse
import datetime
import yfinance as yf
from pathlib import Path
import requests
import csv
import os
import requests
from bs4 import BeautifulSoup
import json
import threading
from django.utils import timezone

DIR_PATH = os.path.join(
    'C:\\Users\\David\\Desktop\\Projects\\Long-Term\\longterm\\longterm', 'media')


class IsraeliPaperScraper:
    def __init__(self):
        self.papers_data = []
        self.isr_stocks_csv_path = os.path.join(DIR_PATH, 'isr_papers.csv')

    def scrape_stock(self, name, symbol, paper_id, paper_type, period='fiveyearly'):
        # period options : fiveyearly, yearly,
        # https://www.bizportal.co.il/forex/quote/ajaxrequests/paperdatagraphjson?period=fiveyearly&paperID=5122627
        url = f'https://www.bizportal.co.il/forex/quote/ajaxrequests/paperdatagraphjson?period={period}&paperID={paper_id}'

        HEADER = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36'}
        r = requests.get(url, headers=HEADER)
        data_points = r.json()['points']
        # check if paper exists in database
        try:
            paper = IsraelPaper.objects.get(paper_id=paper_id)
            last_date = datetime.datetime.strptime(
                data_points[0]['D_p'], '%d/%m/%Y')
            last_price = float(
                data_points[0]['C_p']) / 100.0
            # check if record exists already, create new one if it doesn't
            last_db_record = AssetRecord.objects.filter(
                date=last_date, asset=paper).count()
            # return empty tuple if there's no new record
            if last_db_record > 0:
                return ()
            new_record = AssetRecord(
                asset=paper, date=last_date, price=last_price)
            paper.last_price = last_price
            paper.last_updated = timezone.now()
            return (paper, [new_record])

        except:
            paper = IsraelPaper()
            name = name.replace('"', '')
            paper_dict = {'type': '',
                          'name': '',
                          'symbol': '',
                          'data_points': []}

            if paper_type == 'ETF':
                paper.type = 'ETF'
                paper.symbol = None
            else:
                paper.type = 'Stock'
                paper.symbol = symbol[::-1]

            paper.name = name
            paper.paper_id = paper_id
            records = []
            if data_points:
                paper.last_price = float(
                    data_points[0]['C_p']) / 100.0
                paper.last_updated = timezone.now()
                # creates list of AssetRecord objects
                for point in data_points:
                    date = point['D_p']
                    date = datetime.datetime.strptime(date, '%d/%m/%Y')
                    record = AssetRecord(
                        asset=paper, date=date, price=float(point['C_p']) / 100.0)
                    records.append(record)
            return (paper, records)

    def scrape_isr_papers(self, stocks_data):
        for row in stocks_data:
            name, symbol, paper_id, paper_type = (
                row[0], row[1][::-1], row[2], row[3])
            self.papers_data.append(self.scrape_stock(
                name, symbol, paper_id, paper_type))

    def scrape_to_database(self):
        with open(self.isr_stocks_csv_path, encoding='utf8') as csv_file:
            csv_reader = csv.reader(csv_file)
            rows = (list(csv_reader))
            if len(rows) % 100 == 0:
                threads_count = len(rows) // 100
            else:
                threads_count = len(rows) // 100 + 1

            threads = []
            for i in range(threads_count):
                if i == threads_count - 1:
                    scraping_rows = rows[i * 100:]
                else:
                    scraping_rows = rows[i * 100: (i + 1) * 100]
                x = threading.Thread(target=self.scrape_isr_papers,
                                     args=(scraping_rows,))
                threads.append(x)
                x.start()
            for thread in threads:
                thread.join()
        # save all the data into the database
        records = []
        verified_papers = []
        for paper in self.papers_data:
            if len(paper) > 0:
                if paper[0] is not None:
                    paper[0].save()
                    verified_papers.append(paper[0])
                if len(paper[1]) > 0:
                    records += paper[1]

        AssetRecord.objects.bulk_create(records)
        for paper in verified_papers:
            paper.calculate_returns()
            paper.save()

        # print('Israeli Scraper ended his work.')


class USPapersScraper:
    def __init__(self):
        self.papers_data = []
        self.isr_stocks_csv_path = os.path.join(DIR_PATH, 'us_papers.csv')
        self.cryptos = ['BTC', 'ETH', 'ADA', 'DOGE', 'LTC']

    def scrape_us_papers(self, stocks_data):
        for row in stocks_data:
            ticker = row[0]
            self.papers_data.append(self.scrape_stock(
                ticker))
        # print(f'thread done running')

    def scrape_to_database(self):
        with open(self.isr_stocks_csv_path, encoding='utf8') as csv_file:
            csv_reader = csv.reader(csv_file)
            rows = (list(csv_reader))
            if len(rows) % 50 == 0:
                threads_count = len(rows) // 50
            else:
                threads_count = len(rows) // 50 + 1

            threads = []
            for i in range(threads_count):
                if i == threads_count - 1:
                    scraping_rows = rows[i * 50:]
                else:
                    scraping_rows = rows[i * 50: (i + 1) * 50]
                x = threading.Thread(target=self.scrape_us_papers,
                                     args=(scraping_rows,))
                threads.append(x)
                x.start()
            for thread in threads:
                thread.join()
        # save all the data into the database
        # (ticker, bulk_create_records, solo_records)
        create_records = []
        is_paper = True
        verified_papers = []
        for paper in self.papers_data:
            if len(paper) > 0:
                if paper[0] is not None:
                    try:
                        paper[0].save()
                        verified_papers.append(paper[0])
                    except:
                        is_paper = False
                if is_paper:
                    if len(paper[1]) > 0:
                        create_records += paper[1]
                    if len(paper[2]) > 0:
                        for record in paper[2]:
                            try:
                                record.save()
                            except:
                                asset = Asset.objects.get_subclass(
                                    id=record.asset.id)
                                # print(f'WARNING: {asset.symbol} {record.date}')

                is_paper = True
        AssetRecord.objects.bulk_create(create_records)

        for paper in verified_papers:
            paper.calculate_returns()
            paper.save()

        # print('US Scraper ended his work.')

    def set_uspaper_data(self, paper, symbol, ticker_info):
        paper.type = 'Stock' if ticker_info['quoteType'] == 'EQUITY' else 'Etf'
        paper.name = ticker_info['longName']
        paper.symbol = symbol
        paper.sector = ticker_info['sector'] if 'sector' in ticker_info else None
        paper.industry = ticker_info['industry'] if 'industry' in ticker_info else None
        paper.market_cap = ticker_info['marketCap'] if 'marketCap' in ticker_info else None
        paper.business_summary = ticker_info['longBusinessSummary'] if 'longBusinessSummary' in ticker_info else None
        paper.website_url = ticker_info['website'] if 'website' in ticker_info else None
        paper.logo_url = ticker_info['logo_url'] if 'logo_url' in ticker_info else None
        paper.fulltime_employees = ticker_info['fullTimeEmployees'] if 'fullTimeEmployees' in ticker_info else None
        paper.one_year_high = ticker_info['fiftyTwoWeekHigh'] if 'fiftyTwoWeekHigh' in ticker_info else None
        paper.one_year_low = ticker_info['fiftyTwoWeekLow'] if 'fiftyTwoWeekLow' in ticker_info else None
        paper.enterprise_value = ticker_info['enterpriseValue'] if 'enterpriseValue' in ticker_info else None
        paper.book_value = ticker_info['bookValue'] if 'bookValue' in ticker_info else None
        paper.price_to_book = ticker_info['priceToBook'] if 'priceToBook' in ticker_info else None
        paper.current_ratio = ticker_info['currentRatio'] if 'currentRatio' in ticker_info else None
        paper.trailing_pe = ticker_info['trailingPE'] if 'trailingPE' in ticker_info else None
        paper.forward_pe = ticker_info['forwardPE'] if 'forwardPE' in ticker_info else None
        paper.peg_ratio = ticker_info['pegRatio'] if 'pegRatio' in ticker_info else None
        paper.ps_ratio = ticker_info['priceToSalesTrailing12Months'] if 'priceToSalesTrailing12Months' in ticker_info else None
        paper.revenue_growth = ticker_info['revenueGrowth'] if 'revenueGrowth' in ticker_info else None
        paper.num_of_analysts = ticker_info['numberOfAnalystOpinions'] if 'numberOfAnalystOpinions' in ticker_info else None
        paper.mean_analyst_price = ticker_info['targetMeanPrice'] if 'targetMeanPrice' in ticker_info else None
        return paper

    def set_crypto_data(self, crypto, symbol, crypto_info):
        crypto.name = crypto_info['name']
        crypto.description = crypto_info['description'] if 'description' in crypto_info else None
        crypto.market_cap = crypto_info['marketCap'] if 'marketCap' in crypto_info else None
        crypto.one_year_high = crypto_info['fiftyTwoWeekHigh'] if 'fiftyTwoWeekHigh' in crypto_info else None
        crypto.one_year_low = crypto_info['fiftyTwoWeekLow'] if 'fiftyTwoWeekLow' in crypto_info else None
        crypto.symbol = symbol
        return crypto

    def scrape_stock(self, ticker):
        stock_df = []
        symbol = ticker.upper()
        ticker = yf.Ticker(ticker)
        ticker_info = ticker.info
        # end-case if quoteType does is not found
        if 'quoteType' not in ticker_info or 'longName' not in ticker_info:
            # print(f'{symbol} quote type not found {ticker_info}')
            return (None, [], [])

        stock_df = ticker.history(period="5y")

        has_history = len(stock_df) != 0
        if has_history:
            # remove columns from pandas.DataFrame
            stock_df = stock_df.drop(
                columns=['Volume', 'High', 'Low', 'Open', 'Dividends', 'Stock Splits'])
            records_json = json.loads(stock_df.to_json(date_format='iso'))
        else:
            return (None, [], [])

        # check if ticker already exists in database
        try:
            paper = USPaper.objects.get(symbol=symbol)
            paper = self.set_uspaper_data(paper, symbol, ticker_info)
            last_date = list(records_json['Close'].keys())[-1]
            last_price = records_json['Close'][last_date]
            try:
                # check if record with same date already exists
                # and updates it if it does
                last_db_record = AssetRecord.objects.get(
                    asset=paper, date=parse(last_date))
                last_db_record.price = last_price
                paper.last_price = last_price
                paper.last_updated = timezone.now()
                # print(f'{symbol} Updating old record')
                return (paper, [], [last_db_record])
            except:
                # print(f'{symbol} Creating new record')
                # creates a new record with a new price and date
                new_record = AssetRecord(
                    asset=paper, date=parse(last_date), price=last_price)
                paper.last_price = last_price
                paper.last_updated = timezone.now()
                return (paper, [], [new_record])
        except:
            paper = USPaper()
            paper = self.set_uspaper_data(paper, symbol, ticker_info)
            records = []

            if has_history:
                data_points = records_json['Close']
                last_date = list(data_points.keys())[-1]
                last_price = data_points[last_date]
                paper.last_price = last_price
                paper.last_updated = timezone.now()
                for key, value in data_points.items():
                    try:
                        record = AssetRecord(
                            asset=paper, date=parse(key), price=float(value))
                        records.append(record)
                    except:
                        return (None, [], [])
            return (paper, records, [])

    def scrape_cryptos_to_database(self):
        i = 1
        for crypto in self.cryptos:
            crypto_df = []
            yf_crypto = yf.Ticker(f'{crypto}-USD')
            crypto_info = yf_crypto.info
            crypto_df = yf_crypto.history(period='5y')
            crypto_df = crypto_df.drop(
                columns=['Volume', 'High', 'Low', 'Open', 'Dividends', 'Stock Splits'])
            crypto_json = json.loads(crypto_df.to_json(date_format='iso'))
            data_points = crypto_json['Close']
            # check if ticker already exists in database
            try:
                crypto_obj = Crypto.objects.get(symbol=crypto)
                crypto_obj = self.set_crypto_data(
                    crypto_obj, crypto, crypto_info)
                last_date = list(data_points.keys())[-1]
                last_price = data_points[last_date]
                try:
                    # check if record with same date already exists
                    # and updates it if it does
                    last_db_record = AssetRecord.objects.get(
                        asset=crypto_obj, date=parse(last_date))
                    last_db_record.price = last_price
                    crypto_obj.last_price = last_price
                    crypto_obj.last_updated = timezone.now()
                    crypto_obj.save()
                    last_db_record.save()
                    continue
                except:
                    # creates a new record with a new price and date
                    new_record = AssetRecord(
                        asset=crypto_obj, date=parse(last_date), price=last_price)
                    crypto_obj.last_price = last_price
                    crypto_obj.last_updated = timezone.now()
                    crypto_obj.save()
                    new_record.save()
                    continue
            except:
                crypto_obj = Crypto()
                crypto_obj = self.set_crypto_data(
                    crypto_obj, crypto, crypto_info)
                records = []

                last_date = list(data_points.keys())[-1]
                last_price = data_points[last_date]
                crypto_obj.last_price = last_price
                crypto_obj.last_updated = timezone.now()
                for key, value in data_points.items():
                    try:
                        record = AssetRecord(
                            asset=crypto_obj, date=parse(key), price=float(value))
                        records.append(record)
                    except:
                        break
                crypto_obj.save()
                AssetRecord.objects.bulk_create(records)
                crypto_obj.calculate_returns()
                crypto_obj.save()


class Updater:
    def get_all_portfolios(self):
        return Portfolio.objects.all()

    def update_all_portfolios(self):
        self.create_or_update_exchange_ratio()
        exchange_rate = ExchangeRate.objects.get(from_currency="ILS").rate
        for portfolio in self.get_all_portfolios():
            self.update_portfolio(portfolio, exchange_rate)

    def update_portfolio(self, portfolio, exchange_rate):
        holdings = portfolio.holdings.all()
        total_value = 0
        if holdings.count() > 0:
            for holding in holdings:
                asset = Asset.objects.get_subclass(id=holding.asset.id)
                exchange_rate = exchange_rate if asset.currency == "ILS" else 1
                # calculate the total_value of the holdings and
                # add it to the total portfolio value
                holding.total_value = holding.calculate_total_value()
                total_value += holding.total_value / exchange_rate
                holding.save()

        portfolio.total_value = total_value
        portfolio.save()

        # delete previous portfolio comparisons
        comparisons = PortfolioComparison.objects.filter(
            portfolio=portfolio).\
            values_list('asset_portfolio', flat=True)
        Portfolio.objects.filter(
            pk__in=list(comparisons)).delete()

        last_record, created = PortfolioRecord.objects.get_or_create(
            portfolio=portfolio, date=datetime.date.today(),
            defaults={'price': portfolio.total_value})
        last_record.save()

    def create_or_update_exchange_ratio(self):
        exchange_obj = ExchangeRate.objects.get_or_create(
            from_currency="ILS", to_currency="USD")[0]
        r = requests.get(
            'https://www.xe.com/currencyconverter/convert/?Amount=1&From=USD&To=ILS')
        soup = BeautifulSoup(r.content, 'html.parser')
        exchange_obj.rate = float(
            soup.find('p', {'class': 'iGrAod'}).text.split()[0])
        exchange_obj.save()
