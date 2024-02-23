import requests
import json
import pymysql
import time

# 创建数据库连接
conn = pymysql.connect(host='localhost', port=3306, user='root', password='123456')

# 创建数据库
with conn.cursor() as cursor:
    cursor.execute('CREATE DATABASE IF NOT EXISTS flux')
    cursor.execute('USE flux')

# 循环爬取并存储数据
while True:
    try:
        # 发送请求获取数据
        response = requests.get('https://explorer.runonflux.io/api/statistics/richest-addresses-list')
        data = json.loads(response.text)

        # 解析数据并存储到数据库
        with conn.cursor() as cursor:
            cursor.execute('USE flux')
            for i, d in enumerate(data):
                address = d['address']
                balance = d['balance']
                cursor.execute(f'CREATE TABLE IF NOT EXISTS {address} (balance FLOAT, date TIMESTAMP)')
                cursor.execute(f'INSERT INTO {address} (balance, date) VALUES ({balance}, NOW())')
            conn.commit()

        print(f'{time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())}: 数据已成功爬取并存储到数据库。')

    except Exception as e:
        print(f'{time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())}: 程序发生异常：{e}')

    # 每小时执行一次
    time.sleep(6 * 3600)
