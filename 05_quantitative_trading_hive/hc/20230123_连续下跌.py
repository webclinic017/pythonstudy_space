import os
import sys
curPath = os.path.abspath(os.path.dirname(__file__))
rootPath = os.path.split(curPath)[0]
sys.path.append(rootPath)
from datetime import date, datetime
import datetime
import time
import pandas as pd
import akshare as ak
# 在linux会识别不了包 所以要加临时搜索目录
from util import bt_rank
from util.CommonUtils import get_spark
# 输出显示设置
pd.options.display.max_rows=None
pd.options.display.max_columns=None
pd.options.display.expand_frame_repr=False
pd.set_option('display.unicode.ambiguous_as_wide', True)
pd.set_option('display.unicode.east_asian_width', True)

# 这里最早有ma_250d的日期是2022-01-12
# python /opt/code/pythonstudy_space/05_quantitative_trading_hive/hc/20230123_连续下跌.py 20220112 20230120 2 3 7777
# python /opt/code/pythonstudy_space/05_quantitative_trading_hive/hc/20230123_连续下跌.py 20220112 20230120 5 3 8888
if __name__ == '__main__':
    if len(sys.argv) < 6:
        print("请携带所有参数")
    else:
        start_date = sys.argv[1]
        end_date = sys.argv[2]
        hold_day = int(sys.argv[3])
        hold_n = int(sys.argv[4])
        port = sys.argv[5]

    '''
    策略逻辑(基本面+量价)：
    1.-3=<(当天收盘/开盘-1)*100<=3
    2.股价>最近一年最低点1.3
    3.股价<最近一年最高点0.75
    4.前4~5日 (涨停 or 5日量比大于1.5)
    5.连续3天收盘下跌 and 回踩10日或50日均线
    6.RS>昨日RS
    7.个股rps_5d>昨rps_5d
    11.换手率1~30之间 f_换手率升序
    12.
    ----------放弃的条件--------
    量价齐跌and放量或涨停基本没有
    另一个取连续下跌 这里不取涨停或放量了
    前4~5日 (涨停 or 创10日最高成交金额 or 成交金额是10天平均的一倍以上)
    '''
    appName = os.path.basename(__file__)
    start_time = time.time()
    spark = get_spark(appName)
    start_date, end_date = pd.to_datetime(start_date).date(), pd.to_datetime(end_date).date()
    # 为了向后补数据有值填充
    end_date_5 = pd.to_datetime(end_date + datetime.timedelta(5)).date()
    # 导入到bt 不能有str类型的字段
    # 排除主观因子
    sql = """
       with tmp_ads_01 as (
       select *,
              lag(rs,1)over(partition by stock_code order by trade_date) as lag_rs,
              lag(rps_5d,1)over(partition by stock_code order by trade_date) as lag_rps_5d,
              sum(if(stock_label_names rlike '当天涨停',1,0))over(partition by stock_code order by trade_date rows between 4 preceding and 3 preceding) as is_zt_4_5d,
              sum(if(volume_ratio_5d>1.5,1,0))over(partition by stock_code order by trade_date rows between 4 preceding and 3 preceding) as is_volume_ratio,
              sum(if(change_percent<0,1,0))over(partition by stock_code order by trade_date rows between 2 preceding and current row) as is_lxxd_3d,
              if((high_price>ma_10d and low_price<ma_10d) or (high_price>ma_10d and low_price<ma_10d),1,0) as is_hc_ma10_ma50
       from stock.dwd_stock_quotes_stand_di
       where td between '%s' and '%s'
       ),
       tmp_ads_02 as (
        select *
        from tmp_ads_01
        where stock_name not rlike 'ST'
            and (close_price/open_price-1)*100 between -3 and 3
            and ma_250d is not null
            and close_price>low_price_250d*1.3
            and close_price<high_price_250d*0.75
            and turnover_rate between 1 and 30
            and rs>lag_rs
            and rps_5d>lag_rps_5d
            and is_lxxd_3d =3
            and is_hc_ma10_ma50 = 1
       ),
       tmp_ads_03 as (
        select *
        from tmp_ads_02
        where is_zt_4_5d >0
            or is_volume_ratio >0
       ),
       tmp_ads_04 as (
       --去除or 停复牌
       select a.*
       from tmp_ads_03 a
       left join (select trade_date,lead(trade_date,1)over(order by trade_date) as next_trade_date from stock.ods_trade_date_hist_sina_df) b
            on a.trade_date = b.trade_date
       where a.suspension_time is null
             or a.estimated_resumption_time < b.next_trade_date
       ),
       --要剔除玩所有不要股票再排序 否则排名会变动
       tmp_ads_05 as (
       select *,
--               dense_rank()over(partition by td order by rps_50d) as dr_rps_50d,
              dense_rank()over(partition by td order by f_turnover_rate) as dr_f_turnover_rate
       from tmp_ads_04
       ),
       tmp_ads_06 as (
                      select *,
                             'mm' as stock_strategy_name,
                             dense_rank()over(partition by td order by dr_f_turnover_rate,volume_ratio_5d) as stock_strategy_ranking
                      from tmp_ads_05
       )
            select nvl(t1.trade_date,t2.trade_date) as trade_date,
                   nvl(t1.stock_code||'_'||t1.stock_name,t2.stock_code||'_'||t2.stock_name) as stock_code,
                   nvl(t1.open_price,t2.open_price) as open,
                   nvl(t1.close_price,t2.close_price) as close,
                   nvl(t1.high_price,t2.high_price) as high,
                   nvl(t1.low_price,t2.low_price) as low,
                   nvl(t1.volume,t2.volume) as volume,
                   nvl(t1.stock_strategy_ranking,9999) as stock_strategy_ranking
                   from tmp_ads_06 t1
                   full join stock.dwd_stock_quotes_di t2
                   on t1.trade_date = t2.trade_date
                        and t1.stock_code = t2.stock_code
                        and t2.td between '%s' and '%s'
                   order by stock_strategy_ranking
        """ % (start_date, end_date_5, start_date, end_date_5)

    # 读取数据
    spark_df = spark.sql(sql)
    pd_df = spark_df.toPandas()
    # 将trade_date设置成index
    pd_df = pd_df.set_index(pd.to_datetime(pd_df['trade_date'])).sort_index()
    print('{} 获取数据 运行完毕!!!'.format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    bt_rank.hc(appName.split('.')[0], pd_df, start_date, end_date, end_date_5, hold_day, hold_n, port=port)
    end_time = time.time()
    print('{}：程序运行时间：{}s，{}分钟'.format(os.path.basename(__file__),end_time - start_time, (end_time - start_time) / 60))