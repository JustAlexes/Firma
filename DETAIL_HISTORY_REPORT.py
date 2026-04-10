import os
import time
from dotenv import load_dotenv
import requests
from datetime import datetime
import uuid
import io
import zipfile
import pandas as pd
from dateutil.relativedelta import relativedelta
from pathlib import Path
from openpyxl import load_workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from loguru import logger
from main import APIRequests

### ------------------------------------------------- ### 
def GET_DAILY_DETAIL_HISTORY_REPORT_CSV(date: str, TOKEN_KEY: str, max_attempts: int = 5) -> pd.DataFrame:
    """
    Функция для получения данных из Воронки продаж
    """
    logger.info(f'Получение статистики из Воронки продаж за {date}')
    
    # === Определяем параметры первого запроса для формирования Воронки продаж ===
    HEADERS = {'Authorization': TOKEN_KEY}
    url = 'https://seller-analytics-api.wildberries.ru/api/v2/nm-report/downloads'
    report_date =  str(datetime.strptime(date, "%d.%m.%Y").strftime("%Y-%m-%d"))
    new_uuid = str(uuid.uuid4()) # Храним уникальный id отчета
    reportType = 'DETAIL_HISTORY_REPORT'
    params = {
        'startDate': report_date,
        'endDate': report_date,
        'skipDeletedNm': False
    }
    body = {
        'id': new_uuid,
        'reportType': reportType,
        'params': params
    }
    
    # === Первый запрос для формирования Воронки продаж ===
    response = requests.post(url=url, headers=HEADERS, json=body)
    if response.status_code != 200:
        logger.error(f'Ошибка запроса на формирование отчета за {date} | {response.status_code} | {response.text}')
        return None
    logger.info(f'Формирование отчета за {date}')
    
    # === Второй запрос для проверки окончания формирования Воронки продаж ===
    url = 'https://seller-analytics-api.wildberries.ru/api/v2/nm-report/downloads'
    body = {
        'filter[downloadIds]': [new_uuid]
    }
    
    # === Т.к отчету нужно время чтобы сформироваться, делаем ожидание ===
    for attempt in range(max_attempts):
        response = requests.get(url=url, headers=HEADERS, params=body)
        if response.json().get('data')[0].get('status') != 'SUCCESS':
            if attempt == max_attempts - 1:
                return None
            logger.info('Ожидание формирования отчета...')
            time.sleep(5 * (attempt+1))
            
        else:
            logger.success(f'Отчет за {date} готов!')    
            break
        
    # === Третий запрос для получения отчета Воронки продаж ===
    logger.info(f'Получение отчета за {date}')         
    url = f'https://seller-analytics-api.wildberries.ru/api/v2/nm-report/downloads/file/{new_uuid}'
    response = requests.get(url=url, headers=HEADERS)
    
    if response.status_code != 200:
        logger.error(f'Ошибка получения отчета {response.status_code} | {response.text}')
        return None
    logger.success(f'Отчет за {date} получен!')
    
    # === Запрос отдает ZIP файл в котором лежит csv с названием в виде (new_uuid.csv) в побитовом формате ===
    with zipfile.ZipFile(io.BytesIO(response.content), 'r') as zip_file:
        df_day_stats = pd.read_csv(io.StringIO(zip_file.read(f'{new_uuid}.csv').decode('utf-8')), index_col=None)
        logger.info(f'Показатели за {date} выгружены')        
        return df_day_stats
   
### ------------------------------------------------- ###  
def CALCULATE_DAILY_DETAIL_HISTORY_REPORT_CSV(df: pd.DataFrame):
    """
    Функция расчета данных по дням из Воронки продаж
    """
    # === Рассчитываем все необходимые показатели ===
    updateDate = (datetime.now() - relativedelta(hours=3)).strftime('%d.%m.%Y %H:%M')
    reportDate = datetime.strptime(df['dt'].iloc[0], '%Y-%m-%d').strftime('%d.%m.%Y')
    ordersCount = df['ordersCount'].sum() - df['cancelCount'].sum()   
    ordersSum = df['ordersSumRub'].sum() - df['cancelSumRub'].sum()  
    buyoutsCount = df['buyoutsCount'].sum()
    buyoutsSum = df['buyoutsSumRub'].sum()
    showsCount = 0 # Placeholder (Нельзя получить по API)
    openCard = df['openCardCount'].sum()
    addToCart = df['addToCartCount'].sum()
    showToClickConversion = 0 # Placeholder (Нельзя посчитать без показов)
    addToCartConversion = (df.loc[df['addToCartConversion'] > 0, 'addToCartConversion'].mean()) / 100
    cartToOrderConversion = (df.loc[df['cartToOrderConversion'] > 0, 'cartToOrderConversion'].mean()) / 100
    buyoutPercent = (df.loc[df['buyoutPercent'] > 0, 'buyoutPercent'].mean()) / 100
    addToWishlist = df['addToWishlist'].sum()
    
    # === Собираем показатели в необходимые поля ===
    daily_stats = {
        'updateDate': updateDate,
        'reportDate': reportDate,
        'ordersCount': ordersCount,
        'ordersSum': ordersSum,
        'buyoutsCount': buyoutsCount,
        'buyoutsSum': buyoutsSum,
        'showsCount': showsCount,
        'openCard': openCard,
        'addToCart': addToCart,
        'showToClickConversion': showToClickConversion,
        'addToCartConversion': addToCartConversion,
        'cartToOrderConversion': cartToOrderConversion,
        'buyoutPercent': buyoutPercent,
        'addToWishlist': addToWishlist
    }
    return daily_stats
 
### ------------------------------------------------- ###            
def FORMAT_DAILY_DETAIL_HISTORY_REPORT_CSV(file: str) -> bool | None:
    """
    Функция для форматирования отчета Воронки продаж
    """
    
    # Проверяем существование файла
    file_path = Path(file)
    if not file_path.exists():
        logger.error(f'Файл {file} не найден!')
        return None
    logger.info(f'Форматирование файла {file}')
    
    try:
        # === Открываем файл ===
        df = pd.read_excel(file_path)
        
        # === Считаем размер фрейма ===
        last_row = len(df) + 1
        logger.info(f'Всего записей в файле: {last_row-1}')
        
        # === Переименовываем данные для удобства ===
        header_cols = {
        'Обновлено': 'updateDate',
        'Дата': 'reportDate',
        'Заказано, шт.': 'ordersCount',
        'Заказано, руб.': 'ordersSum',
        'Выкуплено, шт.': 'buyoutsCount',
        'Выкуплено, руб.': 'buyoutsSum',
        'Показов': 'showsCount',
        'Переходов в карточки': 'openCard',
        'Добавлений в корзину': 'addToCart',
        'Средняя конверсия в клик': 'showToClickConversion',
        'Средняя конверсия в корзину': 'addToCartConversion',
        'Средняя конверсия в заказ': 'cartToOrderConversion',
        'Средний процент выкупа': 'buyoutPercent',
        'Добавлений в Отложенные': 'addToWishlist'
        }
        df = df.rename(columns=header_cols)
        
        # === Сортируем по дате ===
        df['reportDate'] = pd.to_datetime(df['reportDate'], format='%d.%m.%Y', errors='coerce')
        df = df.sort_values('reportDate')
        df['reportDate'] = df['reportDate'].dt.strftime('%d.%m.%Y')
        logger.info(f'Данные отсортированы по дате')
        
        # === Преобразование данных к числам ===
        numeric_cols = {
            'ordersCount': int,
            'ordersSum': int,
            'buyoutsCount': int,
            'buyoutsSum': int,
            'showsCount': int,
            'openCard': int,
            'addToCart': int,
            'showToClickConversion': float,
            'addToCartConversion': float,
            'cartToOrderConversion': float,
            'buyoutPercent': float,
            'addToWishlist': int,
        }
        
        for col, dtype in numeric_cols.items():
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
                if dtype == int:
                    df[col] = df[col].astype(int)
        logger.info(f'Типы данных преобразованы')
        
        # === Переименовываем столбцы ===
        header_cols = {
            'updateDate': 'Обновлено',
            'reportDate': 'Дата',
            'ordersCount': 'Заказано, шт.',
            'ordersSum': 'Заказано, руб.',
            'buyoutsCount': 'Выкуплено, шт.',
            'buyoutsSum': 'Выкуплено, руб.',
            'showsCount': 'Показов',
            'openCard': 'Переходов в карточки',
            'addToCart': 'Добавлений в корзину',
            'showToClickConversion': 'Средняя конверсия в клик',
            'addToCartConversion': 'Средняя конверсия в корзину',
            'cartToOrderConversion': 'Средняя конверсия в заказ',
            'buyoutPercent': 'Средний процент выкупа',
            'addToWishlist': 'Добавлений в Отложенные'
        }
        df = df.rename(columns=header_cols)
        logger.info(f'Столбцы переименованы')

        # === Обработка файла в xlsxwriter ===
        writer = pd.ExcelWriter(file_path, engine='xlsxwriter')
        df.to_excel(writer, index=False, sheet_name='Статистика')
        
        workbook = writer.book
        worksheet = writer.sheets['Статистика']
        
        # === Создание форматов для условного форматирования (xlsxwriter делает это надёжно) ===
        greenFormat = workbook.add_format({'bg_color': "#D1F5D8"})
        redFormat = workbook.add_format({'bg_color': "#FACCD1"})
        
        # === Применяем условное форматирование ===
        for col_letter in ['C', 'D', 'G', 'I', 'J', 'K', 'L']:
            worksheet.conditional_format(
                f'{col_letter}3:{col_letter}{last_row}',
                {'type': 'formula', 'criteria': f'={col_letter}3>{col_letter}2', 'format': greenFormat}
            )
            worksheet.conditional_format(
                f'{col_letter}3:{col_letter}{last_row}',
                {'type': 'formula', 'criteria': f'={col_letter}3<{col_letter}2', 'format': redFormat}
            )
        logger.info(f'Применено условное фомратирование')
        
        # === Автоширина столбцов ===
        for i, col in enumerate(df.columns):
            max_len = max(df[col].astype(str).map(len).max(), len(str(col))) + 2
            worksheet.set_column(i, i, min(max_len, 32))
        logger.info(f'Изменена ширина столбцов')
        
        # === ВАЖНО: Закрываем xlsxwriter ПОЛНОСТЬЮ перед openpyxl ===
        writer.close()
        
        # === Применяем числовые форматы с помощью openpyxl ===
        wb = load_workbook(file_path)
        ws = wb.active
        
        # === Подставим формулу рассчета CTR ===
        for row in range(2, last_row + 1):
            ws[f'J{row}'] = f'=IFERROR(H{row}/G{row},0)'
        logger.info(f'Подставлены формулы')
        
        # === Форматы чисел ===
        rub_format = '#,##0 "₽"'
        count_format = '#,##0'
        percent_format = '0.00%'
        
        # === Форматы по столбцам ===
        column_formats = {
            'A': None,         # Обновлено
            'B': None,         # Дата
            'C': count_format, # Заказано, шт.
            'D': rub_format,   # Заказано, руб.
            'E': count_format, # Выкуплено, шт.
            'F': rub_format,   # Выкуплено, руб.
            'G': count_format, # Показов
            'H': count_format, # Переходов
            'I': count_format, # Добавлений в корзину
            'J': percent_format, # Конверсия в клик
            'K': percent_format, # Конверсия в корзину
            'L': percent_format, # Конверсия в заказ
            'M': percent_format, # Процент выкупа
            'N': count_format, # В отложенные
        }
        
        # === Применяем форматы к ячейкам данных (строки со 2 до last_row) ===
        for col_letter, fmt in column_formats.items():
            if fmt:
                for row in range(2, last_row + 1):
                    ws[f'{col_letter}{row}'].number_format = fmt
        logger.info(f'Форматы чисел изменены')
        
        # === Границы для всех ячеек ===
        thin_border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )
        
        for row in ws.iter_rows(min_row=1, max_row=last_row, min_col=1, max_col=ws.max_column):
            for cell in row:
                cell.border = thin_border
        logger.info(f'Границы преобразованы')
        
        # === Форматы заголовка ===
        header_font = Font(bold=True, color='000000')
        header_fill = PatternFill(start_color='CCECFF', fill_type='solid')
        center_align = Alignment(horizontal='center', vertical='center')
        
        for cell in ws[1]:
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = center_align
        logger.info(f'Заголовки преобразованы')
        
        # === Сохраняем и закрываем файл ===
        wb.save(file_path)
        wb.close()
        logger.success(f'Файл {file} успешно форматирован и сохранен!')
        return True
    except Exception as e:
        logger.error(f'Произошла ошибка на одном из этапов форматирования файла {file}! | {e}')              
                
### ------------------------------------------------- ###            
def UPDATE_DAILY_DETAIL_HISTORY_REPORT_CSV(dates: list[str], TOKEN_NAME: str, file_name: str):
    """
    Функция для ежедневного обновления отчета Воронки продаж
    """
    # === Инициализируем токен ===
    try:
        load_dotenv()
        TOKEN_KEY = os.getenv(TOKEN_NAME)
        if TOKEN_KEY == None:
            logger.error('Ошибка инициализации токена!')
            return None
        logger.info('Токен инициализирован!')
        
        for date in dates:
            new_daily_stats = GET_DAILY_DETAIL_HISTORY_REPORT_CSV(date, TOKEN_KEY)
            new_daily_stats = CALCULATE_DAILY_DETAIL_HISTORY_REPORT_CSV(df=new_daily_stats)
                    
            # === Получение сохраненных данных ===
            df_existing = pd.read_excel(file_name)
            
            # === Переименовываем данные для удобства ===
            header_cols = {
            'Обновлено': 'updateDate',
            'Дата': 'reportDate',
            'Заказано, шт.': 'ordersCount',
            'Заказано, руб.': 'ordersSum',
            'Выкуплено, шт.': 'buyoutsCount',
            'Выкуплено, руб.': 'buyoutsSum',
            'Показов': 'showsCount',
            'Переходов в карточки': 'openCard',
            'Добавлений в корзину': 'addToCart',
            'Средняя конверсия в клик': 'showToClickConversion',
            'Средняя конверсия в корзину': 'addToCartConversion',
            'Средняя конверсия в заказ': 'cartToOrderConversion',
            'Средний процент выкупа': 'buyoutPercent',
            'Добавлений в Отложенные': 'addToWishlist'
            }
            df_existing = df_existing.rename(columns=header_cols)
            
            # === Вставка новых данных ===
            if new_daily_stats['reportDate'] not in df_existing['reportDate'].values:
                df_new_day_stats = pd.DataFrame([new_daily_stats], index=None)
                df_combined = pd.concat([df_existing, df_new_day_stats], ignore_index=True)
                df_combined.to_excel(file_name, index=False, sheet_name='Статистика')
                logger.success(f"Данные за {date} добавлены в файл {file_name}")
            
            # === Замена устаревших данных ===
            elif new_daily_stats['reportDate'] in df_existing['reportDate'].values:
                # === Выбираем фрейм с датой обрабатываемой на данный момент ===
                df_updatableDate = df_existing[df_existing['reportDate'] == date]
                # === Заменяем данные, если хотя бы какой-то из показателей увеличился ===
                if (new_daily_stats['ordersCount'] != df_updatableDate['ordersCount'].iloc[0] or 
                    new_daily_stats['ordersSum'] != df_updatableDate['ordersSum'].iloc[0] or
                    new_daily_stats['buyoutsCount'] != df_updatableDate['buyoutsCount'].iloc[0] or
                    new_daily_stats['buyoutsSum'] != df_updatableDate['buyoutsSum'].iloc[0] or
                    new_daily_stats['openCard'] != df_updatableDate['openCard'].iloc[0] or
                    new_daily_stats['addToCart'] != df_updatableDate['addToCart'].iloc[0] or
                    new_daily_stats['addToWishlist'] != df_updatableDate['addToWishlist'].iloc[0]):
                        
                    # === Т.к Показы увеличиться не могут и по API не тянутся, обновлять их не будем ===
                    showsCount = df_updatableDate['showsCount'].iloc[0]
                    showToClickConversion = df_updatableDate['showToClickConversion'].iloc[0]
                    if showsCount > 0 or showToClickConversion > 0:
                        new_daily_stats['showsCount'] = showsCount 
                        new_daily_stats['showToClickConversion'] = showToClickConversion
                        
                    df_new_day_stats = pd.DataFrame([new_daily_stats], index=None)
                    df_existing = df_existing[df_existing['reportDate'] != date]
                    df_combined = pd.concat([df_existing, df_new_day_stats], ignore_index=True)
                    df_combined.to_excel(file_name, index=False, sheet_name='Статистика')
                         
                    logger.success(f"Данные за {date} в файле {file_name} успешно обновлены")
                else:
                    logger.success(f"Данные за {date} в файле {file_name} уже актуальны")
            else:
                logger.critical(f'Неопознанная ошибка!!!')
                
            if date != dates[-1]:
                logger.info(f'Ожидание 30 секунд для предотвращения ошибки 429...')
                time.sleep(30)
        
        if(FORMAT_DAILY_DETAIL_HISTORY_REPORT_CSV(file=file_name)):
            logger.success(f'Форматированние данных при обновлении периода {dates[0]} - {dates[-1]} прошло успешно')
        logger.success(f'Данные за период {dates[0]} - {dates[-1]} успешно обновлены')
    
    except Exception as e:
        logger.error(f'Возникла ошибка на одном из этапов обновления данных | {e}')    

### ------------------------------------------------- ###            
def GET_DAILY_DETAIL_HISTORY_REPORT(TOKEN_NAME: str, date: str, max_attempts: int = 5) -> pd.DataFrame:
    """
    Функция получения данных из Воронки продаж
    """
    logger.info(f'Получение статистики из Воронки продаж за {date}')
    load_dotenv()
    TOKEN_KEY = os.getenv(TOKEN_NAME)
    HEADERS = {'Authorization': TOKEN_KEY}
    url = 'https://seller-analytics-api.wildberries.ru/api/analytics/v3/sales-funnel/products'
    dateStartEnd =  str(datetime.strptime(date, "%d.%m.%Y").strftime("%Y-%m-%d"))
    params = {
        'selectedPeriod': {
            'start': dateStartEnd,
            'end': dateStartEnd
        },
        'skipDeletedNm': False,
        'orderBy': {
            'field': 'openCard',
            'mode': 'desc'
        },
        'limit': 1000
    }
    for attempt in range(max_attempts):
        response = requests.post(url=url, headers=HEADERS, json=params)
        STATUS_CODE = response.status_code
        if STATUS_CODE == 429:
            if attempt == max_attempts - 1:
                logger.error(f'{STATUS_CODE} | Превышен лимит запросов. Повторите попытку позже.')
                return None
            logger.info(f'{STATUS_CODE} | {response.text} | Ожидание {5*(attempt+1)}сек.')
            time.sleep(5 * (attempt+1))
        elif response.status_code in [400, 401, 402, 403]:
            logger.error(f'{response.status_code} | {response.text}')
            return None
        else:
            logger.debug(f'Данные из Воронки продаж за {date} получены')
            break   
    products = response.json().get('data').get('products')

    detail_history = []
    for product in products:
        detail_history_product = {}
        detail_history_product['nmId'] = product.get('product').get('nmId')
        detail_history_product['title'] = product.get('product').get('title')
        detail_history_product['vendorCode'] = product.get('product').get('vendorCode')
        detail_history_product['openCount'] = product.get('statistic').get('selected').get('openCount')
        detail_history_product['cartCount'] = product.get('statistic').get('selected').get('cartCount')
        detail_history_product['orderCount - cancelCount'] = product.get('statistic').get('selected').get('orderCount') - product.get('statistic').get('selected').get('cancelCount')
        detail_history_product['orderSum - cancelSum'] = product.get('statistic').get('selected').get('orderSum') - product.get('statistic').get('selected').get('cancelSum')
        detail_history_product['buyoutCount'] = product.get('statistic').get('selected').get('buyoutCount')
        detail_history_product['buyoutSum'] = product.get('statistic').get('selected').get('buyoutSum')
        detail_history.append(detail_history_product)
        
    if not detail_history:
        logger.error(f'Возникла ошибка при обработке данных за {date}')
        return None
    logger.success(f'Данные из Воронки продаж за {date} обработаны!')
    return detail_history
       
# pd.DataFrame(GET_DAILY_DETAIL_HISTORY_REPORT(TOKEN_NAME='КОСТРИК', date='01.04.2026'), index=None).to_excel('Воронка.xlsx', index=False)

### ------------------------------------------------- ### 
def GET_REALIZATION_DETAIL_REPORT(TOKEN_NAME: str, date: str, max_attempts: int = 5) -> list:    
    """
    Функция для получения отчета о реализации \n
    date в формате dd.mm.yyyy
    """
    logger.success(f'Получение отчета о реализации за {date}')
    
    load_dotenv()
    TOKEN_KEY = os.getenv(TOKEN_NAME)
    HEADERS = {'Authorization': TOKEN_KEY}
    
    url = 'https://statistics-api.wildberries.ru/api/v5/supplier/reportDetailByPeriod'
    
    dateFromTo = str(datetime.strptime(date, "%d.%m.%Y").strftime("%Y-%m-%d"))
    params = {
        'dateFrom': dateFromTo,
        'dateTo': dateFromTo,
        'period': 'daily'
    }
    
    for attempt in range(max_attempts):
        response = requests.get(url=url, headers=HEADERS, params=params)
        STATUS_CODE = response.status_code
        if STATUS_CODE == 429:
            WAIT_TIME = 5 * (attempt + 1)
            if attempt == (max_attempts - 1):
                logger.error(f'{STATUS_CODE} | Превышен лимит запросов. Повторите попытку позже.')
                return None
            logger.warning(f'Ошибка {STATUS_CODE}, ожидание {WAIT_TIME} секунд.')
            time.sleep(WAIT_TIME)
        elif STATUS_CODE == 204:
            logger.warning('Нет данных!')
            return None
        elif STATUS_CODE != 200:
            logger.error(f'Ошибка {STATUS_CODE} | {response.text}')
            return None
        else:
            data = response.json()
            logger.success('Все данные получены!')
            break
    
    if not data:
        logger.warning(f'Отчет за {date} пуст !!!')
        return None
    data = response.json()
    logger.success(f'Отчет за {date} получен!')
    
    realization_detail_report = []
    for el in data:
        realization_detail_el = {}
        realization_detail_el['subject_name'] = el.get('subject_name')
        realization_detail_el['nm_id'] = el.get('nm_id')
        realization_detail_el['barcode'] = el.get('barcode')
        realization_detail_el['doc_type_name'] = el.get('doc_type_name')
        realization_detail_el['quantity'] = el.get('quantity')
        realization_detail_el['retail_price'] = el.get('retail_price')
        realization_detail_el['retail_amount'] = el.get('retail_amount')
        realization_detail_el['sale_percent'] = el.get('sale_percent')
        realization_detail_el['commission_percent'] = el.get('commission_percent')
        realization_detail_el['supplier_oper_name'] = el.get('supplier_oper_name')
        realization_detail_el['retail_price_withdisc_rub'] = el.get('retail_price_withdisc_rub')
        realization_detail_el['delivery_amount'] = el.get('delivery_amount')
        realization_detail_el['return_amount'] = el.get('return_amount')
        realization_detail_el['delivery_rub'] = el.get('delivery_rub')
        realization_detail_el['product_discount_for_report'] = el.get('product_discount_for_report')
        realization_detail_el['supplier_promo'] = el.get('supplier_promo')
        realization_detail_el['ppvz_spp_prc'] = el.get('ppvz_spp_prc')
        realization_detail_el['ppvz_kvw_prc_base'] = el.get('ppvz_kvw_prc_base')
        realization_detail_el['ppvz_kvw_prc'] = el.get('ppvz_kvw_prc')
        realization_detail_el['sup_rating_prc_up'] = el.get('sup_rating_prc_up')
        realization_detail_el['is_kgvp_v2'] = el.get('is_kgvp_v2')
        realization_detail_el['ppvz_sales_commission'] = el.get('ppvz_sales_commission')
        realization_detail_el['ppvz_for_pay'] = el.get('ppvz_for_pay')
        realization_detail_el['ppvz_reward'] = el.get('ppvz_reward')
        realization_detail_el['acquiring_fee'] = el.get('acquiring_fee')
        realization_detail_el['acquiring_percent'] = el.get('acquiring_percent')
        realization_detail_el['payment_processing'] = el.get('payment_processing')
        realization_detail_el['ppvz_vw'] = el.get('ppvz_vw')
        realization_detail_el['bonus_type_name'] = el.get('bonus_type_name', None)
        realization_detail_el['penalty'] = el.get('penalty')
        realization_detail_el['additional_payment'] = el.get('additional_payment')
        realization_detail_el['rebill_logistic_cost'] = el.get('rebill_logistic_cost')
        realization_detail_el['storage_fee'] = el.get('storage_fee')
        realization_detail_el['deduction'] = el.get('deduction')
        realization_detail_el['acceptance'] = el.get('acceptance')
        realization_detail_el['srid'] = el.get('srid')
        realization_detail_el['installment_cofinancing_amount'] = el.get('installment_cofinancing_amount')
        realization_detail_el['cashback_amount'] = el.get('cashback_amount')
        realization_detail_el['cashback_discount'] = el.get('cashback_discount')
        realization_detail_el['cashback_commission_change'] = el.get('cashback_commission_change')
        realization_detail_el['order_uid'] = el.get('order_uid')
        realization_detail_el['payment_schedule'] = el.get('payment_schedule')
        realization_detail_el['seller_promo_discount'] = el.get('seller_promo_discount')
        realization_detail_el['loyalty_discount'] = el.get('loyalty_discount')
        realization_detail_el['sale_price_promocode_discount_prc'] = el.get('sale_price_promocode_discount_prc')
        realization_detail_el['sale_price_affiliated_discount_prc'] = el.get('sale_price_affiliated_discount_prc')
        
        realization_detail_report.append(realization_detail_el)
        
    return realization_detail_report
    
# print(GET_REALIZATION_DETAIL_REPORT(TOKEN_NAME='КОСТРИК', date='01.04.2026'))
# pd.DataFrame(GET_REALIZATION_DETAIL_REPORT(TOKEN_NAME='КОСТРИК', date='01.04.2026'), index=None).to_excel('Реализация.xlsx', index=False)

### ------------------------------------------------- ### 



# TODO
# # В days передается кол-во дней для обновления отчета (в день максимум 20 запросов, рекомендуется - не более 15 дней)        
# file_name = 'Ежедневная статистика.xlsx'
# days = 16
# # При помощи инструментов pandas собираем список дат 
# dates = pd.date_range(end=pd.Timestamp.now()-relativedelta(days=1), periods=days, freq='D').strftime('%d.%m.%Y').tolist()
# UPDATE_DAILY_DETAIL_HISTORY_REPORT_CSV(dates=dates, TOKEN_NAME='КОСТРИК', file_name=file_name)