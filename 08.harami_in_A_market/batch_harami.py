# Python实用宝典
# 2020/05/16
# 转载请注明出处
import datetime
import os.path
import sys
import numpy as np
import backtrader as bt
import matplotlib.pyplot as plt
from backtrader.indicators.ema import ExponentialMovingAverage


class TestStrategy(bt.Strategy):
    def __init__(self):
        self.dataclose = self.datas[0].close
        self.datahigh = self.datas[0].high
        self.datalow = self.datas[0].low
        self.dataopen = self.datas[0].open
        self.volume = self.datas[0].volume

        self.order = None
        self.buyprice = None
        self.buycomm = None
        self.params.profits = []

        self.sma20 = bt.indicators.SimpleMovingAverage(self.datas[0], period=20)

        me1 = ExponentialMovingAverage(self.data, period=12)
        me2 = ExponentialMovingAverage(self.data, period=26)
        self.macd = me1 - me2
        self.signal = ExponentialMovingAverage(self.macd, period=9)

        bt.indicators.MACDHisto(self.data)

    def log(self, txt, dt=None):
        """ Logging function fot this strategy"""
        dt = dt or self.datas[0].datetime.date(0)
        # print('%s, %s' % (dt.isoformat(), txt))

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    "BUY EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f"
                    % (order.executed.price, order.executed.value, order.executed.comm)
                )

                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
                self.bar_executed_close = self.dataclose[0]
            else:
                self.log(
                    "SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f"
                    % (order.executed.price, order.executed.value, order.executed.comm)
                )
                temp = float(order.executed.price - self.buyprice)/float(self.buyprice)
                self.params.profits.append(temp)

            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log("Order Canceled/Margin/Rejected")

        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return
        self.bar_executed = len(self)
        self.log("OPERATION PROFIT, GROSS %.2f, NET %.2f" % (trade.pnl, trade.pnlcomm))

    # Python 实用宝典
    def next(self):
        self.log("Close, %.2f" % self.dataclose[0])
        if self.order:
            return
        if not self.position:
            # condition1 = self.sma20[0] > self.dataclose[0]
            if self.dataclose[-1] < self.dataopen[-1]:
                harami = (
                    self.datahigh[0] < self.dataopen[-1]
                    and self.datalow[0] > self.dataclose[-1]
                )
            else:
                harami = (
                    self.datahigh[0] < self.dataclose[-1]
                    and self.datalow[0] > self.dataopen[-1]
                )

            if harami:
                self.log("BUY CREATE, %.2f" % self.dataclose[0])
                self.order = self.buy()

        else:
            condition = (self.dataclose[0] - self.bar_executed_close) / self.dataclose[
                0
            ]
            if condition > 0.1 or condition < -0.1:
                self.log("SELL CREATE, %.2f" % self.dataclose[0])
                self.order = self.sell()


def run_cerebro(stock_file, result):
    """
    运行策略
    :param stock_file: 股票数据文件位置
    :param result: 回测结果存储变量
    """

    cerebro = bt.Cerebro()

    cerebro.addstrategy(TestStrategy)

    # 加载数据到模型中
    data = bt.feeds.GenericCSVData(
        dataname=stock_file,
        fromdate=datetime.datetime(2010, 1, 1),
        todate=datetime.datetime(2020, 5, 10),
        dtformat="%Y%m%d",
        datetime=2,
        open=3,
        high=4,
        low=5,
        close=6,
        volume=10,
        reverse=True,
    )
    cerebro.adddata(data)

    # 本金100000,数量多少无所谓，因为算的是利润百分比
    cerebro.broker.setcash(100000)
    cerebro.addsizer(bt.sizers.FixedSize, stake=100)

    # 万五佣金
    cerebro.broker.setcommission(commission=0.0005)

    # 运行策略
    cerebro.run()

    # 获取股票名字
    stock_name = stock_file.split("\\")[-1].split(".csv")[0]

    # 将最终回报率以百分比的形式返回
    result[stock_name] = cerebro.runstrats[0][0].params.profits


files_path = "./thoudsand_stocks/"
result = {}

# 遍历所有股票数据
for stock in os.listdir(files_path):
    modpath = os.path.dirname(os.path.abspath(sys.argv[0]))
    datapath = os.path.join(modpath, files_path + stock)
    print(datapath)
    try:
        run_cerebro(datapath, result)
    except Exception as e:
        print(e)

# 计算
pos = []
neg = []
for data in result:
    res = np.mean(result[data])
    if res > 0:
        pos.append(res)
    else:
        neg.append(res)
print(f"正收益数量: {len(pos)}, 负收益数量:{len(neg)}")

plt.hist(pos, facecolor="red", edgecolor="black", alpha=0.7)
plt.hist(neg, facecolor="green", edgecolor="black", alpha=0.7)
plt.show()
