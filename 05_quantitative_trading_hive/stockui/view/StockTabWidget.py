import os
import sys
# 在linux会识别不了包 所以要加临时搜索目录
from stockui.widgets.MyTableView import MyTableView

curPath = os.path.abspath(os.path.dirname(__file__))
rootPath = os.path.split(curPath)[0]
sys.path.append(rootPath)
from PyQt5.QtWidgets import QAction, QAbstractItemView, QHeaderView, QMenu
from PyQt5.QtCore import Qt
from qtpy import uic
from stockui.UiDataUtils import *
from stockui.QSignalSlot import *
from stockui.basewidget import BaseTabWidget
from stockui.PdTable import PdTable
from stockui.view.StockDetailWindow import StockDetailWindow


class StockTabWidget(BaseTabWidget,QSlot):
    """主界面板块tab"""
    def __init__(self, mainWindow, tabPosition):
        super(StockTabWidget, self).__init__(mainWindow, tabPosition)
        self.initUi()
        self.uiDataUtils = UiDataUtils()
        self.listener()
        # 初始化日期 取dwd最新日期
        self.ui.dateTimeEdit.setDate(self.uiDataUtils.q_end_date)

    def initUi(self):
        self.ui = uic.loadUi(os.path.join(curPath, 'designer/tab_stock.ui'), self)
        # 板块详情窗口
        self.stockDetailWindow = StockDetailWindow()


    def loadStockTable(self):
        '''加载股票tab 某日数据'''
        self.stock_df = self.uiDataUtils.get_all_stock(self.date, self.date)
        if self.stock_df.empty:
            print('{} 股票数据为空！！！'.format(self.date))
            return
        # 表格模式
        self.dfModel = PdTable(self.stock_df)
        self.ui.tableView.setModel(self.dfModel)
        # --------设置表格属性-------------------------------------------------
        self.ui.tableView.horizontalHeader().setStretchLastSection(True)
        self.ui.tableView.horizontalHeader().setSectionsClickable(True)
        self.ui.tableView.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.ui.tableView.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.ui.tableView.setSelectionMode(QAbstractItemView.SingleSelection)
        self.ui.tableView.horizontalHeader().setStretchLastSection(True)
        self.ui.tableView.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.ui.tableView.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        # 设置选中颜色
        self.ui.tableView.setStyleSheet("QTableView::item:selected{background-color: rgb(0, 170, 255);}")

        # 允许打开上下文菜单
        self.ui.tableView.setContextMenuPolicy(Qt.CustomContextMenu)
        # 绑定事件
        self.ui.tableView.customContextMenuRequested.connect(self.generateMenu)
    # == == == == == == == == == == == == == == == == == == == == 事件或小部件显示 == == == == == == == == == == == == == == == == == == == ==
    def listener(self):
        self.ui.dateTimeEdit.dateChanged.connect(self.dateChangeSlot)
        self.ui.lastDay.clicked.connect(self.lastDaySlot)
        self.ui.nextDay.clicked.connect(self.nextDaySlot)
        self.ui.tableView.doubleClicked.connect(self.openStockDetail)
        self.ui.query.clicked.connect(lambda: self.querySlot(self.ui.queryText.text()))
        # 回车
        self.ui.queryText.returnPressed.connect(lambda: self.querySlot(self.ui.queryText.text()))

    def querySlot(self, text):
        '''查询工具'''
        try:
            print(text)
            self.stock_df = self.uiDataUtils.query_stock_where(self.date, self.date, text)
            if self.stock_df.empty:
                print('{} 股票数据为空！！！'.format(date))
                return
            # 表格模式
            self.dfModel = PdTable(self.stock_df)
            self.ui.tableView.setModel(self.dfModel)

        except Exception as e:
            print(e)

    def generateMenu(self, pos):
        '''自定义菜单'''
        # 获取点击行号
        for i in self.ui.tableView.selectionModel().selection().indexes():
            rowNum = i.row()
            menu = QMenu()
            item1 = menu.addAction("加入自选分组")
            item2 = menu.addAction("删除")
            # 转换坐标系
            screenPos = self.ui.tableView.mapToGlobal(pos)
            print(screenPos)
            # 被阻塞
            action = menu.exec(screenPos)
            if action == item1:
                print('加入自选分组')
                model = self.ui.tableView.model()
                dfRow = model.getRow(rowNum)
                code = dfRow['code']
                print('code：',type(dfRow),code)
            elif action == item2:
                print('删除')
            else:
                return


    def dateChangeSlot(self, date):
        """日期改变"""
        date = date.toString('yyyy-MM-dd')
        self.date = date
        self.loadStockTable()

    def openStockDetail(self, item):
        """双击传递key 并打开子窗口"""
        row = item.row()
        model = item.model()
        dfRow = model.getRow(row)
        # code = dfRow['code']
        # print(code)
        self.stockDetailWindow.showWindow(self.stock_df, dfRow)
