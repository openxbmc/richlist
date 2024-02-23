import pymysql
from flask import Flask, render_template, request, redirect, url_for
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.ticker import ScalarFormatter
from matplotlib.ticker import FixedLocator
from matplotlib.dates import DateFormatter, HourLocator


from io import BytesIO
import base64

app = Flask(__name__)

@app.route('/')
def index():
    # 连接 MySQL 数据库
    with pymysql.connect(host='localhost', db='flux', port=3306, user='root', password='123456') as db:
        cursor = db.cursor()

        # 查询所有表，并按最新 balance 排序
        query_sql = "SELECT TABLE_NAME FROM information_schema.TABLES WHERE TABLE_SCHEMA='flux'"
        cursor.execute(query_sql)
        tables = cursor.fetchall()
        results = []
        for table in tables:
            query_last_balance_sql = f"SELECT balance FROM `{table[0]}` ORDER BY date DESC LIMIT 1"
            cursor.execute(query_last_balance_sql)
            last_balance = cursor.fetchone()[0]
            results.append({'name': table[0], 'balance': last_balance})

        results = sorted(results, key=lambda x: x['balance'], reverse=True)

    return render_template('index.html', results=results)


@app.route('/chart/<table>')
def chart(table):
    # 连接 MySQL 数据库
    with pymysql.connect(host='localhost', db='flux', port=3306, user='root', password='123456') as db:
        cursor = db.cursor()

        # 查询数据并绘图
        time_period = request.args.get('time_period', None)
        if time_period == 'day':
            query_data_sql = f"SELECT * FROM {table} WHERE date >= DATE_SUB(NOW(), INTERVAL 1 DAY) ORDER BY date DESC"
        elif time_period == 'week':
            query_data_sql = f"SELECT * FROM {table} WHERE date >= DATE_SUB(NOW(), INTERVAL 1 WEEK) ORDER BY date DESC"
        elif time_period == 'month':
            query_data_sql = f"SELECT * FROM {table} WHERE date >= DATE_SUB(NOW(), INTERVAL 1 MONTH) ORDER BY date DESC"
        else:
            query_data_sql = f"SELECT * FROM {table} ORDER BY date DESC"

        cursor.execute(query_data_sql)
        data = cursor.fetchall()
        data = pd.DataFrame(data, columns=['balance', 'date'])

        # 设置图像样式
        matplotlib.rcParams['font.family'] = 'sans-serif'
        matplotlib.rcParams['font.sans-serif'] = 'Arial'
        matplotlib.rcParams['font.size'] = 10
        matplotlib.rcParams['axes.linewidth'] = 0.5

        #fig, ax = plt.subplots()
        fig, ax = plt.subplots(figsize=(12, 8))
        ax.plot(data['date'], data['balance'])

        # 根据时间周期设置 x 轴标签格式和间隔
        if time_period == 'day':
            ax.xaxis.set_major_locator(matplotlib.dates.HourLocator(interval=2))
            ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter('%m-%d\n%H:%M'))
        elif time_period == 'three_day':
            ax.xaxis.set_major_locator(matplotlib.dates.HourLocator(interval=8))
            ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter('%m-%d\n%H:%M'))
        elif time_period == 'week':
            ax.xaxis.set_major_locator(matplotlib.dates.DayLocator(interval=1))
            ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter('%m-%d'))

        ax.set_title(table)
        ax.set_xlabel('Date')
        ax.set_ylabel('Balance')
        #ax.tick_params(axis='x', rotation=90)
        ax.yaxis.set_major_formatter(ScalarFormatter(useOffset=False))

        # 将 Y 列坐标格式设置为数字，禁用科学记数法
        plt.ticklabel_format(style='plain', axis='y')

        fig.tight_layout()

        # 将图形转换为 HTML 格式
        figfile = BytesIO()
        fig.savefig(figfile, format='png')
        figfile.seek(0)
        figdata_png = base64.b64encode(figfile.getvalue()).decode()

    # 将数据和图形传递给网页模板
    return render_template('chart.html', table=table, figdata=figdata_png, time_period=time_period)

if __name__ == '__main__':
    app.run(debug=True)