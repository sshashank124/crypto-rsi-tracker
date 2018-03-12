from binance.client import Client
import numpy as np
import pandas as pd
import smtplib
import time
import yaml

CONFIG = yaml.load(open('./CONFIG.yml'))

API_KEY = CONFIG['binance_api']['key']
API_SECRET = CONFIG['binance_api']['secret']
user = CONFIG['gmail']['user']
passwd = CONFIG['gmail']['password']

client = Client(API_KEY, API_SECRET)

# against ETH
SYMBOLS = ('ADA', 'ADX', 'BAT', 'BCC', 'DASH', 'EOS', 'IOTA',
        'LTC', 'NEO', 'OMG', 'STORJ', 'XLM', 'NANO', 'XRP', 'XVG', 'ZEC')
RSI_N = 14
RSI_THRESHOLD = 8
RUN_INTERVAL_MINS = 30

def send_email(rsi_values):
    if len(rsi_values) > 0:

        message = '\n'.join('{0:>8} {1:.2f}'.format(symbol, rsi) for (symbol, rsi) in rsi_values)
        email_text = 'From: {0}\nTo: {1}\nSubject: Stock Recommendations\n\n{2}'.format(user, user, message)
        try:
            server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
            server.ehlo()
            server.login(user, passwd)
            server.sendmail(user, user, email_text)
            server.close()
        except:
            pass


while True:
    rsi_values = []
    for SYMBOL in SYMBOLS:
        klines = client.get_historical_klines(SYMBOL + 'ETH', Client.KLINE_INTERVAL_30MINUTE, '{} hours ago UTC'.format((RSI_N + 3) // 2))
        closings = np.asarray(klines, dtype=np.float)[-RSI_N - 1:, 4]

        diffs = np.diff(closings)
        ups = diffs.clip(min=0)
        downs = diffs.clip(max=0)
        ups_avg = pd.ewma(ups, span=RSI_N)[-1]
        downs_avg = -pd.ewma(downs, span=RSI_N)[-1]
        rs = ups_avg / downs_avg
        rsi = 100 - 100 / (1 + rs)
        
        rsi_values.append((SYMBOL, rsi))

    print('\n'.join('{0:>8} {1:.2f}'.format(symbol, rsi) for (symbol, rsi) in rsi_values))
    rsi_values = list(filter(lambda x: x[1] < RSI_THRESHOLD, rsi_values))

    send_email(rsi_values)

    time.sleep(60 * RUN_INTERVAL_MINS)
