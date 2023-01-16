import math
import os
import sys
import pandas as pd
import numpy as np
import statsmodels.api as sm
from scipy import stats
# 在linux会识别不了包 所以要加临时搜索目录
curPath = os.path.abspath(os.path.dirname(__file__))
rootPath = os.path.split(curPath)[0]
sys.path.append(rootPath)

'''ICIR 因子清洗工具'''
def filter_extreme_MAD(series,n=3):
    """3倍中位数去极值"""
    median = series.median()
    new_median = ((series - median).abs()).median()
    return series.clip(median - n*new_median,median + n*new_median)

def percentile(df_factor, min=0.01, max=0.99):
    """固定比例去极值"""
    # 得到上下限的值
    q = df_factor.quantile([min, max])
    # 超出上下限的值，赋值为上下限
    return np.clip(df_factor, q.iloc[0], q.iloc[-1])

def winsorize_percentile(series, left=0.025, right=0.975):
    lv, rv = np.percentile(series, [left*100, right*100])
    return series.clip(lv, rv)

def stand(series):
    """z-score 标准化"""
    mean = series.mean()
    std = series.std()
    return (series - mean) / std

def nonlinear_transform(series, quantile_to_subtract):
    # 转换后因子值 = -（因子值 - 对应分位数）^2，此时因子值离该分位数越近，转换后因子值越大
    return -(series.sub(series.quantile(quantile_to_subtract, axis=1), axis=0) ** 2)

def dwd_factor(df):
    pass

def neutralization(factor,df):
    '''单因子行业市值中性化'''
    industry_plates = sm.categorical(df['industry_plate'], drop=True)
    pd_df = df.drop(['industry_plate'], axis=1).join(industry_plates)
    # 行业市值中性化 第一个是y = 因子值 第二个是x= 市值+行业
    r_df = pd.DataFrame()
    grouped = pd_df.groupby(['trade_date'])
    for name, group in grouped:
        group['OLS'] = sm.OLS(group[factor], group.iloc[:, 5:], hasconst=False, missing='drop').fit().resid
        r_df = r_df.append(group[['trade_date','stock_code','stock_name',factor,'holding_yield_n']])
    return r_df

def factor_ic(factor,df, Rank_IC=True):
    '''单因子IC_IR计算'''
    if Rank_IC == True:
        rank_ic = df.groupby('trade_date')['holding_yield_n',factor].corr(method='spearman').reset_index()
        print(rank_ic)
        return rank_ic[rank_ic.level_1 == 'holding_yield_n'][['trade_date',factor]]
    else:
        normal_ic = df.groupby('trade_date')['holding_yield_n', factor].corr(method='pearson').reset_index()
        return normal_ic[normal_ic.level_1 == 'holding_yield_n'][['trade_date',factor]]

def ic_ir(factor,df):
    '''单因子IC_IR报告
       歧义ic一般是指ic均值
       ic_mean(ic均值的绝对值)：>0.05好;>0.1很好;>0.15非常好;>0.2可能错误(未来函数);当ic均值>0是正向因子
       ic_ir(ir=ic均值/ic标准差)：>=0.5认为因子稳定获取超额收益能力较强;越大越好
       ic>0：ic>0的概率 没什么作用
       abs_ic>0.02：ic绝对值>0,02的比例
       t_abs：样本T检验，X对比0，如果t只在1，-1之间，说明X均值为0，假设成立;在这绝对值应该越大越好，t_abs<1：因子有效性差
       p：当p值小于0.05时，认为与0差异显著;在这越小越好
       skew：偏度 为正则是右偏，为负则是左偏，指正态左右偏峰谷在另一则
       kurtosis：峰度 峰度描述的是分布集中趋势高峰的形态，通常与标准正态分布相比较。
                在归一化到同一方差时，若分布的形状比标准正态分布更瘦高，则称为尖峰分布，若分布的形状比标准正态分布更矮胖，则称为平峰分布。
                当峰度系数为 0 则为标准正态分布，大于 0 为尖峰分布，小于 0 为平峰分布。
    '''
    # 案例 ['IC mean:0.018','IC std:0.037','IR:0.4864','IC>0:0.6752','ABS_IC>2%:0.5398','t_stat:12.5434','p_value:0.0','skew:0.3329','kurtosis:-0.2338']
    # ['IC mean:0.004', 'IC std:0.0972', 'IR:0.0414', 'IC>0:0.4857', 'ABS_IC>2%:0.8071', 't_stat:0.4901', 'p_value:0.6249', 'skew:0.1638', 'kurtosis:0.3735']
    x = df[[factor]]
    # 样本T检验，X对比0，如果t只在1，-1之间，说明X均值为0，假设成立;在这绝对值应该越大越好，t_abs<1：因子有效性差
    # 当p值小于0.05时，认为差异显著;在这越小越好
    t_stat, p_value = stats.ttest_1samp(x, 0)
    r_df = pd.DataFrame()
    r_df['因子名称'] = factor
    r_df['ic_mean'] = round(x.mean()[0], 4)
    r_df['ic_std'] = round(x.std()[0], 4)
    r_df['ic_ir'] = round(x.mean()[0] / x.std()[0], 4)
    r_df['ic>0'] = round(len(x[x > 0].dropna()) / len(x), 4)
    r_df['abs_ic>0.02'] = round(len(x[abs(x) > 0.02].dropna()) / len(x), 4)
    r_df['t_abs'] = abs(t_stat.round(4)[0])
    r_df['p'] = p_value.round(4)[0]
    # 对于正态分布的数据，偏度应该大约为零。对于单峰连续分布，偏度值大于零意味着分布右尾的权重更大。从统计学上讲，该函数skewtest可用于确定偏度值是否足够接近零。
    # skew([1, 2, 3, 4, 5]) 0.0
    # skew([2, 8, 0, 4, 1, 9, 9, 0]) 0.2650554122698573
    r_df['skew'] = stats.skew(x).round(4)[0]
    r_df['kurtosis'] = stats.kurtosis(x).round(4)[0]
    return r_df
