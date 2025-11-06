import math
import requests
import pandas as pd
import time

from fake_useragent import UserAgent


def seller_prices(seller_id: str | int, personal_discount: int):
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
        time.sleep(1)
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            products = data.get('products', [])
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
                time.sleep(1)

    print(f'Получено {len(items)} объектов')
    try:
        site_prices = pd.DataFrame(items)
        site_prices.to_csv('site_prices.csv', index=False)
        print(f'Прайс сохранен!')
    except Exception as e:
        print(f'Возникла ошибка сохранения: {e}')

def main():
    seller_prices(seller_id=53699, personal_discount=6)

if __name__ == '__main__':
    main()

