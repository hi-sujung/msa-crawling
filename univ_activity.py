import os
import pandas as pd
import requests
from bs4 import BeautifulSoup
from google.cloud.sql.connector import Connector
import sqlalchemy
import pymysql.cursors
import datetime

# 서비스 계정 인증을 위한 환경변수 설정
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "서비스계정 key JSON 파일 경로"

url = 'https://www.sungshin.ac.kr/ce/11806/subview.do'

HEADERS = {'User-Agent': 'Mozilla/5.0 (iPad; CPU OS 12_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148'}
res = requests.get(url, headers=HEADERS)

print("response status code: ", res.status_code)

soup = BeautifulSoup(res.text, "html.parser")

# 공지
notice_elements = soup.find_all('td', class_='_artclTdNum')
notice = [n_element.text.strip() for n_element in notice_elements]
num = 0
for i in range(len(notice)):
    if notice[i] == "공지":
        num += 1
        print("공지: ", num)

# 학과명
major_elements = soup.select('div.row-list ul li')[:1]
major = [m_element.text.strip() for m_element in major_elements]
# major = ['운동재활복지학과']
# major = ['기악과']

# 공지명
title_elements = soup.select('td._artclTdTitle a strong')[num:]
title = [t_element.text.strip() for t_element in title_elements]

# 날짜
date_elements = soup.find_all('td', class_='_artclTdRdate')[num:]
date = [d_element.text.strip() for d_element in date_elements]

# 링크
link_elements = soup.find_all('a', class_='artclLinkView')[num:]
link = ["https://www.sungshin.ac.kr{}".format(l_element['href']) for l_element in link_elements]

connector = Connector()
def getconn() -> pymysql.connections.Connection:
    conn: pymysql.connections.Connection = connector.connect(
        "sql인스턴스연결이름",
        "pymysql",
        user="user",
        password="password",
        db="dbName"
    )
    return conn

pool = sqlalchemy.create_engine(
    "mysql+pymysql://",
    creator=getconn,
)

# Create DataFrame
df = pd.DataFrame({
    'Major': major * len(title),
    'Date': date,
    'Title': title,
    'Link': link
})

# Establish connection
conn = pool.raw_connection()
cursor = conn.cursor()

# Insert data into the database
for index, row in df.iterrows():
    postDepartment = row['Major']
    startDate = row['Date']
    title = row['Title']
    link = row['Link']
    cursor.execute("INSERT INTO univ_activity(post_department, start_date, title, link) VALUES (%s, %s, %s, %s)", (postDepartment, startDate, title, link))

# Fetch all data from the table
cursor.execute('SELECT univ_activity_id, post_department, start_date, title, link FROM univ_activity')
result = cursor.fetchall()

print('현재 테이블 데이터 수: {}'.format(len(result)))
print('========================')

# Set the date for deletion (6 months ago)
current_date = datetime.datetime.now()
month_ago = current_date - datetime.timedelta(days=180)
print(month_ago)

# Delete records older than 6 months
cursor.execute('DELETE FROM univ_activity WHERE start_date < %s', (month_ago,))

print("Done!")

# Fetch all data from the table after deletion
cursor.execute('SELECT univ_activity_id, post_department, start_date, title, link FROM univ_activity')
result = cursor.fetchall()

print('현재 테이블 데이터 수: {}'.format(len(result)))

# Commit changes
conn.commit()

# Close the connection
conn.close()
