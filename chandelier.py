
import ccxt
import talib
import numpy as np
import time
from talib.abstract import *
import pandas_ta
import datetime
import pandas as pd

# 거래소 객체를 생성합니다.
exchange = ccxt.kucoin({
    'apiKey': '',
    'secret': '',
    'password': '',
    'enableRateLimit': True,
    'rateLimit': 1000,
    'options': {
        'createMarketBuyOrderRequiresPrice': False,
        'fetchOHLCVWarning': False,
    }
})

# 매매 대상 코인의 심볼을 설정합니다.
symbol = 'BTC/USDT'

# chandelier exit strategy에 사용되는 변수를 초기화합니다.
period = 14
multiplier = 2
timeframe = '15m'

longStopPrev = 0.0
shortStopPrev = 0.0
dirPrev = -1  # 올라갈떄는 1 내려갈떄는 -1
closePrev = -1

while True:
    try:
        # Millisecond time of one day ago
        since = round(time.time() * 1000) - 86400000

        # Fetch the OHLCV data
        ohlcv = exchange.fetch_ohlcv(symbol=symbol, timeframe=timeframe, limit=period) 

        # 히스토리 데이터에서 각 값에 해당하는 배열을 추출합니다.
        high = np.array([ohlcv[i][2] for i in range(period)])
        low = np.array([ohlcv[i][3] for i in range(period)])
        closes = np.array([ohlcv[i][4] for i in range(period)])

        # Find the highest price
        highest_price = max(closes)

        # Calculate the lowest price
        lowest_price = min(closes) 

        # chandelier exit strategy 계산을 위한 ATR값을 구합니다.
        atr = ATR(high, low, closes, timeperiod=period-1)[-1]
            
        longStop = highest_price - multiplier * atr 

        if closePrev == -1:
            closePrev = closes[-1]
                
        if longStopPrev == 0.0:
            longStopPrev = longStop

        if closePrev > longStopPrev and longStopPrev > longStop:
            longStop = longStopPrev

        shortStop = lowest_price + multiplier * atr

        if shortStopPrev == 0.0:
            shortStopPrev = shortStop

        if closePrev < shortStopPrev and shortStopPrev < shortStop:
            shortStop = shortStopPrev     
        
        dir = dirPrev
        if closes[-1] > shortStopPrev:
            dir = 1
        elif closes[-1] < longStopPrev:
            dir = -1

        buySignal = dir == 1 and dirPrev == -1
        sellSignal = dir == -1 and dirPrev == 1
        changeCond = dir != dirPrev

        if buySignal: print("buying")

        if sellSignal: print("selling!")

        if changeCond: print("changing direction!")

        if buySignal or sellSignal or changeCond:
            print(closes[-1])
            print(datetime.datetime.now())

        dirPrev = dir
        shortStopPrev = shortStop
        longStopPrev = longStop
        closePrev = closes[-1]
 
        # 현재 잔고를 업데이트합니다.
        balance = exchange.fetch_balance()['USDT']['free']

        btc_balance = exchange.fetch_balance()['BTC']['free']

        # 매수 또는 매도합니다.

        ticker = exchange.fetch_ticker(symbol)
        close = ticker['last']

        if buySignal and balance >= 1:
            amount = balance / close
            exchange.create_market_buy_order(symbol, amount)
            buy_price = close
            print(f"Buy: {buy_price:.2f}")
            # 현재 포지션과 잔고를 출력합니다.
            print('USDT:', balance)
            print(f"현재 보유중인 BTC 수량: {btc_balance:.8f}")
        elif sellSignal and btc_balance >= 1:
            exchange.create_market_sell_order(symbol, btc_balance)
            sell_price = close
            print(f"Sell: {sell_price:.2f}")
            profit = (sell_price - buy_price) / buy_price * 100
            print(f"Profit/loss: {profit:.2f}%")

        time.sleep(60)
    except Exception as e:
        print(e)


