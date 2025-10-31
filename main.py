import math
import requests
import pandas as pd

seller = '53699'
page = 1
catalog_url = f'https://catalog.wb.ru/sellers/v4/catalog?ab_testing=false&ab_testing=false&appType=1&curr=rub&dest=123587633&hide_dtype=11&lang=ru&page={str(page)}&sort=popular&spp=30&supplier={seller}&uclusters=1'
quantity_products = 1

items = []
personal_discount = 6

response = requests.get(catalog_url)
print(response.json())

# while quantity_products != 0:
#     response = requests.get(catalog_url)
#     data = response.json()
#     products = data.get('products', [])
#     quantity_products = (len(products))
    
#     if quantity_products != 0:
#         for product in products:
#             price = product.get('sizes', [{}])[0].get('price', {}).get('product', 0) / 100
#             personal_price = price * (1 - personal_discount/100)

#             item = {
#                 'sku': product.get('id'),
#                 'name': product.get('name'),
#                 'price': math.floor(personal_price)
#             }

#             items.append(item)

#         page = page + 1
# df = pd.DataFrame(items)
# print(df.shape)


