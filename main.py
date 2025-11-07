import math
import aiohttp
import pandas as pd
import time
import os
from dotenv import load_dotenv
import asyncio

from fake_useragent import UserAgent


async def seller_prices(session: aiohttp.ClientSession, seller_id: str | int, personal_discount: int):
    print(f'Получение цен из каталога продавца на сайте\n')

    page = 1
    appType = 1 # Веб версия
    curr = 'rub' # Валюта
    lang = 'ru' # Язык


    items = []
    quantity_products = 1
    fua = UserAgent()

    while quantity_products != 0:
        headers = {
            'UserAgent': fua.random
        }
        url = f'https://catalog.wb.ru/sellers/v4/catalog?ab_testing=false&ab_testing=false&appType={str(appType)}&curr={curr}&dest=123587633&hide_dtype=11&lang={lang}&page={str(page)}&sort=popular&spp=10&supplier={str(seller_id)}&uclusters=1'
        await asyncio.sleep(1)
        # response = requests.get(url, headers=headers)

        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                products = await data.get('products', [])
                quantity_products = (len(products))
                print(f'STATUS_CODE: {response.status_code}, quantity_products: {quantity_products}')
                
                if quantity_products != 0:
                    for product in products:
                        price = product.get('sizes', [{}])[0].get('price', {}).get('product', 0) / 100
                        personal_price = price * (1 - personal_discount/100)
                        item = {
                            'sku': product.get('id'),
                            'name': product.get('name'),
                            'price': math.floor(personal_price)
                        }
                        items.append(item)
                    page = page + 1
                    await asyncio.sleep(1)

    print(f'Получено {len(items)} объектов')
    try:
        site_prices = pd.DataFrame(items)
        site_prices.to_csv('site_prices.csv', index=False)
        print(f'Прайс сохранен!')
    except Exception as e:
        print(f'Возникла ошибка сохранения: {e}')


async def get_nomenclature(TOKEN: str):
    load_dotenv()
    TOKEN = os.getenv(TOKEN)

    

async def main():
    # asyncio.run(get_nomenclature('seller-53699'))
    # asyncio.run(seller_prices(53699, 6))
    async with aiohttp.ClientSession() as session:
        await asyncio.gather(
            seller_prices(session=session, seller_id=53699, personal_discount=6)
            )
    # seller_prices(seller_id=53699, personal_discount=6)

if __name__ == '__main__':
    asyncio.run(main())

