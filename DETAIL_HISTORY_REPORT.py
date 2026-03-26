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

### ------------------------------------------------- ### 
def GET_DETAIL_HISTORY_REPORT(date: str, TOKEN_KEY: str, file: str, max_attempts: int = 5) -> object:
    """
    Функция для формирования отчета Воронки продаж
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
        logger.error(f'Ошибка запроса на формирование отчета за {date} | {response.status_code}')
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
        file_content = pd.read_csv(io.StringIO(zip_file.read(f'{new_uuid}.csv').decode('utf-8')), index_col=None)
        logger.info(f'Рассчет показателей за {date}')
        
        # === Рассчитываем все необходимые показатели ===
        updateDate = (datetime.now() - relativedelta(hours=3)).strftime('%d.%m.%Y %H:%M')
        reportDate = datetime.strptime(file_content['dt'].iloc[0], '%Y-%m-%d').strftime('%d.%m.%Y')
        ordersCount = file_content['ordersCount'].sum() - file_content['cancelCount'].sum()   
        ordersSum = file_content['ordersSumRub'].sum() - file_content['cancelSumRub'].sum()  
        buyoutsCount = file_content['buyoutsCount'].sum()
        buyoutsSum = file_content['buyoutsSumRub'].sum()
        showsCount = 0 # Placeholder (Нельзя получить по API)
        openCard = file_content['openCardCount'].sum()
        addToCart = file_content['addToCartCount'].sum()
        showToClickConversion = 0 # Placeholder (Нельзя посчитать без показов)
        addToCartConversion = (file_content.loc[file_content['addToCartConversion'] > 0, 'addToCartConversion'].mean()) / 100
        cartToOrderConversion = (file_content.loc[file_content['cartToOrderConversion'] > 0, 'cartToOrderConversion'].mean()) / 100
        buyoutPercent = (file_content.loc[file_content['buyoutPercent'] > 0, 'buyoutPercent'].mean()) / 100
        addToWishlist = file_content['addToWishlist'].sum()
        
        # === Собираем показатели в необходимые поля ===
        day_stats = {
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
        
        return day_stats
    
    
### ------------------------------------------------- ###            
def FORMAT_DETAIL_HISTORY_REPORT(file: str) -> bool | None:
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
        for col_letter in ['C', 'G', 'I', 'J', 'K', 'L']:
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
    except:
        logger.error(f'Произошла ошибка на одном из этапов форматирования файла {file}!')
                    
                
### ------------------------------------------------- ###            
def UPDATE_DETAIL_HISTORY_REPORT(dates: list[str], TOKEN_NAME: str, file_name: str):
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
            new_day_stats = GET_DETAIL_HISTORY_REPORT(date, TOKEN_KEY, file=file_name)
                    
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
            if new_day_stats['reportDate'] not in df_existing['reportDate'].values:
                df_new_day_stats = pd.DataFrame([new_day_stats], index=None)
                df_combined = pd.concat([df_existing, df_new_day_stats], ignore_index=True)
                df_combined.to_excel(file_name, index=False, sheet_name='Статистика')
                logger.success(f"Данные за {date} добавлены в файл {file_name}")
            
            # === Замена устаревших данных ===
            elif new_day_stats['reportDate'] in df_existing['reportDate'].values:
                # === Выбираем фрейм с датой обрабатываемой на данный момент ===
                df_updatableDate = df_existing[df_existing['reportDate'] == date]
                # === Заменяем данные, если хотя бы какой-то из показателей увеличился ===
                if (new_day_stats['ordersCount'] > df_updatableDate['ordersCount'].iloc[0] or 
                    new_day_stats['ordersSum'] > df_updatableDate['ordersSum'].iloc[0] or
                    new_day_stats['buyoutsCount'] > df_updatableDate['buyoutsCount'].iloc[0] or
                    new_day_stats['buyoutsSum'] > df_updatableDate['buyoutsSum'].iloc[0] or
                    new_day_stats['openCard'] > df_updatableDate['openCard'].iloc[0] or
                    new_day_stats['addToCart'] > df_updatableDate['addToCart'].iloc[0] or
                    new_day_stats['addToWishlist'] > df_updatableDate['addToWishlist'].iloc[0]):
                        
                    # === Т.к Показы увеличиться не могут и по API не тянутся, обновлять их не будем ===
                    showsCount = df_updatableDate['showsCount'].iloc[0]
                    showToClickConversion = df_updatableDate['showToClickConversion'].iloc[0]
                    if showsCount > 0 or showToClickConversion > 0:
                        new_day_stats['showsCount'] = showsCount 
                        new_day_stats['showToClickConversion'] = showToClickConversion
                        
                    df_new_day_stats = pd.DataFrame([new_day_stats], index=None)
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
        
        if(FORMAT_DETAIL_HISTORY_REPORT(file=file_name)):
            logger.success(f'Форматированние данных при обновлении периода {dates[0]} - {dates[-1]} прошло успешно')
        logger.success(f'Данные за период {dates[0]} - {dates[-1]} успешно обновлены')
    
    except Exception as e:
        logger.error(f'Возникла ошибка на одном из этапов обновления данных | {e}')    

# В days передается кол-во дней для обновления отчета (в день максимум 20 запросов, рекомендуется - не более 15 дней)        
file_name = 'Ежедневная статистика.xlsx'
days = 15
# При помощи инструментов pandas собираем список дат 
dates = pd.date_range(end=pd.Timestamp.now()-relativedelta(days=1), periods=days, freq='D').strftime('%d.%m.%Y').tolist()

# for date in dates:
#     print(date)
UPDATE_DETAIL_HISTORY_REPORT(dates=dates, TOKEN_NAME='КОСТРИК', file_name=file_name)


 