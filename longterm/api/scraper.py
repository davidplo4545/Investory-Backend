#!/usr/bin/env python
# -*- coding: utf-8 -*-
from api.models import AssetRecord, Crypto, IsraelPaper, USPaper,\
    Portfolio, PortfolioRecord, Holding
import django
from dateutil import parser
from dateutil.parser import parse
import datetime
import yfinance as yf
from pathlib import Path
import requests
import csv
import os
import sys
import json
import threading
from django.utils import timezone

DIR_PATH = os.path.join(
    'C:\\Users\\David\\Desktop\\Projects\\Long-Term\\longterm\\longterm', 'media')


class IsraeliPaperScraper:
    def __init__(self):
        self.conversion_rate = 3.25
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
                data_points[0]['C_p']) / 100.0 / self.conversion_rate
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
                paper.type = 'stock'
                paper.symbol = symbol

            paper.name = name
            paper.paper_id = paper_id
            records = []
            if data_points:
                paper.last_price = float(
                    data_points[0]['C_p']) / 100.0 / self.conversion_rate
                paper.last_updated = timezone.now()
                # creates list of AssetRecord objects
                for point in data_points:
                    date = point['D_p']
                    date = datetime.datetime.strptime(date, '%d/%m/%Y')
                    record = AssetRecord(
                        asset=paper, date=date, price=float(point['C_p']) / 100.0 / self.conversion_rate)
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
        for paper in self.papers_data:
            if len(paper) > 0:
                if paper[0] is not None:
                    paper[0].save()
                if len(paper[1]) > 0:
                    records += paper[1]

        AssetRecord.objects.bulk_create(records)

        print('Israeli Scraper ended his work.')


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
            print(f'{ticker} is done.')
        print(f'thread done running')

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
        for paper in self.papers_data:
            if len(paper) > 0:
                if paper[0] is not None:
                    try:
                        paper[0].save()
                    except:
                        is_paper = False
                if is_paper:
                    if len(paper[1]) > 0:
                        create_records += paper[1]
                    if len(paper[2]) > 0:
                        for record in paper[2]:
                            record.save()
                is_paper = True
        AssetRecord.objects.bulk_create(create_records)

        print('US Scraper ended his work.')

    def scrape_stock(self, ticker):
        stock_df = []
        symbol = ticker.upper()
        ticker = yf.Ticker(ticker)
        ticker_info = ticker.info
        # end-case if quoteType does is not found
        if 'quoteType' not in ticker_info or 'longName' not in ticker_info:
            print(f'{symbol} quote type not found {ticker_info}')
            return (None, [], [])

        quote_type = 'stock' if ticker_info['quoteType'] == 'EQUITY' else 'etf'
        sector = ticker_info['sector'] if 'sector' in ticker_info else None
        industry = ticker_info['industry'] if 'industry' in ticker_info else None
        name = ticker_info['longName']
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
                print(f'{symbol} Updating old record')
                return (paper, [], [last_db_record])
            except:
                print(f'{symbol} Creating new record')
                # creates a new record with a new price and date
                new_record = AssetRecord(
                    asset=paper, date=parse(last_date), price=last_price)
                paper.last_price = last_price
                paper.last_updated = timezone.now()
                return (paper, [], [new_record])
        except:
            paper = USPaper()
            paper.type = quote_type
            paper.name = name
            paper.symbol = symbol
            paper.sector = sector
            paper.industry = industry
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
            print(f'Scraping Crypto {crypto}')
            # check if ticker already exists in database
            try:
                crypto_obj = Crypto.objects.get(symbol=crypto)
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
                crypto_obj.symbol = crypto
                crypto_obj.name = crypto_info['name']
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
                print(f'crypto {crypto} saved')
                AssetRecord.objects.bulk_create(records)
                print(f'crypto {crypto} saved records')


class Updater:
    def get_all_portfolios(self):
        return Portfolio.objects.all()

    def update_all_portfolios(self):
        for portfolio in self.get_all_portfolios():
            self.update_portfolio(portfolio)

    def update_portfolio(self, portfolio):
        holdings = portfolio.holdings.all()
        total_value = 0
        total_cost = 0
        if holdings.count() > 0:
            for holding in holdings:
                # calculate the total_value of the holdings and
                # add it to the total portfolio value
                holding.total_value = holding.calculate_total_value()
                total_value += holding.total_value
                holding.save()

        actions = portfolio.actions.all()
        if actions.count() > 0:
            for action in actions:
                if action.type == "SELL":
                    total_cost -= action.total_cost
                else:
                    total_cost += action.total_cost

        portfolio.total_value = total_value
        portfolio.total_cost = total_cost
        portfolio.save()

        # Update/Create last record
        try:
            last_record = PortfolioRecord.objects.get(
                portfolio=portfolio, date=datetime.date.today())
            last_record.price = portfolio.total_value
            last_record.save()
        except:
            new_record = PortfolioRecord()
            new_record.portfolio = portfolio
            new_record.date = datetime.date.today()
            new_record.price = portfolio.total_value
            new_record.save()
