import fdb
import pandas as pd
import json
import sys
from pathlib import Path


with open('connection.json', 'r') as con_file:
    con = json.load(con_file)


items_info_csv = "items_info.csv"
barcodes_csv = 'barcodes.csv'
prices_csv = 'prices.csv'



class ItemToCsv:
    def __init__(self):
        self.price_type = con["price_type"]
        self.host = con['host']
        self.database = con['path']
        self.user = con["user"]
        self.password = con["password"]
        self.con = None
        self.cursor = None
        self.charset = 'utf-8'

    def connect_server(self):
        try:
            self.con = fdb.connect(
                host=self.host,
                database=self.database,
                user=self.user,
                password=self.password,
                charset=self.charset,
            )

        except fdb.fbcore.DatabaseError:
            print('Не получается подключится к базу данных...')
            return False

        else:
            print('Connection was successful!')
            self.cursor = self.con.cursor()
            return True

    def get_items_info(self):
        items_info_sql = 'SELECT ITM_ID, ITM_CODE, ITM_NAME, ITM_UNIT, ITM_GROUP, ITM_DELETED_MARK, ' \
                         'UNT_ID, UNT_NAME, ' \
                         'ITMG_ID, ITMG_NAME ' \
                         'FROM CTLG_ITM_ITEMS_REF ' \
                         'LEFT OUTER JOIN CTLG_UNT_UNITS_REF ON ITM_UNIT=UNT_ID ' \
                         'LEFT OUTER JOIN CTLG_ITM_GROUPS_REF ON ITM_GROUP=ITMG_ID ' \
                         'WHERE ITM_DELETED_MARK=0'
        self.cursor.execute(items_info_sql)
        columns_items_info = [desc[0] for desc in self.cursor.description]

        items_info = self.cursor.fetchall()

        items_price_sql = 'SELECT PRC_ITEM, PRC_PRICE_TYPE, PRC_VALUE ' \
                          'FROM CTLG_ITM_PRICES_REF ' \
                          'WHERE PRC_PRICE_TYPE=?'

        self.cursor.execute(items_price_sql, (con["price_type"], ))
        items_prices = self.cursor.fetchall()

        columns_items_prices = [desc[0] for desc in self.cursor.description]

        items_barcode_sql = 'SELECT BRCD_ID, BRCD_ITEM, BRCD_VALUE, BRCD_DELETED ' \
                            'FROM CTLG_ITM_BARCODES_REF ' \
                            'WHERE BRCD_DELETED=0'

        self.cursor.execute(items_barcode_sql)
        items_barcode = self.cursor.fetchall()
        columns_barcodes = [desc[0] for desc in self.cursor.description]

        dataframe_items = pd.DataFrame(items_info, columns=columns_items_info)
        dataframe_prices = pd.DataFrame(items_prices, columns=columns_items_prices)
        dataframe_barcodes = pd.DataFrame(items_barcode, columns=columns_barcodes)

        dataframe_items.to_csv(items_info_csv, index=False)
        dataframe_prices.to_csv(prices_csv, index=False)

        dataframe_barcodes.to_csv(barcodes_csv, index=False)
        self.cursor.close()
        self.con.close()

