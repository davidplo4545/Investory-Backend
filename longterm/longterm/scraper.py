#!/usr/bin/env python
# -*- coding: utf-8 -*-
from dateutil import parser
from dateutil.parser import parse
from datetime import datetime
import yfinance as yf
from pathlib import Path
import requests
import csv
import os
import json
import threading

DIR_PATH = os.path.join(Path(__file__).parent.absolute(), 'media')


def scrape_maya():
    url = 'https://mayaapi.tase.co.il/api/fund/history'

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36',
        'X-Maya-With': 'allow'}
    payload = {'DateFrom': '2021-04-25T21:00:00.000Z',
               'DateTo': '2021-05-25T21:00:00.000Z', 'FundId': '5122627', 'Page': 6, 'Period': 7}

    r = requests.post(url, headers=headers, data=payload)
    print(r.json())


class IsraeliPaperScraper:
    def __init__(self):
        self.json_result = []
        self.isr_stocks_csv_path = os.path.join(DIR_PATH, 'isr_papers.csv')

    def scrape_stock(self, name, symbol, paper_id, paper_type, period='fiveyearly'):
        # period options : fiveyearly, yearly,
        # https://www.bizportal.co.il/forex/quote/ajaxrequests/paperdatagraphjson?period=fiveyearly&paperID=5122627
        url = f'https://www.bizportal.co.il/forex/quote/ajaxrequests/paperdatagraphjson?period={period}&paperID={paper_id}'

        HEADER = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36'}
        r = requests.get(url, headers=HEADER)
        data_points = r.json()['points']
        name = name.replace('"', '')
        paper_dict = {'type': '',
                      'name': '',
                      'symbol': '',
                      'data_points': []}

        if paper_type == 'ETF':
            paper_dict['type'] = 'etf'
            paper_dict['symbol'] = None
        else:
            paper_dict['type'] = 'stock'
            paper_dict['symbol'] = symbol

        paper_dict['name'] = name
        paper_dict['id'] = paper_id

        for point in data_points:
            data_point = {'date': point['D_p'], 'price': point['C_p']}
            paper_dict['data_points'].append(data_point)
        return paper_dict

    def scrape_stock_from_id(self, paper_id, period='fiveyearly'):
        # period options : fiveyearly, yearly,
        # https://www.bizportal.co.il/forex/quote/ajaxrequests/paperdatagraphjson?period=fiveyearly&paperID=5122627
        url = f'https://www.bizportal.co.il/forex/quote/ajaxrequests/paperdatagraphjson?period={period}&paperID={paper_id}'

        paper_dict = {'type': '',
                      'name': '',
                      'symbol': '',
                      'data_points': []}

        # find paper data inside the csv file
        with open(self.isr_stocks_csv_path, encoding='utf8') as csv_file:
            csv_reader = csv.reader(csv_file)
            rows = (list(csv_reader))
            for row in rows:
                if row[2] == str(paper_id):
                    paper_type = row[3]
                    name = row[0]
                    symbol = row[1]
                    break

        HEADER = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36'}
        r = requests.get(url, headers=HEADER)

        data_points = r.json()['points']
        name = name.replace('"', '')

        if paper_type == 'ETF':
            paper_dict['type'] = 'etf'
            paper_dict['symbol'] = None
        else:
            paper_dict['type'] = 'stock'
            paper_dict['symbol'] = symbol

        paper_dict['name'] = name
        paper_dict['id'] = paper_id

        for point in data_points:
            data_point = {'date': point['D_p'], 'price': point['C_p']}
            paper_dict['data_points'].append(data_point)

        file_path = os.path.join(DIR_PATH, f'{paper_id}.json')
        with open(file_path, mode='w', newline='', encoding='utf8') as json_file:
            json.dump(paper_dict, json_file)

    def scrape_isr_papers(self, stocks_data, thread_id):
        for row in stocks_data:
            name, symbol, paper_id, paper_type = (
                row[0], row[1][::-1], row[2], row[3])
            self.json_result.append(self.scrape_stock(
                name, symbol, paper_id, paper_type))

    def scrape_all(self):
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
                                     args=(scraping_rows, i + 1,))
                threads.append(x)
                x.start()
            for thread in threads:
                thread.join()

        file_path = os.path.join(DIR_PATH, 'isr_stocks.json')
        with open(file_path, mode='w', newline='', encoding='utf8') as json_file:
            json.dump(self.json_result, json_file)


class USPapersScraper:
    def __init__(self):
        self.json_result = []
        self.cryptos = ['BTC', 'ETH', 'ADA', 'DOGE', 'LTC']

    def scrape_all(self):
        file_path = os.path.join(DIR_PATH, 'us_popular.csv')
        # read symbols to scrape (currently only the ones I've chosen)
        with open(file_path, encoding="utf8") as csv_file:
            csv_reader = csv.reader(csv_file)
            rows = (list(csv_reader))[1:]
        i = 1
        for row in rows:
            symbol = row[0]
            stock_df = []
            stock_df = yf.download(symbol, period='5y', progress=False)
            if len(stock_df) == 0:
                print(None)
            else:
                # remove columns from pandas.DataFrame
                stock_df = stock_df.drop(
                    columns=['Volume', 'High', 'Low', 'Open', 'Adj Close'])
                i += 1
                stock_json = stock_df.to_json(date_format='iso')
                stock_json = json.loads(stock_json)
                stock_json['type'] = row[8]
                stock_json['symbol'] = symbol
                stock_json['sector'] = row[6]
                stock_json['industry'] = row[7]
                stock_json['name'] = row[1]
                self.json_result.append(stock_json)
                print(f'stock number {i} done')

        # dump data to a json file
        file_path = os.path.join(DIR_PATH, 'us_stocks.json')
        with open(file_path, mode='w', newline='', encoding='utf8') as json_file:
            json.dump(self.json_result, json_file)

    def scrape_stock(self, ticker):
        stock_df = []
        symbol = ticker.upper()
        try:
            ticker = yf.Ticker(ticker)
            ticker_info = ticker.info
            print(ticker_info)
            print(ticker_info['quoteType'])
            quote_type = 'stock' if ticker_info['quoteType'] == 'EQUITY' else 'etf'

            sector = ticker_info['sector'] if 'sector' in ticker_info else ''
            industry = ticker_info['industry'] if 'industry' in ticker_info else ''
            name = ticker_info['longName']
            stock_df = ticker.history(period="5y")
        except:
            print(f'Ticker: {symbol} does not exist')
            return

        if len(stock_df) == 0:
            print(None)
        else:
            # remove columns from pandas.DataFrame
            stock_df = stock_df.drop(
                columns=['Volume', 'High', 'Low', 'Open', 'Dividends', 'Stock Splits'])
            stock_json = stock_df.to_json(date_format='iso')
            stock_json = json.loads(stock_json)
            stock_json['type'] = quote_type
            stock_json['symbol'] = symbol
            stock_json['sector'] = sector
            stock_json['industry'] = industry
            stock_json['name'] = name
            self.json_result.append(stock_json)
            print(f'stock {symbol} done')

        # dump data to a json file
        file_path = os.path.join(DIR_PATH, f'{symbol}.json')
        with open(file_path, mode='w', newline='', encoding='utf8') as json_file:
            json.dump(self.json_result, json_file)

    def scrape_cryptos(self):
        i = 1
        for crypto in self.cryptos:
            crypto_df = []
            yf_crypto = yf.Ticker(f'{crypto}-USD')
            crypto_info = yf_crypto.info
            crypto_df = yf_crypto.history(period='5y')
            if len(crypto_df) == 0:
                print(None)
            else:
                # remove columns from pandas.DataFrame
                crypto_df = crypto_df.drop(
                    columns=['Volume', 'High', 'Low', 'Open', 'Dividends', 'Stock Splits'])
                i += 1
                crypto_json = crypto_df.to_json(date_format='iso')
                crypto_json = json.loads(crypto_json)
                crypto_json['type'] = crypto_info['quoteType'].lower()
                crypto_json['symbol'] = crypto
                crypto_json['name'] = crypto_info['name']
                self.json_result.append(crypto_json)
                print(f'crypto {crypto} done')

        # dump data to a json file
        file_path = os.path.join(DIR_PATH, 'cryptos.json')
        with open(file_path, mode='w', newline='', encoding='utf8') as json_file:
            json.dump(self.json_result, json_file)


# scraper = IsraeliPaperScraper()
# scraper.scrape_all()

# print('done israeli')
scraper = USPapersScraper()
scraper.scrape_stock('aal')
# scraper.scrape_all()

# scraper.scrape_cryptos()
