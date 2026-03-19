import csv
import io
import math
import zipfile
from loguru import logger
import time
from dotenv import load_dotenv
from datetime import datetime
from zoneinfo import ZoneInfo
from dateutil.relativedelta import relativedelta
import os
import numpy as np
import pandas as pd
import requests
from fake_useragent import UserAgent
from seleniumbase import Driver

from requests.exceptions import HTTPError, ConnectionError, Timeout, RequestException


USER_AGENT = UserAgent().chrome
WB_URL = 'https://www.wildberries.ru'
# OZON_URL = 'https://www.ozon.ru/'
COOKIES_NEED = 'x_wbaas_token'

DEFAULT_PAYMENT_URL = "https://static-basket-01.wbbasket.ru/vol1/global-payment/default-payment.json"
SETTINGS_URL = "https://static-basket-01.wbbasket.ru/vol0/data/settings-front.json"

    
class APIRequests:

    def __init__(self, TOKEN_NAME: str):
        load_dotenv()
        self.TOKEN_NAME = TOKEN_NAME
        self.TOKEN_KEY = os.getenv(self.TOKEN_NAME)
        self.logger = logger
        self.logger.info(f'Токен {self.TOKEN_NAME} инициализирован')

    def get_nomenclature(self, max_attempts: int = 5) -> list:
        """ 
        Получаем список номенклатуры по API
        """

        URL = 'https://content-api.wildberries.ru/content/v2/get/cards/list'
        HEADERS = {'Authorization': self.TOKEN_KEY}
        limit = 100
        total = float('inf')
        updatedAt = None
        nmID = None
        cards = []
        
        for attempt in range(max_attempts):
            while total >= limit:
                wait_time = 5 * (attempt + 1)
                PARAMS = {
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
                    self.logger.info(f'Запрос URL: {URL}, попытка: {attempt + 1}/{max_attempts}')                    
                    response = requests.post(url=URL, headers=HEADERS, json=PARAMS)
                        
                    if response.status_code == 200:
                        data = response.json()
                        items = data.get('cards', [])
                        updatedAt = data.get('cursor', {}).get('updatedAt')
                        nmID = data.get('cursor', {}).get('nmID')
                        total = data.get('cursor', {}).get('total')
                                                
                        if items:
                            for item in items:
                                card = {}
                                card['brand'] = item.get('brand')
                                card['category'] = item.get('subjectName')
                                card['nmID'] = item.get('nmID')
                                card['article'] = item.get('vendorCode')
                                card['name'] = item.get('title')
                                card['skus'] = []
                                for size in item.get('sizes', []):
                                    for sku in size.get('skus', []):
                                        card['skus'].append(sku)
                                cards.append(card)
                                
                        if total == 0: 
                            self.logger.success(f'Все карточки получены. Всего: {len(cards)}')
                            break
                        else:
                            self.logger.info(f'Получено карточек: {len(cards)}') 
                            
                    elif response.status_code == 429:
                        self.logger.warning(f"{response.status_code}. Превышен лимит запросов. Повторная попытка через {wait_time}s")
                        time.sleep(wait_time)
                        attempt += 1
                    elif response.status_code in [400, 401, 403, 404]:
                        error_details = response.text()
                        self.logger.error(f"{response.status_code}. Ошибка запроса: {error_details}")
                        total = 0
                        break
                    else:
                        error_details = response.text()
                        self.logger.error(f"{response.status_code}. Ошибка запроса: {error_details}. Повторная попытка через {wait_time}s")
                        time.sleep(wait_time)
                        attempt += 1
                        
                except HTTPError as e:
                    self.logger.error(f'Ошибка клиента: {e}. Повторная попытка через {wait_time}s')
                    time.sleep(wait_time)
                except Timeout as e:
                    self.logger.error(f'Превышено время запроса: {e}. Повторная попытка через {wait_time}s.')
                except Exception as e:
                    self.logger.error(f'Ошибка запроса: {e}')
                    break
        return cards

    def get_prices(self, max_attempts: int = 5) -> list:
        """
        Получаем цены по API
        """

        URL = 'https://discounts-prices-api.wildberries.ru/api/v2/list/goods/filter'
        HEADERS = {'Authorization': self.TOKEN_KEY}
        PARAMS = {
            'limit': 1000
        }
        cards = []
       
        for attempt in range(max_attempts): 
            wait_time = 5 * (attempt + 1)
            try:
                response = requests.get(url=URL, headers=HEADERS, params=PARAMS)
                self.logger.info(f'Запрос URL: {URL}, попытка: {attempt + 1}/{max_attempts}')
                if response.status_code == 200:
                    data = response.json()
                    items = data.get('data', {}).get('listGoods', [])
                    self.logger.info(f'Получено: {len(items)} товара')
                    
                    for item in items:
                        card = {}
                        card['nmID'] = item.get('nmID', None)
                        card['price'] = item.get('sizes', [])[
                            0].get('price', None)
                        card['discount'] = item.get('discount', None)
                        card['discountedPrice'] = int(
                            round(card['price'] * (1 - card['discount']/100), 0))
                        card['clubDiscount'] = item.get('clubDiscount', 0)
                        card['clubDiscountedPrice'] = round(
                            card['discountedPrice'] * (1 - card['clubDiscount']/100), 1)
                        cards.append(card)
                    self.logger.success(f'Все цены для токена "{self.TOKEN_NAME}" успешно получены!')
                    return cards
                
                elif response.status_code == 429:
                    self.logger.warning(f"{response.status_code}. Превышен лимит запросов. Повторная попытка через {wait_time}s")
                    time.sleep(wait_time)
                    attempt += 1
                            
                elif response.status_code in [400, 401, 403, 404]:
                    error_details = response.text()
                    self.logger.error(f"{response.status_code}. Ошибка запроса: {error_details}")
                    break
                
                else:
                    error_details = response.text()
                    self.logger.error(f"{response.status_code}. Ошибка запроса: {error_details}. Повторная попытка через {wait_time}s")
                    time.sleep(wait_time)
                    attempt += 1

            except HTTPError as e:
                self.logger.error(f'Ошибка клиента: {e}. Повторная попытка через {wait_time}s')
                time.sleep(wait_time)
                attempt += 1
                
            except Timeout as e:
                self.logger.error(f'Превышено время запроса: {e}. Повторная попытка через {wait_time}s.')
                attempt += 1
                
            except Exception as e:
                self.logger.error(f'Ошибка запроса: {e}')
                break


    def get_orders(self, datefrom: str, max_attempts: int = 5) -> list:
        """
        Получаем заказы по API
        datefrom в формате dd.mm.yyyy
        """

        URL = 'https://statistics-api.wildberries.ru/api/v1/supplier/orders'
        HEADERS = {'Authorization': self.TOKEN_KEY}
        dateFrom = str(datetime.strptime(datefrom, "%d.%m.%Y").strftime("%Y-%m-%d"))
        PARAMS = {
            'dateFrom': dateFrom,
            'flag': 1
                  }

        orders = []
        
        for attempt in range(max_attempts):
            wait_time = 5 * (attempt + 1)
            try:
                response = requests.get(url=URL, headers=HEADERS, params=PARAMS)
                self.logger.info(f'Запрос URL: {URL}, попытка: {attempt + 1}/{max_attempts}')
                if response.status_code == 200:
                    data = response.json()
                    
                    # for item in data:
                    #     if item.get('isCancel', False) is False:
                    #         order = {}
                    #         order['brand'] = item.get('brand')
                    #         order['category'] = item.get('subject')
                    #         order['article'] = item.get('supplierArticle')
                    #         order['nmID'] = item.get('nmId')
                    #         order['priceWithDisc'] = item.get('priceWithDisc')
                    #         orders.append(order)
                    return data

                elif response.status_code == 429:
                    self.logger.warning(f"{response.status_code}. Превышен лимит запросов. Повторная попытка через {wait_time}s")
                    time.sleep(wait_time)
                    attempt += 1
                            
                elif response.status_code in [400, 401, 403, 404]:
                    error_details = response.text()
                    self.logger.error(f"{response.status_code}. Ошибка запроса: {error_details}")
                    break
                
                else:
                    error_details = response.text()
                    self.logger.error(f"{response.status_code}. Ошибка запроса: {error_details}. Повторная попытка через {wait_time}s")
                    time.sleep(wait_time)
                    attempt += 1

            except HTTPError as e:
                self.logger.error(f'Ошибка клиента: {e}. Повторная попытка через {wait_time}s')
                time.sleep(wait_time)
                attempt += 1
                
            except Timeout as e:
                self.logger.error(f'Превышено время запроса: {e}. Повторная попытка через {wait_time}s.')
                attempt += 1
                
            except Exception as e:
                self.logger.error(f'Ошибка запроса: {e}')
                break

    def get_supplies(self, max_attempts: int = 5) -> list:
        """
        Получение поставок
        """
        
        URL = 'https://supplies-api.wildberries.ru/api/v1/supplies'
        HEADERS = {'Authorization': self.TOKEN_KEY}
        dates = [{
            'from': (datetime.now(ZoneInfo('Europe/Moscow')).date() - relativedelta(months=1)).isoformat(),
            'type': 'supplyDate'
            }]
        statusIDs = [3]
        PARAMS = {
            "dates": dates,
            "statusIDs": statusIDs
        }

        def get_supplies_IDs() -> list:
            """ 
            Получаем ID всех созданных поставок
            """
            supplies_IDs = []
            for attempt in range(max_attempts):
                wait_time = 5 * (attempt + 1)
                try:
                    self.logger.info(f'Запрос URL: {URL}. Попытка: {attempt + 1}/{max_attempts}')
                    response = requests.post(url=URL, headers=HEADERS, json=PARAMS)
            
                    if response.status_code == 200:
                        data = response.json()
                        for item in data:
                            supply = {}
                            supply['supplyID'] = item.get('supplyID')
                            supplies_IDs.append(supply)

                        self.logger.success(f'ID всех поставок получены. Количество поставок: {len(supplies_IDs)}')
                        return supplies_IDs

                    elif response.status_code == 429:
                        self.logger.warning(f"{response.status_code}. Превышен лимит запросов. Повторная попытка через {wait_time}s")
                        time.sleep(wait_time)
                        attempt += 1  

                    elif response.status_code in [400, 401, 403, 404]:
                        error_details = response.text()
                        self.logger.error(f"{response.status_code}. Ошибка запроса: {error_details}")
                        break
                      
                    else:
                        error_details = response.text()
                        self.logger.error(f"{response.status_code}. Ошибка запроса: {error_details}. Повторная попытка через {wait_time}s")
                        time.sleep(wait_time)
                        attempt += 1

                except HTTPError as e:
                    self.logger.error(f'Ошибка клиента: {e}. Повторная попытка через {wait_time}s')
                    time.sleep(wait_time)
                    attempt += 1
                    
                except Timeout as e:
                    self.logger.error(f'Превышено время запроса: {e}. Повторная попытка через {wait_time}s.')
                    attempt += 1
                    
                except Exception as e:
                    self.logger.error(f'Ошибка запроса: {e}')
                    break
                

        def get_supplies_details():
            """
            По полученным ID получаем подробную информацию о всех поставках
            """
            supplies_details = []
            supplies_goods = []
            supplies_IDs = get_supplies_IDs()
            if supplies_IDs:
                for supply_ID in supplies_IDs: 
                    for attempt in range(max_attempts):
                        wait_time = 5 * (attempt + 1)
                        URL = f'https://supplies-api.wildberries.ru/api/v1/supplies/{supply_ID["supplyID"]}'
                        
                        try:
                            self.logger.info(f'Запрос: {URL}. Попытка {attempt + 1}/{max_attempts}')
                            response = requests.get(url=URL, headers=HEADERS)
                            if response.status_code == 200:
                                supply_item = response.json()
                                supply = {
                                        'supplyID': supply_ID["supplyID"],
                                        'supplyDate': datetime.strptime(datetime.fromisoformat(supply_item.get('supplyDate')).strftime('%d.%m.%Y'), '%d.%m.%Y').date(),
                                        'warehouse': supply_item.get('warehouseName'),
                                    }
                                supplies_details.append(supply)
                                break
                                
                            elif response.status_code == 429:
                                self.logger.warning(f"{response.status_code}. Превышен лимит запросов. Повторная попытка через {wait_time}s")
                                time.sleep(wait_time)
                                attempt += 1
                                        
                            elif response.status_code in [400, 401, 403, 404]:
                                error_details = response.text()
                                self.logger.error(f"{response.status_code}. Ошибка запроса: {error_details}")
                                break
                            
                            else:
                                error_details = response.text()
                                self.logger.error(f"{response.status_code}. Ошибка запроса: {error_details}. Повторная попытка через {wait_time}s")
                                time.sleep(wait_time)
                                attempt += 1
                                
                        except HTTPError as e:
                            self.logger.error(f'Ошибка клиента: {e}. Повторная попытка через {wait_time}s')
                            time.sleep(wait_time)
                            attempt += 1
                            
                        except Timeout as e:
                            self.logger.error(f'Превышено время запроса: {e}. Повторная попытка через {wait_time}s.')
                            attempt += 1
                            
                        except Exception as e:
                            self.logger.error(f'Ошибка запроса: {e}')
                            break
                                    
                         
                    for attempt in range(max_attempts):
                        URL = f'https://supplies-api.wildberries.ru/api/v1/supplies/{supply_ID["supplyID"]}/goods'
                        
                        try:
                            self.logger.info(f'Запрос: {URL}. Попытка {attempt + 1}/{max_attempts})')
                            response = requests.get(url=URL, headers=HEADERS)
                            if response.status_code == 200:
                                supplies_goods_json = response.json()
                                for supply_item in supplies_goods_json:
                                    supply_product = {
                                        'supplyID': supply_ID["supplyID"],
                                        'barcode': supply_item.get('barcode'),
                                        'article': supply_item.get('vendorCode'),
                                        'nmID': supply_item.get('nmID'),
                                        'quantity': supply_item.get('quantity')
                                    }
                                    supplies_goods.append(supply_product)
                                break
                                
                            elif response.status_code == 429:
                                self.logger.warning(f"{response.status_code}. Превышен лимит запросов. Повторная попытка через {wait_time}s")
                                time.sleep(wait_time)
                                attempt += 1
                                          
                            elif response.status_code in [400, 401, 403, 404]:
                                error_details = response.text()
                                self.logger.error(f"{response.status_code}. Ошибка запроса: {error_details}")
                                break
                            
                            else:
                                error_details = response.text()
                                self.logger.error(f"{response.status_code}. Ошибка запроса: {error_details}. Повторная попытка через {wait_time}s")
                                time.sleep(wait_time)
                                attempt += 1
                                
                        except HTTPError as e:
                            self.logger.error(f'Ошибка клиента: {e}. Повторная попытка через {wait_time}s')
                            time.sleep(wait_time)
                            attempt += 1
                            
                        except Timeout as e:
                            self.logger.error(f'Превышено время запроса: {e}. Повторная попытка через {wait_time}s.')
                            attempt += 1
                            
                        except Exception as e:
                            self.logger.error(f'Ошибка запроса: {e}')
                            break
                        
            return supplies_details, supplies_goods
        
        supplies_details, supplies_goods = get_supplies_details()
        if supplies_details:
            self.logger.success(f'Информация о {len(supplies_details)} поставках получена')
        if supplies_goods:
            self.logger.success(f'Содержание {len(supplies_details)} поставок получено')
            
        try:
            supplies = pd.merge(left=pd.DataFrame(supplies_goods), right=pd.DataFrame(supplies_details), on='supplyID')
            supplies = pd.merge(left=supplies, right=pd.read_excel('required_files/Склады по регионам.xlsx', index_col=False), on='warehouse')
            supplies = supplies[['supplyID', 'supplyDate', 'barcode', 'article', 'nmID', 'quantity', 'warehouse', 'region']]
            self.logger.success(f'Информация о всех поставках получена')
            return supplies
        
        except Exception:
            self.logger.error(f'Ошибка. Данные о поставках не получены!')
            return None
 
    def get_commission(self, max_attempts: int = 5) -> list:
        """
        Получаем комиссии по API
        """

        URL = 'https://common-api.wildberries.ru/api/v1/tariffs/commission'
        HEADERS = {'Authorization': self.TOKEN_KEY}
        PARAMS = {'locale': 'ru'}
        NEED_COMMISSION = ['Туалетная вода', 'Духи', 'Парфюмерные наборы', 'Гели']

        for attempt in range(max_attempts):
            wait_time = 5 * (attempt + 1)
            try:
                response = requests.get(url=URL, headers=HEADERS, params=PARAMS)
                self.logger.info(f'Запрос URL: {URL}, попытка: {attempt + 1}/{max_attempts}')
                if response.status_code == 200:
                    data = response.json()
                    data = [item for item in data['report'] if item.get('subjectName') in NEED_COMMISSION]

                    return data

                elif response.status_code == 429:
                    self.logger.warning(f"{response.status_code}. Превышен лимит запросов. Повторная попытка через {wait_time}s")
                    time.sleep(wait_time)
                    attempt += 1
                            
                elif response.status_code in [400, 401, 403, 404]:
                    error_details = response.text()
                    self.logger.error(f"{response.status_code}. Ошибка запроса: {error_details}")
                    break
                
                else:
                    error_details = response.text()
                    self.logger.error(f"{response.status_code}. Ошибка запроса: {error_details}. Повторная попытка через {wait_time}s")
                    time.sleep(wait_time)
                    attempt += 1

            except HTTPError as e:
                self.logger.error(f'Ошибка клиента: {e}. Повторная попытка через {wait_time}s')
                time.sleep(wait_time)
                attempt += 1
                
            except Timeout as e:
                self.logger.error(f'Превышено время запроса: {e}. Повторная попытка через {wait_time}s.')
                attempt += 1
                
            except Exception as e:
                self.logger.error(f'Ошибка запроса: {e}')
                break


class WebDriver:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, user_agent: str = None, url: str = None, cookies_need: str = None):
        if not hasattr(self, '_initialized') or not self._initialized:
            self.driver = None 
            self.user_agent = user_agent or USER_AGENT
            self.url = url or WB_URL
            self.cookies_need = cookies_need or COOKIES_NEED
            self.logger = logger
            self.logger.info(f'Класс WebDriver инициализирован')
            self._initialized = True
        
    def _get_wbaas_token(self, max_attempts: int = 3) -> str:
        driver = Driver(
            uc=True,
            headless=True,
            agent=self.user_agent
        )
        
        try:
            driver.open(self.url)
            for attempt in range(max_attempts):
                self.logger.info(f'Получение wbaas токена, попытка: {attempt + 1}/{max_attempts}')
                wait_time = 5 * (attempt + 1)
                cookies = driver.execute_cdp_cmd('Network.getAllCookies', {})
                
                for cookie in cookies.get('cookies', []):
                    if cookie.get('name') == self.cookies_need:
                        logger.success(f'Токен wbaas получен!')
                        wbaas_token = cookie.get('value')
                        return wbaas_token
                    
                    else:
                        logger.error(f'Ошибка получения кукки. Повторная попытка через {wait_time}s')
                        time.sleep(wait_time)
                        
            return None
        
        finally:
            driver.quit()

    def get_supplier_prices(self, supplier: str | int) -> list:
        URL = 'https://www.wildberries.ru/__internal/catalog/sellers/v4/catalog'
        page = 1
        COOKIES = {
            COOKIES_NEED: WebDriver()._get_wbaas_token()
        }
        HEADERS = {
            'user-agent': USER_AGENT
        }
        PARAMS = {
            'ab_testing': 'false',
            'appType': '1',
            'curr': 'rub',
            'dest': '123587059',
            'hide_dtype': '9',
            'hide_vflags': '4294967296',
            'lang': 'ru',
            'page': str(page),
            'sort': 'popular',
            'spp': '30',
            'supplier': str(supplier),
            'uclusters': '2',
        }
        
        try:
            response = requests.get(
                url=URL,
                params=PARAMS,
                cookies=COOKIES,
                headers=HEADERS,
                )

            result = response.json()
            total_products = result.get('total', 0)
            pages = (total_products//100) + 1
            
        except Exception:
            pass
        
        if response.status_code == 200 and total_products > 0:
            self.logger.info(f'Сайт Wildberries доступен, данные собираются')
            goods = []
            for page in range(pages):
                PARAMS = PARAMS.copy()
                PARAMS['page'] = str(page + 1)   
                       
                self.logger.info(f'Получение товаров {page + 1} страницы')
                response = requests.get(
                'https://www.wildberries.ru/__internal/catalog/sellers/v4/catalog',
                params=PARAMS,
                cookies=COOKIES,
                headers=HEADERS,
                )
                
                if response.status_code == 200:
                    result = response.json()
                    products = result.get('products', [])
                    
                    for product in products:
                        good = {}
                        good['supplier'] = product.get('supplier')            
                        good['brand'] = product.get('brand')
                        good['nmID'] = product.get('id')
                        good['name'] = product.get('name')
                        good['wbPrice'] = product.get('sizes')[0].get('price').get('product')/100
                        goods.append(good)
                    self.logger.info(f'Товары {page + 1} страницы получены')
            self.logger.info(f'Все товары получены: {len(goods)}')
            return goods
        else:
            self.logger.error(f'{response.status_code}. Ошибка доступа к сайту Wildberries!')
            return None      
                    
        
    def get_wallet_discount_percent(self) -> int:
        COOKIES = {
            COOKIES_NEED: WebDriver()._get_wbaas_token()
        }
        HEADERS = {
            'user-agent': USER_AGENT
        }
        
        self.logger.info("Получаем настройки скидок")
        try:
            response = requests.get(SETTINGS_URL, headers=HEADERS, cookies=COOKIES, timeout=5)
            response.raise_for_status()
            settings = response.json().get("variables")
            max_price = int(settings.get("wlt1DiscountDisplayMaxPrice", 0))
            min_delta = int(settings.get("pricesDeltaToShowSale", 0))
        except Exception:
            self.logger.exception("Ошибка при получении настроек скидок")
            return 0, 0, 0
        self.logger.success("Настройки скидок успешно получены")

        
        self.logger.info("Получаем процент скидки для типа «Незалогиненный кошелёк»")
        try:
            response = requests.get(DEFAULT_PAYMENT_URL, headers=HEADERS, cookies=COOKIES, timeout=5)
            response.raise_for_status()
            payload = response.json()    
        except Exception:
            self.logger.exception("Ошибка при получении default-payment.json")
            return 0, 0, 0
        self.logger.debug("Ответ default-payment.json получен")
        
        if payload.get("state") != 0:
            self.logger.warning("Скидка ВБ Кошелька не применяется")
            return 0, 0, 0

        for item in payload.get("data", []):
            self.logger.debug("Проверяем тип оплаты на сайте")

            if (item.get("wc_type") == "Незалогиненный кошелёк"
                and item.get("is_active") is True):
                try:
                    discount = item["discount_value"]
        
                except Exception:
                    self.logger.warning("Некорректное значение скидки")
                    return 0, 0, 0

                self.logger.success("Найдена скидка для ВБ Кошелька")
                return int(max_price), int(min_delta), int(discount)

        self.logger.warning("Скидка для «Незалогиненный кошелёк» не найдена")
        return 0, 0, 0

 
class Reports:
  
    def __init__(self, TOKEN_NAME: str = None, supplier: int | str = None):
            self.TOKEN_NAME = TOKEN_NAME
            if self.TOKEN_NAME != None:
                self.TOKEN_KEY = os.getenv(TOKEN_NAME)
            self.supplier = supplier
            self.logger = logger
            self.logger.info(f'Отчеты инициализированы')
            
    def nomenclature(self) -> pd.DataFrame:
        nomenclature = pd.DataFrame(APIRequests(self.TOKEN_NAME).get_nomenclature())
        # file_name = 'Номенклатура.xlsx'
        # with pd.ExcelWriter(file_name) as writer:
        #     nomenclature.to_excel(writer, sheet_name='Номенклатура', index=False)
        #     logger.success(f'Файл {file_name} сохранен!')
        return nomenclature
        
    def supplies(self) -> pd.DataFrame:
        nomenclature = pd.DataFrame(APIRequests(self.TOKEN_NAME).get_nomenclature())
        supplies = pd.DataFrame(APIRequests(self.TOKEN_NAME).get_supplies())
        
        if all(not df.empty for df in [nomenclature, supplies]):
            supplies = supplies.merge(right=nomenclature[['article', 'name']], on='article')
            supplies = supplies[['supplyID','supplyDate', 'barcode', 'article', 'nmID', 'name', 'quantity', 'region', 'warehouse']]
            supplies = supplies.rename(columns={
                'supplyID': 'Номер поставки', 
                'supplyDate': 'Дата поставки', 
                'barcode': 'Штрихкод', 
                'article': 'Артикул продавца',
                'nmID': 'Артикул WB',
                'name': 'Наименование',
                'quantity': 'Количество',
                'region': 'Регион',
                'warehouse': 'Склад'
            })
            supplies = supplies.sort_values(by='Дата поставки', ascending=False)
            file_name = f'Поставки {self.TOKEN_NAME}.xlsx'
            with pd.ExcelWriter(file_name) as writer:
                supplies.to_excel(writer, sheet_name='Поставки по складам', index=False)
                supplies = supplies[['Артикул продавца', 'Артикул WB', 'Наименование', 'Количество']].groupby(['Артикул продавца', 'Артикул WB', 'Наименование'], as_index=False)['Количество'].sum()
                supplies.to_excel(writer, sheet_name='Поставки по товарам', index=False)
                logger.success(f'Файл {file_name} сохранен!')
            return supplies

    def prices(self) -> pd.DataFrame:
        if self.TOKEN_NAME != None:
            nomenclature = pd.DataFrame(APIRequests(self.TOKEN_NAME).get_nomenclature())
            prices_API_df = pd.DataFrame(APIRequests(self.TOKEN_NAME).get_prices())
        if self.supplier != None:
            prices_WB_df = pd.DataFrame(WebDriver().get_supplier_prices(self.supplier))
        if self.TOKEN_NAME != None or self.supplier != None:
            max_price, min_delta, wallet_discount = WebDriver().get_wallet_discount_percent()
            
        # Полноценный отчет
        if self.TOKEN_NAME != None and self.supplier != None:
            if all(not df.empty for df in [nomenclature, prices_API_df, prices_WB_df]) and (0 not in (max_price, min_delta, wallet_discount)):
                nomenclature = nomenclature[['category', 'nmID', 'article', 'name']]
                prices_WB_df = prices_WB_df.drop(['name'], axis=1)
                prices = pd.merge(left=nomenclature, right=prices_API_df, on='nmID', how='left')
                prices = pd.merge(left=prices, right=prices_WB_df, on='nmID', how='left')
                prices['wbDiscount'] = round((1 - prices['wbPrice']/prices['clubDiscountedPrice']) * 100)
                prices = prices[['supplier', 'brand', 'category', 'article', 'nmID', 'name', 'price', 'discount', 'discountedPrice', 'wbDiscount', 'wbPrice']]
                prices.loc[(prices['wbPrice'] > 0), 'max_price'] = max_price
                prices.loc[(prices['wbPrice'] > 0), 'min_delta'] = min_delta
                prices.loc[(prices['wbPrice'] > 0), 'wallet_discount'] = wallet_discount
                prices.loc[(prices['wbPrice'] < prices['max_price']), 'personal_price'] = np.floor(prices['wbPrice'] * (1 - (prices['wallet_discount']+1)/100))
                prices.loc[(prices['wbPrice'] >= prices['max_price']), 'personal_price'] = prices['wbPrice']

                prices = prices.drop(columns=['max_price', 'min_delta'], axis=1)
                prices = prices.rename(columns={
                                'supplier': 'Продавец', 
                                'brand': 'Бренд', 
                                'category': 'Категория',
                                'article': 'Артикул продавца',
                                'nmID': 'Артикул WB',
                                'name': 'Наименование',
                                'price': 'Цена',
                                'discount': 'Скидка',
                                'discountedPrice': 'Цена со скидкой',
                                'wbDiscount': 'Скидка WB',
                                'wbPrice': 'Цена со скидкой WB',
                                'wallet_discount': 'Скидка WB Wallet',
                                'personal_price': 'Цена покупателя'
                            })

        # Отчет только по сайту
        if self.supplier != None:
            if not prices_WB_df.empty and (0 not in (max_price, min_delta, wallet_discount)):
                prices = prices_WB_df
        
        # file_name = f'Цены {self.TOKEN_NAME}.xlsx'
        # with pd.ExcelWriter(file_name) as writer:
        #     prices.to_excel(writer, sheet_name='Цены', index=False)
        #     logger.success(f'Файл {file_name} сохранен!')
        return prices
            
    def orders(self) -> pd.DataFrame:
        orders = pd.DataFrame(APIRequests().get_orders())
        # file_name = 'Заказы.xlsx'
        # with pd.ExcelWriter(file_name) as writer:
        #     orders.to_excel(writer, sheet_name='Заказы', index=False)
        #     logger.success(f'Файл {file_name} сохранен!')   
        return orders
    
    
import uuid
def main():    
    
    
if __name__ == '__main__':
    main()