import os
import asyncio
import logging
from datetime import datetime
from zoneinfo import ZoneInfo
from dateutil.relativedelta import relativedelta
import math
import aiohttp
import pandas as pd
from dotenv import load_dotenv

from fake_useragent import UserAgent


class ParseRequests:
    """
    Docstring for ParseRequests
    """
    def __init__(self, session: aiohttp.ClientSession, seller_id: str | int, personal_discount: int):
        self.session = session
        self.seller_id = seller_id
        self.personal_discount = personal_discount
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

    async def fetch_prices(self) -> list:
        """Получаем товары со страницы с ценами на сайте"""
        page = 1
        dest = 1257218  # г. Москва, Милютинский переулок 3
        items = []
        total_pages = 1
        fua = UserAgent()

        while page <= total_pages:
            headers = {
                'UserAgent': fua.random
            }
            url = f'https://www.wildberries.ru/__internal/u-catalog/sellers/v4/catalog?ab_testing=false&ab_testing=false&appType=1&curr=rub&dest=-{dest}&hide_dtype=11&lang=ru&page={page}&sort=popular&spp=30&supplier={self.seller_id}'

            try:
                async with self.session.get(url, headers=headers) as response:
                    print(f'Запрос: {url}')

                    if response.status == 200:
                        data = await response.json()
                        products = data.get('products', [])

                        total_pages = math.ceil(data.get('total', 1) / 100)

                        print(
                            f"POST_CODE {response.status} \n"
                            f"Seller {self.seller_id}, page {page}: \n"
                            f"Found {len(products)} products, total pages: {total_pages} \n"
                        )

                        for product in products:
                            wb_price = product.get('sizes', [{}])[0].get(
                                'price', {}).get('product', 0) / 100
                            personal_price = wb_price * \
                                (1 - self.personal_discount/100)

                            item = {
                                'WB_ID': product.get('id'),
                                'wb_price': wb_price,
                                'personal_discount': self.personal_discount,
                                'personal_price': math.floor(personal_price)
                            }

                            items.append(item)
                        page = page + 1

                    elif response.status == 429:
                        print("Too many requests. Waiting 10 seconds...")
                        await asyncio.sleep(10)

                    else:
                        print(
                            f"Error {response.status}. Retrying in 5 seconds...")
                        await asyncio.sleep(5)

            except aiohttp.ClientError as e:
                print(f'Error {e}. Retrying in 5 seconds...')
                await asyncio.sleep(5)

        return items


class APIRequests:
    def __init__(self, session: aiohttp.ClientSession, TOKEN: str):
        load_dotenv()
        self.TOKEN = os.getenv(TOKEN)
        self.session = session
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

    async def get_nomenclature(self, max_attempts: int = 5) -> list:
        """ Получаем список номенклатуры по API """

        url = 'https://content-api.wildberries.ru/content/v2/get/cards/list'
        headers = {'Authorization': self.TOKEN}

        limit = 100
        total = float('inf')
        updatedAt = None
        nmID = None
        cards = []
        
        while total >= limit:
            for attempt in range(max_attempts):
                wait_time = 5 * (attempt + 1)
                params = {
                    'settings': {
                        'cursor': {
                            'limit': limit,
                            'updatedAt': updatedAt,
                            'nmID': nmID
                        },
                        'sort': {},
                        'filter': {
                            "withPhoto": -1
                        }
                    }
                }
                
                try:
                    self.logger.info(f'Requesting cards, cursor total: {total}, attempt {attempt + 1}/{max_attempts}')
                    async with self.session.post(url=url, headers=headers, json=params) as response:

                        if response.status == 200:
                            data = await response.json()
                            items = data.get('cards', [])

                            updatedAt = data.get('cursor', {}).get('updatedAt')
                            nmID = data.get('cursor', {}).get('nmID')
                            total = data.get('cursor', {}).get('total')
                            self.logger.info(f'Fetched {len(items)} items, total remaining: {total}')
                            
                            for item in items:
                                card = {}
                                card['brand'] = item.get('brand')
                                card['category'] = item.get('subjectName')
                                card['WB_ID'] = item.get('nmID')
                                card['article'] = item.get('vendorCode')
                                card['name'] = item.get('title')
                                card['skus'] = []
                                for size in item.get('sizes', []):
                                    for sku in size.get('skus', []):
                                        card['skus'].append(sku)

                                cards.append(card)

                        elif response.status == 429:
                            details = await response.text()
                            self.logger.warning(f"Rate limit exceeded. Retry after: {wait_time}s. Details: {details}")
                            await asyncio.sleep(wait_time)
                            attempt += 1
                            
                        elif response.status in [400, 401, 403, 404]:
                            error_details = await response.text()
                            self.logger.error(f"Request failed with status {response.status}: {error_details}")
                            total = 0
                            break

                        else:
                            error_details = await response.text()
                            self.logger.error(f"Request failed with status {response.status}: {error_details}. Retrying...")
                            await asyncio.sleep(wait_time)
                            attempt += 1

                except aiohttp.ClientError as e:
                    self.logger.error(f'Client error during request: {e}. Retrying...')
                    await asyncio.sleep(wait_time)
                    attempt += 1
                except asyncio.TimeoutError:
                    self.logger.error('Request timed out. Retrying...')
                    attempt += 1
                except Exception as e:
                    self.logger.error(f'Unexpected error during request: {e}')
                    break

        return cards

    async def get_prices(self) -> list:
        """ Получаем цены по API """

        url = 'https://discounts-prices-api.wildberries.ru/api/v2/list/goods/filter'
        headers = {'Authorization': self.TOKEN}

        cards = []

        params = {
            'limit': 1000
        }
        try:
            async with self.session.get(url=url, headers=headers, params=params) as response:
                print(f'Запрос: {url}')

                if response.status == 200:
                    data = await response.json()
                    items = data.get('data', {}).get('listGoods', [])
                    total = len(items)

                    print(f'Total: {total}, Found {len(items)} products')

                    for item in items:
                        card = {}
                        card['WB_ID'] = item.get('nmID', None)
                        card['price'] = item.get('sizes', [])[
                            0].get('price', None)
                        card['discount'] = item.get('discount', None)
                        card['discountedPrice'] = int(
                            round(card['price'] * (1 - card['discount']/100), 0))
                        card['clubDiscount'] = item.get('clubDiscount', 0)
                        card['clubDiscountedPrice'] = round(
                            card['discountedPrice'] * (1 - card['clubDiscount']/100), 1)

                        cards.append(card)

                elif response.status == 429:
                    print("Too many requests. Waiting 10 seconds...")

                else:
                    print(f"Error {response.status}. Retrying in 5 seconds...")

        except aiohttp.ClientError as e:
            print(f'Error {e}. Retrying in 5 seconds...')
            await asyncio.sleep(5)

        return cards

    async def get_orders(self) -> list:
        """ Получаем поставки по API """

        url = 'https://statistics-api.wildberries.ru/api/v1/supplier/orders'
        headers = {'Authorization': self.TOKEN}
        dateFrom = (datetime.now(ZoneInfo('Europe/Moscow')).date() -
                    relativedelta(months=1)).isoformat()
        params = {'dateFrom': dateFrom}

        orders = []

        try:
            async with self.session.get(url=url, headers=headers, params=params) as response:
                print(f'Запрос: {url}')

                if response.status == 200:
                    data = await response.json()

                    for item in data:
                        if item.get('isCancel', False) is False:
                            order = {}
                            order['region'] = item.get('oblastOkrugName')
                            order['article'] = item.get('supplierArticle')
                            order['WB_ID'] = item.get('nmId')
                            order['category'] = item.get('subject')
                            order['brand'] = item.get('brand')

                            orders.append(order)

                    return orders

                elif response.status == 429:
                    print("Too many requests. Waiting 10 seconds...")

                else:
                    print(f"Error {response.status}. Retrying in 5 seconds...")

        except aiohttp.ClientError as e:
            print(f'Error {e}. Retrying in 5 seconds...')
            await asyncio.sleep(5)

    async def get_supplies(self) -> list:
        url = 'https://supplies-api.wildberries.ru/api/v1/supplies'
        headers = {'Authorization': self.TOKEN}
        dates = [{'type': 'supplyDate'}]
        statusIDs = [3]
        params = {
            "dates": dates,
            "statusIDs": statusIDs
        }

        supplies_IDs = []

        try:
            async with self.session.post(url=url, headers=headers, json=params) as response:
                print(f'Запрос: {url}')

                if response.status == 200:
                    data = await response.json()

                    for item in data:
                        supply = {}
                        supply['supplyID'] = item.get('supplyID')

                        supplies_IDs.append(supply)

                elif response.status == 429:
                    print("Too many requests. Waiting 10 seconds...")

                else:
                    print(f"Error {response.status}. Retrying in 5 seconds...")

        except aiohttp.ClientError as e:
            print(f'Error {e}. Retrying in 5 seconds...')
            await asyncio.sleep(5)

        supplies_details = []

        for supply_ID in supplies_IDs:
            url = f'https://supplies-api.wildberries.ru/api/v1/supplies/{supply_ID['supplyID']}'
            try:
                async with self.session.get(url=url, headers=headers) as response:
                    print(f'Запрос: {url}')

                    if response.status == 200:
                        item = await response.json()

                        supply = {}
                        supply['createDate'] = item.get('createDate')
                        supply['supplyID'] = supply_ID
                        supply['warehouseID'] = item.get('warehouseID')
                        supply['warehouseName'] = item.get('warehouseName')
                        supply['acceptanceCost'] = item.get('acceptanceCost')
                        supply['storageCoef'] = item.get('storageCoef')
                        supply['deliveryCoef'] = item.get('deliveryCoef')
                        supply['quantity'] = item.get('quantity')
                        supply['acceptedQuantity'] = item.get(
                            'acceptedQuantity')
                        supply['readyForSaleQuantity'] = item.get(
                            'readyForSaleQuantity')

                        supplies_details.append(supply)

                    elif response.status == 429:
                        print("Too many requests. Waiting 10 seconds...")

                    else:
                        print(
                            f"Error {response.status}. Retrying in 5 seconds...")

            except aiohttp.ClientError as e:
                print(f'Error {e}. Retrying in 5 seconds...')
                await asyncio.sleep(5)


async def main():
    async with aiohttp.ClientSession() as session:
        api_requests = APIRequests(session=session, TOKEN='КОСТРИК')
        result = await asyncio.gather(
            api_requests.get_nomenclature()
        )
        print(len(result[0]))
    #     result = await asyncio.gather(
    #         get_nomenclature(session=session, TOKEN='КОСТРИК'),
    #         seller_prices(session=session, seller_id=53699, personal_discount=7),
    #         get_prices(session=session, TOKEN='КОСТРИК')
    #         )

    # nomenclature_df = pd.DataFrame(result[0])
    # wb_prices_df = pd.DataFrame(result[1])
    # api_prices_df = pd.DataFrame(result[2])
    # cost_price_1C = (pd.read_excel('Прайс-лист.xls')).rename(columns={'Код': 'article', 'Наименование': 'name', 'Закуп.': 'cost_price'})
    # cost_price_1C['cost_price'] = cost_price_1C['cost_price'].str.replace('\'', '').astype('Float64')

    # report = pd.merge(
    #     left=nomenclature_df,
    #     right=wb_prices_df[['WB_ID', 'wb_price', 'personal_discount', 'personal_price']],
    #     how='left',
    #     on='WB_ID').merge(
    #         right=api_prices_df,
    #         how='left',
    #         on='WB_ID').merge(
    #             right=cost_price_1C[['article', 'cost_price']],
    #             how='left',
    #             on='article')

    # report['spp'] = (round((1 - report['wb_price']/report['clubDiscountedPrice']) * 100, 0)).astype('Int64')
    # report['profit'] = round(report['clubDiscountedPrice'] - report['cost_price'], 2)
    # report['markup, %'] = (round((report['clubDiscountedPrice']/report['cost_price']) * 100)).astype('Int64')

    # report = report[['brand', 'category', 'WB_ID', 'name', 'article', 'skus', 'price', 'discount', 'discountedPrice', 'clubDiscount', 'clubDiscountedPrice', 'spp', 'wb_price', 'personal_discount', 'personal_price', 'cost_price', 'profit', 'markup, %']]

    # try:
    #     pd.DataFrame(report).to_csv('Метрики.csv', index=False)
    #     pd.DataFrame(report).to_excel('Метрики.xlsx', index=False)

    # except Exception as e:
    #     print(f'\n\nОшибка сохранения: {e}!\n\n')


if __name__ == '__main__':
    asyncio.run(main())
