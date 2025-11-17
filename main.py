import math
import aiohttp
import pandas as pd
import time
import os
from dotenv import load_dotenv
import asyncio
import requests

from fake_useragent import UserAgent


async def seller_prices(session: aiohttp.ClientSession, seller_id: str | int, personal_discount: int) -> list:
    """ Получаем товары со страницы продавца с ценами на сайте """
    page = 1
    dest = 1257218 # г. Москва, Милютинский переулок 3
    items = []
    total_pages = 1
    fua = UserAgent()

    while page <= total_pages:
        headers = {
            'UserAgent': fua.random
        }
        url = f'https://www.wildberries.ru/__internal/u-catalog/sellers/v4/catalog?ab_testing=false&ab_testing=false&appType=1&curr=rub&dest=-3902910&hide_dtype=11&lang=ru&page={page}&sort=popular&spp=30&supplier={seller_id}'
        
        try:
            async with session.get(url, headers=headers) as response:
                print(f'Запрос: {url}')

                if response.status == 200:
                    data = await response.json()
                    products = data.get('products', [])

                    total_pages = math.ceil(data.get('total', 1) / 100)
                    
                    print(
                        f"POST_CODE {response.status} \n" 
                        f"Seller {seller_id}, page {page}: \n"
                        f"Found {len(products)} products, total pages: {total_pages} \n"
                    )
                    
                    for product in products:
                        price = product.get('sizes', [{}])[0].get('price', {}).get('product', 0) / 100
                        personal_price = price * (1 - personal_discount/100)

                        item = {
                            'WB_ID': product.get('id'),
                            # 'name': product.get('name'),
                            'price': math.floor(personal_price)
                        }

                        items.append(item)
                    page = page + 1

                elif response.status == 429:
                    print("Too many requests. Waiting 10 seconds...")
                    await asyncio.sleep(10)
                
                else:
                    print(f"Error {response.status}. Retrying in 5 seconds...")
                    await asyncio.sleep(5)

        except aiohttp.ClientError as e:
            print(f'Error {e}. Retrying in 5 seconds...')
            await asyncio.sleep(5)
            
    return items



async def get_nomenclature(session: aiohttp.ClientSession, TOKEN: str) -> list:
    """ Получаем список номенклатуры по API """
    load_dotenv()
    TOKEN = os.getenv(TOKEN)
    
    url = 'https://content-api.wildberries.ru/content/v2/get/cards/list'
    headers = {'Authorization': TOKEN}
    
    limit = 100
    total = 100
    updatedAt = None
    nmID = None

    cards = []

    while total >= limit:
        params =  {
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
            async with session.post(url=url, headers=headers, json=params) as response:
                print(f'Запрос: {url}')

                if response.status == 200:
                    data = await response.json()
                    items = data.get('cards', [])
            
                    updatedAt = data.get('cursor', {}).get('updatedAt', None)
                    nmID = data.get('cursor', {}).get('nmID', None)
                    total = data.get('cursor', {}).get('total', 0)
                    print(f'Total: {total}, Found {len(items)} products')

                    for item in items:
                        card = {}
                        card['WB_ID'] = item.get('nmID', 0) # Артикул ВБ
                        card['name'] = item.get('title', None) # Наименование
                        # card['CARD_ID'] = item.get('imtID', None) # Артикул склейки карточки
                        card['article'] = item.get('vendorCode', None) # Артикул продавца
                        card['skus'] = [] # Баркоды
                        for size in item.get('sizes', []):
                            for sku in size.get('skus', []):
                                card['skus'].append(sku)
                        
                        cards.append(card)
            
                elif response.status == 429:
                    print("Too many requests. Waiting 10 seconds...")
                    await asyncio.sleep(10)
                        
                else:
                    print(f"Error {response.status}. Retrying in 5 seconds...")
                    await asyncio.sleep(5)

        except aiohttp.ClientError as e:
            print(f'Error {e}. Retrying in 5 seconds...')
            await asyncio.sleep(5)
                    

    
    return cards 



async def get_prices(session: aiohttp.ClientSession, TOKEN: str) -> list:
    """ Получаем цены по API """
    load_dotenv()
    TOKEN = os.getenv(TOKEN)
    
    url = 'https://discounts-prices-api.wildberries.ru/api/v2/list/goods/filter'
    headers = {'Authorization': TOKEN}
    
    cards = []

    params =  {
        'limit': 1000
    }
    try:
        async with session.get(url=url, headers=headers, json=params) as response:
            print(f'Запрос: {url}')
            data = await response.json()

            print(data.get('errorText'))

            if response.status == 200:
                data = await response.json()
                items = data.get('listGoods', [])
                total = len(items)

                print(f'Total: {total}, Found {len(items)} products')

                for item in items:
                    card = {}
                    card['WB_ID'] = item.get('nmID', 0) # Артикул ВБ
                    # card['name'] = item.get('title', None) # Наименование
                    # card['CARD_ID'] = item.get('imtID', None) # Артикул склейки карточки
                    # card['article'] = item.get('vendorCode', None) # Артикул продавца
                    card['price'] = item.get('sizes', [])[0].get('price', 0)
                    card['discount'] = item.get('discount', 0)
                    card['discountedPrice'] = card['price'] * (1 - card['discount']/100)
                    card['clubDiscount'] = item.get('clubDiscount', 0)
                    card['clubDiscountedPrice'] = card['discountedPrice'] * (1 - card['clubDiscount']/100)
                    
                    cards.append(card)
        
            elif response.status == 429:
                print("Too many requests. Waiting 10 seconds...")
                await asyncio.sleep(10)
                    
            else:
                print(f"Error {response.status}. Retrying in 5 seconds...")
                await asyncio.sleep(5)
    except aiohttp.ClientError as e:
        print(f'Error {e}. Retrying in 5 seconds...')
        await asyncio.sleep(5)
                    

    
    return cards 
        

    

async def main():
    async with aiohttp.ClientSession() as session:
        result = await asyncio.gather(
            # get_nomenclature(session=session, TOKEN='КОСТРИК'),
            # seller_prices(session=session, seller_id=53699, personal_discount=6),
            get_prices(session=session, TOKEN='КОСТРИК')
            )

    # nomenclature_df = pd.DataFrame(result[0])
    # wb_prices_df = pd.DataFrame(result[1])
    api_prices_df = pd.DataFrame(result[0])

    # report = pd.merge(left=nomenclature_df, right=prices_df[['WB_ID', 'price']], how='left', on='WB_ID')
    pd.DataFrame(api_prices_df).to_csv('Метрики.csv', index=False)


if __name__ == '__main__':
    asyncio.run(main())
    