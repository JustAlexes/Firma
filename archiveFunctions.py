# Функция должна получать воронку продаж по дням в csv файле, но ПРОБЛЕМА ограничения 20 запросов в сутки
def GET_DAILY_DETAIL_HISTORY_REPORT_CSV(date: str, TOKEN_KEY: str, max_attempts: int = 5, DEF_WAIT: int = 15) -> pd.DataFrame:
    """
    Функция для получения данных из Воронки продаж
    """
        
    # === Определяем параметры первого запроса ===
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
    for attempt in range(max_attempts):
        logger.info(f'Получение статистики из Воронки продаж за {date}')
        response = requests.post(url=url, headers=HEADERS, json=body)
        STATUS_CODE = response.status_code
        if STATUS_CODE == 429 or STATUS_CODE in [504]:
            if attempt == max_attempts - 1:
                logger.error(f'Ошибка запроса на формирование отчета за {date} | {STATUS_CODE} | {response.text}')
                return None
            else:
                TIME_WAIT = DEF_WAIT * (attempt + 1)
                logger.warning(f'Ошибка {STATUS_CODE}, ожидание {TIME_WAIT} сек.')
                time.sleep(TIME_WAIT)
        elif STATUS_CODE != 200:
            logger.error(f'Ошибка запроса на формирование отчета за {date} | {STATUS_CODE} | {response.text}')
            return None
        else:
            logger.info(f'Началось формирование отчета за {date}')
            time.sleep(DEF_WAIT)
            break
        
    # === Определяем параметры второго запроса ===
    url = 'https://seller-analytics-api.wildberries.ru/api/v2/nm-report/downloads'
    body = {
        'filter[downloadIds]': [new_uuid]
    }
    # === Второй запрос для проверки окончания формирования Воронки продаж ===
    for attempt in range(max_attempts):
        logger.info(f'Проверка готовности отчета за {date}')
        response = requests.get(url=url, headers=HEADERS, params=body)
        STATUS_CODE = response.status_code
        
        if response.json().get('data')[0].get('status') == 'SUCCESS':
            logger.success(f'Отчет за {date} готов!')    
            break
        elif STATUS_CODE == 429: 
            if attempt == max_attempts - 1:
                logger.error(f'Ошибка проверки готовности отчета! | {STATUS_CODE} | {response.text}')
                return None
            else:
                TIME_WAIT = DEF_WAIT * (attempt + 1)
                logger.warning(f'Ошибка {STATUS_CODE} | Ожидание формирования отчета {TIME_WAIT} сек.')
                time.sleep(TIME_WAIT) 
        else:
            logger.error(f'Ошибка проверки готовности отчета! | {STATUS_CODE} | {response.text}')
            return None
        
    
    # === Определяем параметры третьего запроса ===
    url = f'https://seller-analytics-api.wildberries.ru/api/v2/nm-report/downloads/file/{new_uuid}'
    # === Третий запрос для получения отчета Воронки продаж ===         
    for attempt in range(max_attempts):
        logger.info(f'Получение отчета за {date}')
        response = requests.get(url=url, headers=HEADERS)
        STATUS_CODE = response.status_code
        if STATUS_CODE == 200:
            logger.success(f'Отчет за {date} получен!')
            break
        elif STATUS_CODE == 429:
            if attempt == max_attempts - 1:
                logger.error(f'Ошибка получения отчета | {STATUS_CODE} | {response.text}')
                return None
            else:
                TIME_WAIT = DEF_WAIT * (attempt + 1)
                logger.warning(f'Ошибка получения отчета {STATUS_CODE} | Ожидание {TIME_WAIT} сек.')
                time.sleep(TIME_WAIT)
        else:
            logger.error(f'Ошибка получения отчета {STATUS_CODE} | {response.text}')
            return None
    # === Запрос отдает ZIP файл в котором лежит csv с названием в виде (new_uuid.csv) в побитовом формате ===
    with zipfile.ZipFile(io.BytesIO(response.content), 'r') as zip_file:
        df_day_stats = pd.read_csv(io.StringIO(zip_file.read(f'{new_uuid}.csv').decode('utf-8')), index_col=None)
        if not df_day_stats.empty:
            logger.info(f'Показатели за {date} выгружены')        
            return df_day_stats
        else:
            return None

# Функция обрабатывает получаемые данные из метода GET_DAILY_DETAIL_HISTORY_REPORT_CSV   
def CALCULATE_DAILY_DETAIL_HISTORY_REPORT(df: pd.DataFrame):
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
     


