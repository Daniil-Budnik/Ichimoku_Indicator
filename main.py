import pandas as pd
from datetime import datetime, timedelta
import matplotlib.ticker as ticker
import matplotlib.dates as mdates
from mpl_finance import candlestick_ohlc
import matplotlib.pyplot as plt
import numpy as np
import decimal
import math as mt

# Индикатор Ишимоку 
def Ichimoku(ohcl_df):

    tenkan_window = 20
    kijun_window = 60
    senkou_span_b_window = 120
    cloud_displacement = 30
    chikou_shift = -30

    # Даты с плавающей точкой в mdates, например, 736740.0	 
    # # Период - это разница двух последних дат
    last_date = ohcl_df["Date"].iloc[-1]
    period = last_date - ohcl_df["Date"].iloc[-2]

    # Добавить строки для сдвига на N периодов (cloud_displacement)
    ext_beginning = decimal.Decimal(last_date+period)
    ext_end = decimal.Decimal(last_date + ((period*cloud_displacement)+period))

    dates_ext = list(Drange(ext_beginning, ext_end, str(period)))
    dates_ext_df = pd.DataFrame({"Date": dates_ext})
    dates_ext_df.index = dates_ext                              

    ohcl_df = ohcl_df.append(dates_ext_df)

    # Tenkan 
    tenkan_sen_high = ohcl_df['High'].rolling( window=tenkan_window ).max()
    tenkan_sen_low = ohcl_df['Low'].rolling( window=tenkan_window ).min()
    ohcl_df['tenkan_sen'] = (tenkan_sen_high + tenkan_sen_low) /2

    # Kijun 
    kijun_sen_high = ohcl_df['High'].rolling( window=kijun_window ).max()
    kijun_sen_low = ohcl_df['Low'].rolling( window=kijun_window ).min()
    ohcl_df['kijun_sen'] = (kijun_sen_high + kijun_sen_low) / 2

    # Senkou Span A 
    ohcl_df['senkou_span_a'] = ((ohcl_df['tenkan_sen'] + ohcl_df['kijun_sen']) / 2).shift(cloud_displacement)

    # Senkou Span B 
    senkou_span_b_high = ohcl_df['High'].rolling( window=senkou_span_b_window ).max()
    senkou_span_b_low = ohcl_df['Low'].rolling( window=senkou_span_b_window ).min()
    ohcl_df['senkou_span_b'] = ((senkou_span_b_high + senkou_span_b_low) / 2).shift(cloud_displacement)

    # Chikou
    ohcl_df['chikou_span'] = ohcl_df['Close'].shift(chikou_shift)

    return ohcl_df


# Генератор диапазонов для десятичных знаков
def Drange(x, y, jump): 
    while x < y:
        yield float(x)
        x += decimal.Decimal(jump)

# Модификатор
def Operator(Mx,My):

    # Проверка от левых данных
    Xs, Ys = [], []
    for i in Mx: 
        if(mt.isnan(My[i]) != True):
            Xs.append(i)
            Ys.append(My[i])

    # Масштабируем сигнал от 0 до Pi
    Xpi = np.linspace(0,np.pi,len(Xs))

    # Метод для конвертации массива данных в функцию от 0 до pi
    def F(x, E=0.005): 
        Nm = 0
        for k in Xpi: 
            if(abs(k-x) < E): return Ys[Nm] 
            Nm += 1

    # Синк функция
    def S(k, x, n = 100): return ( ((-1)**k) * np.sin(n*x) ) / ( n * x - k * np.pi )

    # Функцию разделил на условные блоки (чтобы не запутаться)
    def DF1(k): return ( ( F(Xpi[k+1]) + F(Xpi[k]) ) / 2 )
    def DF2():  return ( (F(np.pi) - F(0)) / np.pi )
    def DF3(k): return ( ( Xpi[k+1] + Xpi[k] ) / 2 )

    # Функция модификатор (5.36)
    def ATh(F,x):
        AT = 0 
        for k in range(0,len(Xpi)-1): AT += ( DF1(k) - ( DF2() * DF3(k) ) - F(0) ) * S(k,x) 
        return AT + (DF2()*x) + F(0)

    return {"X" : Xs, "Y" : [ATh(F,x) for x in Xpi]}

# Главный метод
if __name__ == "__main__":    
    
    # Используем индикатор
    Ichi = Ichimoku(pd.read_csv('./data.csv',index_col=0)) 
    fig, ax = plt.subplots()    

    # Данные о графике
    plt.title("Ишимоку")
    plt.xlabel('Данные')
    plt.ylabel('Цена (BTC)')

    # Получение данных Ишимоку
    d2 = Ichi.loc[:, ['tenkan_sen','kijun_sen','senkou_span_a','senkou_span_b', 'chikou_span']]
    d2 = d2.tail(100)
    date_axis = d2.index.values

    # Получаем тренды
    candlesticks_df = Ichi.loc[:, ['Date','Open','High','Low', 'Close']]
    candlesticks_df = candlesticks_df.tail(100)
    
    # Ишимоку
    plt.plot(date_axis, d2['tenkan_sen'], label="Tenkan", color='#0496ff')
    plt.plot(date_axis, d2['kijun_sen'], label="Kijun", color="#991515")
    plt.plot(date_axis, d2['senkou_span_a'], label="Span A", color="#008000")
    plt.plot(date_axis, d2['senkou_span_b'], label="Span B", color="#ff0000")
    plt.plot(date_axis, d2['chikou_span'], label="Chikou", color="#000000")
    
    # Просветы при повышении и понижении (зелёный и красный)
    ax.fill_between(date_axis, d2['senkou_span_a'], d2['senkou_span_b'], where=d2['senkou_span_a']> d2['senkou_span_b'], facecolor='#008000', interpolate=True, alpha=0.25)
    ax.fill_between(date_axis, d2['senkou_span_a'], d2['senkou_span_b'], where=d2['senkou_span_b']> d2['senkou_span_a'], facecolor='#ff0000', interpolate=True, alpha=0.25)
        
    # Рисуем тренды
    candlestick_ohlc(ax, candlesticks_df.values, width=0.6, colorup='#83b987', colordown='#eb4d5c', alpha=0.5 )

    # Ишимоку
    oXY = Operator(date_axis,d2['tenkan_sen'])
    plt.plot(oXY["X"],oXY["Y"], 'o',label="Tenkan Mod", color='#0496ff')

    oXY = Operator(date_axis,d2['kijun_sen'])
    plt.plot(oXY["X"],oXY["Y"], 'o', label="Kijun Mod", color="#991515")
    
    oXY = Operator(date_axis,d2['senkou_span_a'])
    plt.plot(oXY["X"],oXY["Y"],'o', label="Span A Mod", color="#008000")
    
    oXY = Operator(date_axis,d2['senkou_span_b'])
    plt.plot(oXY["X"],oXY["Y"], 'o', label="Span B Mod", color="#ff0000")
    
    oXY = Operator(date_axis,d2['chikou_span'])
    plt.plot(oXY["X"],oXY["Y"],'o',label="Chikou Mod", color="#000000")


    # Различные настройки
    ax.legend()
    ax.grid(linestyle='-', linewidth='0.5')
    ax.yaxis.tick_right()
    ax.set_yscale("log", nonposy='clip')
    ax.autoscale_view()
    ax.tick_params(axis='x', size=7)
    ax.tick_params(axis='y', size=7)
    fig.tight_layout()

    # Рисуем
    plt.show()                                           
