import os
import re
import pandas as pd
import requests
from bs4 import BeautifulSoup
from google.cloud.sql.connector import Connector
import sqlalchemy
import pymysql.cursors

# 서비스계정 key JSON 파일
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "./rising-woods-388317-8a18f2625ba5.json"

url = 'https://www.campuspick.com/activity/view?id=25379'

HEADERS = {'User-Agent': 'Mozilla/5.0 (iPad; CPU OS 12_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148'}
html = requests.get(url, headers=HEADERS).text

content = re.search(r'cp\.activityview\.data = {(.*?)};', html, re.S).group(1)

# Use regular expressions to capture specific fields
title = re.search(r'title: "(.*?)"', content).group(1)
startDate = re.search(r'startDate: "(.*?)"', content).group(1)
endDate = re.search(r'endDate: "(.*?)"', content).group(1)
website = re.search(r'website: "(.*?)"', content).group(1)
company = re.search(r'company: "(.*?)"', content).group(1)
description = re.search(r'description: "(.*?)"', content).group(1)

# DB 연결
connector = Connector()
def getconn() -> pymysql.connections.Connection:
    conn: pymysql.connections.Connection = connector.connect(
        "rising-woods-388317:asia-northeast3:notice-mysql",
        "pymysql",
        user="root",
        password="hisujung",
        db="noticeDB"
    )
    return conn

pool = sqlalchemy.create_engine(
    "mysql+pymysql://",
    creator=getconn,
)

conn = pool.raw_connection()
cursor = conn.cursor()

cursor.execute("INSERT INTO external_act (title, start_date, deadline, link, content) VALUES (%s, %s, %s, %s, %s)", (title, startDate, endDate, website, description))
result = cursor.fetchall()

# 커밋하기
conn.commit()
# 연결 종료
conn.close()

print("Done!")
