import os
import asyncio
import time
from loguru import logger
from datetime import datetime
from zoneinfo import ZoneInfo
from dateutil.relativedelta import relativedelta
import math
import aiohttp
import pandas as pd
from dotenv import load_dotenv
import gspread
from seleniumbase import Driver
import requests
from fake_useragent import UserAgent


# UA = UserAgent()
# USER_AGENT = UA.chrome
# URL = 'https://www.wildberries.ru'
# COOKIES_NEED = 'x_wbaas_token'
    
# class WebDriverCookies:
#     def __init__(self, user_agent: str = None, url: str = None, cookies_need: str = None):
#         self.user_agent = user_agent or USER_AGENT
#         self.url = url or URL
#         self.cookies_need = cookies_need or COOKIES_NEED
    
#     def get_token(self) -> str:
#         driver = Driver(
#             uc=True,
#             headed=True,
#             agent=self.user_agent
#         )
        
#         try:
#             driver.open(self.url)
#             for i in range(3):
#                 driver.get_cookies
                
#         finally:
#             driver.quit()
        


# x_wbaas_token = '1.1000.26736a9708a340bdbc4664025f5f98aa.MTV8ODAuOTMuMTg3Ljg5fE1vemlsbGEvNS4wIChXaW5kb3dzIE5UIDEwLjA7IFdpbjY0OyB4NjQpIEFwcGxlV2ViS2l0LzUzNy4zNiAoS0hUTUwsIGxpa2UgR2Vja28pIENocm9tZS8xNDQuMC4wLjAgU2FmYXJpLzUzNy4zNnwxNzcxMjQxMzE3fHJldXNhYmxlfDJ8ZXlKb1lYTm9Jam9pSW4wPXwwfDN8MTc3MDYzNjUxN3wx.MEUCIH7UsEWL3ErVenJ4LG2XkwiKG+4eJGTxeQHAQg2bQaZAAiEAsQBlu+3I5bwj9Y7wr1oBfHy5FA6bVa8F9jnhFyZk8vU='
# URL = ''
# PARAMS = {
#         "ab_testing":"false",
#         "appType":"1",
#         "curr":"rub",
#         "dest":"123587059",
#         "hide_dtype":"9",
#         "hide_vflags":"4294967296",
#         "lang":"ru",
#         "page":"1",
#         "sort":"popular",
#         "spp":"30",
#         "supplier":"53699",
#         "uclusters":"3"
#     }
# HEADERS = {
#             }

# driver.open('https://www.wildberries.ru')
# time.sleep(10)
# driver.quit()

# response = requests.get(url=URL, headers=HEADERS, params=PARAMS)
# print(HEADERS)
# print(response)
# print(response.status_code)

# response = requests.get(
#     url='https://www.wildberries.ru/__internal/catalog/sellers/v4/catalog',
#     params={
#         "ab_testing":"false",
#         "appType":"1",
#         "curr":"rub",
#         "dest":"123587059",
#         "hide_dtype":"9",
#         "hide_vflags":"4294967296",
#         "lang":"ru",
#         "page":"1",
#         "sort":"popular",
#         "spp":"30",
#         "supplier":"53699",
#         "uclusters":"3"
#     },
#     headers={
#         "accept":"*/*",
#         "accept-language":"ru,en;q=0.9",
#         "authorization":"Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpYXQiOjE3NzAwMDIyNzYsInVzZXIiOiI4NDM5Mzk1MSIsInNoYXJkX2tleSI6IjEzIiwiY2xpZW50X2lkIjoid2IiLCJzZXNzaW9uX2lkIjoiMDY4ZDEyZTBhMTQ2NDgzYWIzNTdkNDhlYTI4OWFlZTIiLCJwaG9uZSI6InllT2dPVlh3Q2R4VEZUTTVUTEUrd1E9PSIsInZhbGlkYXRpb25fa2V5IjoiMTgxYWZlYWE4ODk0YTA2NTExOGUzNmVjOWQ5OWY0ZTdlOGUxZjE2YTk4ZTM3YjQ0NDhmNTQ1N2Y0YTExOTFkYyIsInVzZXJfcmVnaXN0cmF0aW9uX2R0IjoxNjc0MTEwOTM5LCJ2ZXJzaW9uIjoyfQ.ib_g4_8bnpxgdvQi-yD-bvGNxxjC2McUPT5ksIh169710Hm2VuUx-jIEG8_U7yvD2nlnA_OuLtVCVDheB-z-4vHTyRqqH8txrUxtIpWps8h7ZHDToCXEQjbuyAjdUkuvKp-aHOvaoQO2SBqX1_guHBYKC93ewjekHYDXiY0pn3sJBxO-0uP2TH1ry6LwIGK4_Z156mYoyl9g45zNTWSKTIB76esRPOd3tC4A7okpZOF7EQeTT6s0eXSj3jVkcGuU2PdOco2ZgIm7fgu9aVxHVU_Jc-7EM5Z-qibudEXwqds0ag41G-v57SDqR_xx4j4xE1trsEjGH-kLGqLLdwehdA",
#         "deviceid":"site_ead5724dd3aa4c0fb8f949aa11104dac",
#         "priority":"u=1, i",
#         "referer":"https://www.wildberries.ru/seller/53699",
#         "sec-ch-ua":"\"Chromium\";v=\"142\", \"YaBrowser\";v=\"25.12\", \"Not_A Brand\";v=\"99\", \"Yowser\";v=\"2.5\"",
#         "sec-ch-ua-mobile":"?1",
#         "sec-ch-ua-platform":"\"Android\"",
#         "sec-fetch-dest":"empty",
#         "sec-fetch-mode":"cors",
#         "sec-fetch-site":"same-origin",
#         "user-agent":"Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Mobile Safari/537.36",
#         "x-requested-with":"XMLHttpRequest",
#         "x-spa-version":"13.21.4"
#     },
#     cookies={
#         "_wbauid":"401878001768557149; _cp=1; external-locale=ru; _wbauid=8574176031768559539; wbx-validation-key=b61a6104-e1aa-4b51-b491-e4c46340b24d; feedbacks_link_accepted=1; x_wbaas_token=1.1000.cffbe45167d545faae560828521067ef.MHwxNzguNzQuNjguMTA2fE1vemlsbGEvNS4wIChXaW5kb3dzIE5UIDEwLjA7IFdpbjY0OyB4NjQpIEFwcGxlV2ViS2l0LzUzNy4zNiAoS0hUTUwsIGxpa2UgR2Vja28pIENocm9tZS8xNDIuMC4wLjAgWWFCcm93c2VyLzI1LjEyLjAuMCBTYWZhcmkvNTM3LjM2fDE3NzA5Nzc4NzR8cmV1c2FibGV8MnxleUpvWVhOb0lqb2lJbjA9fDB8M3wxNzcwMzczMDc0fDE=.MEUCIFNJ3iCdP6oNQ7C3MYfJ9THR7xiAtkTOHtu5SDS1xQ5pAiEA3+R3CI4wwjUxYpTIzjz/spZBw/kM6EYI2g82pfZYu7s=; routeb=1770002277.354.628.657647|4cbe85fb742f9006ed4b10eaae805e6b; x-supplier-id-external=064e1dc5-9e31-4107-a6d6-2f9abd3bbcec; __zzatw-wb=MDA0dC0cTHtmcDhhDHEWTT17CT4VHThHKHIzd2UxP2gmYlBeIDVRP0FaW1Q4NmdBEXUmCQg3LGBwVxlRExpceEdXeiwgEXdtK08JEWFAQmllbQwtUlFRS19/Dg4/aU5ZQ11wS3E6EmBWGB5CWgtMeFtLKRZHGzJhXkZpdRUNPA5kQUNvLC5EZ1BjSl8ndFZVeidPQ35vJ08PFBU/d19vG3siXyoIJGM1Xz9EaVhTMCpYQXt1J3Z+KmUzPGwkX0dbJ0NXU38oGg1pN2wXPHVlLwkxLGJ5MVIvE0tsP0caRFpbQDsyVghDQE1HFF9BWncyUlFRS2EQR0lrZU5TQixmG3EVTQgNND1aciIPWzklWAgSPwsmIBh3ayVXfw1hQ0Rvbxt/Nl0cOWMRCxl+OmNdRkc3FSR7dSYKCTU3YnAvTCB7SykWRxsyYV5GaXUVTw0PGD51KHgmRCIgYERdIENcSjIrTRd0bVlYOD0XQHMnLl5uVxlRDxZhDhYYRRcje0I3Yhk4QhgvPV8/YngiD2lIYCZDVU8JJRsYe20kS3FPLH12X30beylOIA0lVBMhP05yIuyW0A==; cfidsw-wb=5KPM0zh0WlXrSn6uUaLkStpHqcwiwjpLPOgabOVQM46wJkSPuQs+exiJ+I5N4MKWLNSa2LnAMlkVXOgFugjGBdES6y7MjbbLGKoSEvTYqU7f/iTvh+Q8RFbYQvB/OlYUe/Oq2z2rSGxABY85P9psNT2oK3DqsPa985c1KvbFbw=="
#     },
    
# )

# print(response.text)


# class ParseRequests:
#     """
#     Docstring for ParseRequests
#     """
#     def __init__(self, session: aiohttp.ClientSession):
#         self.session = session
#         logger.info('Create parse class')

#     async def fetch_prices(self) -> list:
#         """Получаем товары со страницы с ценами на сайте"""


#         while page <= total_pages:
#             headers = {
#                 'UserAgent': fua.random
#             }
#             url = f'https://www.wildberries.ru/__internal/u-catalog/sellers/v4/catalog?ab_testing=false&ab_testing=false&appType=1&curr=rub&dest=-{dest}&hide_dtype=11&lang=ru&page={page}&sort=popular&spp=30&supplier={self.seller_id}'

#             try:
#                 async with self.session.get(url, headers=headers) as response:
#                     print(f'Запрос: {url}')

#                     if response.status == 200:
#                         data = await response.json()
#                         products = data.get('products', [])

#                         total_pages = math.ceil(data.get('total', 1) / 100)

#                         print(
#                             f"POST_CODE {response.status} \n"
#                             f"Seller {self.seller_id}, page {page}: \n"
#                             f"Found {len(products)} products, total pages: {total_pages} \n"
#                         )

#                         for product in products:
#                             wb_price = product.get('sizes', [{}])[0].get(
#                                 'price', {}).get('product', 0) / 100
#                             personal_price = wb_price * \
#                                 (1 - self.personal_discount/100)

#                             item = {
#                                 'WB_ID': product.get('id'),
#                                 'wb_price': wb_price,
#                                 'personal_discount': self.personal_discount,
#                                 'personal_price': math.floor(personal_price)
#                             }

#                             items.append(item)
#                         page = page + 1

#                     elif response.status == 429:
#                         print("Too many requests. Waiting 10 seconds...")
#                         await asyncio.sleep(10)

#                     else:
#                         print(
#                             f"Error {response.status}. Retrying in 5 seconds...")
#                         await asyncio.sleep(5)

#             except aiohttp.ClientError as e:
#                 print(f'Error {e}. Retrying in 5 seconds...')
#                 await asyncio.sleep(5)

#         return items


class APIRequests:
    def __init__(self, session: aiohttp.ClientSession, TOKEN_KEY: str):
        load_dotenv()
        self.TOKEN_KEY = TOKEN_KEY
        self.TOKEN = os.getenv(self.TOKEN_KEY)
        self.session = session
        self.logger = logger
        self.logger.info(f'Токен {self.TOKEN_KEY} инициализирован')

    async def get_nomenclature(self, max_attempts: int = 5) -> list:
        """ 
        Получаем список номенклатуры по API
        """

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
                    self.logger.info(f'Запрос URL: {url}, попытка: {attempt + 1}/{max_attempts}')
                    async with self.session.post(url=url, headers=headers, json=params) as response:
                        
                        if response.status == 200:
                            data = await response.json()
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
                                
                        elif response.status == 429:
                            self.logger.warning(f"{response.status}. Превышен лимит запросов. Повторная попытка через {wait_time}s")
                            await asyncio.sleep(wait_time)
                            attempt += 1
                            
                        elif response.status in [400, 401, 403, 404]:
                            error_details = await response.text()
                            self.logger.error(f"{response.status}. Ошибка запроса: {error_details}")
                            total = 0
                            break

                        else:
                            error_details = await response.text()
                            self.logger.error(f"{response.status}. Ошибка запроса: {error_details}. Повторная попытка через {wait_time}s")
                            await asyncio.sleep(wait_time)
                            attempt += 1

                except aiohttp.ClientError as e:
                    self.logger.error(f'Ошибка клиента: {e}. Повторная попытка через {wait_time}s')
                    await asyncio.sleep(wait_time)
                    attempt += 1
                except asyncio.TimeoutError as e:
                    self.logger.error(f'Превышено время запроса: {e}. Повторная попытка через {wait_time}s.')
                    attempt += 1
                except Exception as e:
                    self.logger.error(f'Ошибка запроса: {e}')
                    break
        return cards

    async def get_prices(self, max_attempts: int = 5) -> list:
        """
        Получаем цены по API
        """

        url = 'https://discounts-prices-api.wildberries.ru/api/v2/list/goods/filter'
        headers = {'Authorization': self.TOKEN}
        cards = []
        params = {
            'limit': 1000
        }
       
        for attempt in range(max_attempts): 
            wait_time = 5 * (attempt + 1)
            try:
                async with self.session.get(url=url, headers=headers, params=params) as response:
                    self.logger.info(f'Запрос URL: {url}, попытка: {attempt + 1}/{max_attempts}')

                    if response.status == 200:
                        data = await response.json()
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
                        self.logger.success(f'Все цены для токена "{self.TOKEN_KEY}" успешно получены!')
                        return cards

                    elif response.status == 429:
                                self.logger.warning(f"{response.status}. Превышен лимит запросов. Повторная попытка через {wait_time}s")
                                await asyncio.sleep(wait_time)
                                attempt += 1
                                
                    elif response.status in [400, 401, 403, 404]:
                        error_details = await response.text()
                        self.logger.error(f"{response.status}. Ошибка запроса: {error_details}")
                        break
                    
                    else:
                        error_details = await response.text()
                        self.logger.error(f"{response.status}. Ошибка запроса: {error_details}. Повторная попытка через {wait_time}s")
                        await asyncio.sleep(wait_time)
                        attempt += 1

            except aiohttp.ClientError as e:
                self.logger.error(f'Ошибка клиента: {e}. Повторная попытка через {wait_time}s')
                await asyncio.sleep(wait_time)
                attempt += 1
                
            except asyncio.TimeoutError as e:
                self.logger.error(f'Превышено время запроса: {e}. Повторная попытка через {wait_time}s.')
                attempt += 1
                
            except Exception as e:
                self.logger.error(f'Ошибка запроса: {e}')
                break


    async def get_orders(self, max_attempts: int = 5) -> list:
        """
        Получаем заказы по API
        """

        url = 'https://statistics-api.wildberries.ru/api/v1/supplier/orders'
        headers = {'Authorization': self.TOKEN}
        dateFrom = (datetime.now(ZoneInfo('Europe/Moscow')).date() -
                    relativedelta(months=1)).isoformat()
        params = {'dateFrom': dateFrom}
        orders = []
        
        for attempt in range(max_attempts):
            wait_time = 5 * (attempt + 1)
            try:
                async with self.session.get(url=url, headers=headers, params=params) as response:
                    self.logger.info(f'Запрос URL: {url}, попытка: {attempt + 1}/{max_attempts}')

                    if response.status == 200:
                        data = await response.json()

                        for item in data:
                            if item.get('isCancel', False) is False:
                                order = {}
                                order['region'] = item.get('oblastOkrugName')
                                order['article'] = item.get('supplierArticle')
                                order['nmID'] = item.get('nmId')
                                order['category'] = item.get('subject')
                                order['brand'] = item.get('brand')

                                orders.append(order)
                        return orders

                    elif response.status == 429:
                                self.logger.warning(f"{response.status}. Превышен лимит запросов. Повторная попытка через {wait_time}s")
                                await asyncio.sleep(wait_time)
                                attempt += 1
                                
                    elif response.status in [400, 401, 403, 404]:
                        error_details = await response.text()
                        self.logger.error(f"{response.status}. Ошибка запроса: {error_details}")
                        break
                    
                    else:
                        error_details = await response.text()
                        self.logger.error(f"{response.status}. Ошибка запроса: {error_details}. Повторная попытка через {wait_time}s")
                        await asyncio.sleep(wait_time)
                        attempt += 1

            except aiohttp.ClientError as e:
                self.logger.error(f'Ошибка клиента: {e}. Повторная попытка через {wait_time}s')
                await asyncio.sleep(wait_time)
                attempt += 1
                
            except asyncio.TimeoutError as e:
                self.logger.error(f'Превышено время запроса: {e}. Повторная попытка через {wait_time}s.')
                attempt += 1
                
            except Exception as e:
                self.logger.error(f'Ошибка запроса: {e}')
                break

    async def get_supplies(self, max_attempts: int = 5) -> list:
        """
        Получение поставок
        """
        
        url = 'https://supplies-api.wildberries.ru/api/v1/supplies'
        headers = {'Authorization': self.TOKEN}
        dates = [{
            'from': (datetime.now(ZoneInfo('Europe/Moscow')).date() - relativedelta(months=1)).isoformat(),
            'type': 'supplyDate'
            }]
        statusIDs = [3]
        params = {
            "dates": dates,
            "statusIDs": statusIDs
        }

        async def get_supplies_IDs() -> list:
            """ 
            Получаем ID всех созданных поставок
            """
            supplies_IDs = []
            for attempt in range(max_attempts):
                wait_time = 5 * (attempt + 1)
                try:
                    self.logger.info(f'Запрос URL: {url}. Попытка: {attempt + 1}/{max_attempts}')
                    async with self.session.post(url=url, headers=headers, json=params) as response:
                    
                        if response.status == 200:
                            data = await response.json()
                            for item in data:
                                supply = {}
                                supply['supplyID'] = item.get('supplyID')
                                supplies_IDs.append(supply)
                            
                            self.logger.success(f'ID всех поставок получены. Количество поставок: {len(supplies_IDs)}')
                            return supplies_IDs
                        
                        elif response.status == 429:
                            self.logger.warning(f"{response.status}. Превышен лимит запросов. Повторная попытка через {wait_time}s")
                            await asyncio.sleep(wait_time)
                            attempt += 1  
                                                
                        elif response.status in [400, 401, 403, 404]:
                            error_details = await response.text()
                            self.logger.error(f"{response.status}. Ошибка запроса: {error_details}")
                            break
                        
                        else:
                            error_details = await response.text()
                            self.logger.error(f"{response.status}. Ошибка запроса: {error_details}. Повторная попытка через {wait_time}s")
                            await asyncio.sleep(wait_time)
                            attempt += 1

                except aiohttp.ClientError as e:
                    self.logger.error(f'Ошибка клиента: {e}. Повторная попытка через {wait_time}s')
                    await asyncio.sleep(wait_time)
                    attempt += 1
                    
                except asyncio.TimeoutError as e:
                    self.logger.error(f'Превышено время запроса: {e}. Повторная попытка через {wait_time}s.')
                    attempt += 1
                    
                except Exception as e:
                    self.logger.error(f'Ошибка запроса: {e}')
                    break
                

        async def get_supplies_details():
            """
            По полученным ID получаем подробную информацию о всех поставках
            """
            supplies_details = []
            supplies_goods = []
            supplies_IDs = await get_supplies_IDs()
            if supplies_IDs:
                for supply_ID in supplies_IDs: 
                    for attempt in range(max_attempts):
                        wait_time = 5 * (attempt + 1)
                        url = f'https://supplies-api.wildberries.ru/api/v1/supplies/{supply_ID["supplyID"]}'
                        
                        try:
                            self.logger.info(f'Запрос: {url}. Попытка {attempt + 1}/{max_attempts}')
                            async with self.session.get(url=url, headers=headers) as response:
                                if response.status == 200:
                                    supply_item = await response.json()
                                    supply = {
                                            'supplyID': supply_ID["supplyID"],
                                            'warehouse': supply_item.get('warehouseName'),
                                        }

                                    supplies_details.append(supply)
                                    break
                                    
                                elif response.status == 429:
                                    self.logger.warning(f"{response.status}. Превышен лимит запросов. Повторная попытка через {wait_time}s")
                                    await asyncio.sleep(wait_time)
                                    attempt += 1
                                            
                                elif response.status in [400, 401, 403, 404]:
                                    error_details = await response.text()
                                    self.logger.error(f"{response.status}. Ошибка запроса: {error_details}")
                                    break
                                
                                else:
                                    error_details = await response.text()
                                    self.logger.error(f"{response.status}. Ошибка запроса: {error_details}. Повторная попытка через {wait_time}s")
                                    await asyncio.sleep(wait_time)
                                    attempt += 1

                        except aiohttp.ClientError as e:
                            self.logger.error(f'Ошибка клиента: {e}. Повторная попытка через {wait_time}s')
                            await asyncio.sleep(wait_time)
                            attempt += 1
                            
                        except asyncio.TimeoutError as e:
                            self.logger.error(f'Превышено время запроса: {e}. Повторная попытка через {wait_time}s.')
                            attempt += 1
                            
                        except Exception as e:
                            self.logger.error(f'Ошибка запроса: {e}')
                            break
                        
                         
                    for attempt in range(max_attempts):
                        url = f'https://supplies-api.wildberries.ru/api/v1/supplies/{supply_ID["supplyID"]}/goods'
                        
                        try:
                            self.logger.info(f'Запрос: {url}. Попытка {attempt + 1}/{max_attempts})')
                            async with self.session.get(url=url, headers=headers) as response:
                                if response.status == 200:
                                    supplies_goods_json = await response.json()
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
                                    
                                elif response.status == 429:
                                    self.logger.warning(f"{response.status}. Превышен лимит запросов. Повторная попытка через {wait_time}s")
                                    await asyncio.sleep(wait_time)
                                    attempt += 1
                                              
                                elif response.status in [400, 401, 403, 404]:
                                    error_details = await response.text()
                                    self.logger.error(f"{response.status}. Ошибка запроса: {error_details}")
                                    break
                                
                                else:
                                    error_details = await response.text()
                                    self.logger.error(f"{response.status}. Ошибка запроса: {error_details}. Повторная попытка через {wait_time}s")
                                    await asyncio.sleep(wait_time)
                                    attempt += 1

                        except aiohttp.ClientError as e:
                            self.logger.error(f'Ошибка клиента: {e}. Повторная попытка через {wait_time}s')
                            await asyncio.sleep(wait_time)
                            attempt += 1
                            
                        except asyncio.TimeoutError as e:
                            self.logger.error(f'Превышено время запроса: {e}. Повторная попытка через {wait_time}s.')
                            attempt += 1
                            
                        except Exception as e:
                            self.logger.error(f'Ошибка запроса: {e}')
                            break
                        
            return supplies_details, supplies_goods
        
        supplies_details, supplies_goods = await get_supplies_details()
        if supplies_details:
            self.logger.success(f'Информация о {len(supplies_details)} поставках получена')
        if supplies_goods:
            self.logger.success(f'Содержание {len(supplies_details)} поставок получено')
            
        try:
            supplies = pd.merge(left=pd.DataFrame(supplies_goods), right=pd.DataFrame(supplies_details), on='supplyID')
            supplies = pd.merge(left=supplies, right=pd.read_excel('required_files/Склады по регионам.xlsx', index_col=False), on='warehouse')
            supplies = supplies[['supplyID', 'barcode', 'article', 'nmID', 'quantity', 'warehouse', 'region']]
            self.logger.success(f'Информация о всех поставках получена')
            return supplies
        
        except Exception:
            self.logger.error(f'Ошибка. Данные о поставках не получены!')
            return None

class Reports:
    def __init__(self):
        pass    
     
    async def supplies(self) -> None:
        async with aiohttp.ClientSession() as supplies_session:
            api_requests = APIRequests(session=supplies_session, TOKEN_KEY='КОСТРИК')        
            result = await asyncio.gather(
                    api_requests.get_nomenclature(),
                    api_requests.get_supplies()
            )
        nomenclature, supplies = result[0], result[1]
        supplies = pd.merge(left=pd.DataFrame(supplies), right=pd.DataFrame(nomenclature)[['article', 'name']], on='article')
        supplies = supplies[['supplyID', 'barcode', 'article', 'nmID', 'name', 'quantity', 'region', 'warehouse']]
        
        file_name = 'Поставки.xlsx'
        with pd.ExcelWriter(file_name) as writer:
            supplies.to_excel(writer, sheet_name='Поставки по складам', index=False)
            supplies = supplies[['article', 'nmID', 'name', 'quantity']].groupby(['article', 'nmID', 'name'], as_index=False)['quantity'].sum()
            supplies.to_excel(writer, sheet_name='Поставки по товарам', index=False)
            logger.success(f'Файл {file_name} сохранен!')

    async def prices(self) -> None:
        async with aiohttp.ClientSession() as prices_session:
            api_requests = APIRequests(session=prices_session, TOKEN_KEY='КОСТРИК')        
            result = await asyncio.gather(
                    api_requests.get_prices(),
            )
            prices = pd.DataFrame(result[0])
            
        file_name = 'Цены.xlsx'
        with pd.ExcelWriter(file_name) as writer:
            prices.to_excel(writer, sheet_name='Цены', index=False)
            logger.success(f'Файл {file_name} сохранен!')
    
async def main():
    reports = Reports()
    await asyncio.gather(
        reports.prices(),
        reports.supplies()
        )

if __name__ == '__main__':
    asyncio.run(main())