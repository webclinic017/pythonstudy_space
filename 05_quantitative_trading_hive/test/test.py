import datetime
import multiprocessing
import os
import sys
import time
import random
import statsmodels.api as sm
from util.algorithmUtils import rps

curPath = os.path.abspath(os.path.dirname(__file__))
rootPath = os.path.split(curPath)[0]
sys.path.append(rootPath)
from bak.情绪数据源 import *
from util import btUtils
import warnings
from datetime import date
import talib as ta
import akshare as ak
import numpy as np
import pandas as pd
import backtrader as bt
import matplotlib.pyplot as plt
import plotly.express as px
from decimal import Decimal
from util.CommonUtils import get_spark
from tqdm import tqdm
from lxml import etree
import requests
import json
warnings.filterwarnings("ignore")
# 输出显示设置
pd.options.display.max_rows=None
pd.options.display.max_columns=None
pd.options.display.expand_frame_repr=False
pd.set_option('display.unicode.ambiguous_as_wide', True)
pd.set_option('display.unicode.east_asian_width', True)
#matplotlib中文显示设置
plt.rcParams['font.sans-serif']=['FangSong']   #中文仿宋
plt.rcParams['font.sans-serif']=['SimHei']     #用来正常显示中文标签
plt.rcParams['axes.unicode_minus']=False       #用来正常显示负号


# python /opt/code/pythonstudy_space/05_quantitative_trading_hive/test/test.py
if __name__ == '__main__':
    # 描述: 东方财富股票指数数据, 历史数据按日频率更新
    # 沪深300 000300
    # stock_zh_index_daily_df = ak.stock_zh_index_daily(symbol="sh000300")
    # print(stock_zh_index_daily_df)
    # df = ak.stock_a_lg_indicator(symbol='000609')
    # df = df[df['trade_date'] >= pd.to_datetime('20221226').date()]
    # print(df)
    # print(df.dtypes)
    #
    # a = Decimal(1.25)
    # b = 4.33
    # print(type(a))
    # print(type(Decimal(b)))
    #
    # df['total_mv'] = df['total_mv'].apply(lambda x: Decimal(x))
    # df['total_mv'] = df['total_mv'].astype(float)
    # # print(df.dtypes)
    # print(df.display())
    #
    # df2 = pd.DataFrame({"A": [Decimal(5.2), Decimal(5.2), Decimal(5.2), Decimal(5.2)],
    #                    "D": [5, 4, 2, 8]})
    # print(df2.dtypes)

    # df = ak.stock_tfp_em(date='20221130')
    # print(df)
    # t1 = pd.Timestamp('2019-01-10')
    # print(type(t1),t1)

    # print(pd.to_datetime('20221101').date().strftime('%Y%m%d')+'哈哈')
    # tock_zh_valuation_baidu_df = ak.stock_zh_valuation_baidu(symbol="600584", indicator="市盈率(TTM)")
    # print(tock_zh_valuation_baidu_df)
    # ods 单独没有这个29号数据
    # 字段是 date open close high low volume


    df = pd.DataFrame({"A": ['a', 'b', 'b', 'd'],
                       "B": [11, 2, 4, 3],
                       "C": [4, 3, 8, 5],
                       "D": [5, 4, 2, 8]})
    print(df)
    # df['OLS'] = df.groupby('B', group_keys=False).apply(lambda x: x['A']-x['C'])
    # df['OLS'] = df.groupby('B', group_keys=False).apply(lambda x: sm.OLS(x['A'].astype(float),x.iloc[:, 6:], hasconst=False, missing='drop').fit().resid)
    df['OLS'] = df.groupby('A', group_keys=False).apply(lambda x: sm.OLS(x['B'].astype(float),x.iloc[:, 2:], hasconst=False, missing='drop').fit().resid)
    # df['OLS'] = df.groupby('A', group_keys=False).apply(lambda x: print(x['A'],x.iloc[:, 2:]))
    # df['OLS'] = df.iloc[:, 2:].sum()

    # print(df)
    # print(type(df.values.tolist()))
    # df2 = pd.DataFrame({"A": [pd.to_datetime('20221101').date(), pd.to_datetime('20221201').date(), pd.to_datetime('20220104').date(), pd.to_datetime('20221020').date()]})
    # df['r'] = df.A.shift(1)
    # df = ak.stock_a_lg_indicator(symbol='000609')
    # print(df)


    # print('333',stock_board_concept_hist_em_df3)

    # lst99 = [['001', [1,11]],['002', [2,22]],['003', [3,33]]]
    # for i,(num,(a,b)), in enumerate(lst99):
    #     print(i+1, num,a,b)
    #
    # print(int(5/2))
    # pa_group = [['001', 'df'],['002', 'df'],['003', 'df']]
    # for i in range(len(pa_group)):
    #     print(len(pa_group))
    #     print(i)
    #     num,kk = pa_group[i][0],pa_group[i][1]
    #     print(num,kk)

    # stock_hot_rank_em_df = ak.stock_hot_rank_em()
    # print(stock_hot_rank_em_df)

    # stock_hot_follow_xq_df = ak.stock_hot_follow_xq(symbol="最热门")
    # print(stock_hot_follow_xq_df)

    # df = ak.stock_lrb_em(date='20221231')
    # df = ak.stock_board_concept_name_em()
    # print(df)

