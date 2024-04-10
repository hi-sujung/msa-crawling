import os
import pandas as pd
import requests
from bs4 import BeautifulSoup
import pika
import datetime

# 서비스 계정 인증을 위한 환경변수 설정
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "서비스계정 key JSON 파일 경로"

def crawl_and_publish_to_rabbitmq():
    url = 'https://www.sungshin.ac.kr/ce/11806/subview.do'

    HEADERS = {'User-Agent': 'Mozilla/5.0 (iPad; CPU OS 12_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148'}
    res = requests.get(url, headers=HEADERS)

    print("response status code: ", res.status_code)

    soup = BeautifulSoup(res.text, "html.parser")

    # 데이터 추출
    notice_elements = soup.find_all('td', class_='_artclTdNum')
    notice = [n_element.text.strip() for n_element in notice_elements]
    num = 0
    for i in range(len(notice)):
        if notice[i] == "공지":
            num += 1
            print("공지: ", num)

    major_elements = soup.select('div.row-list ul li')[:1]
    major = [m_element.text.strip() for m_element in major_elements]

    title_elements = soup.select('td._artclTdTitle a strong')[num:]
    title = [t_element.text.strip() for t_element in title_elements]

    date_elements = soup.find_all('td', class_='_artclTdRdate')[num:]
    date = [d_element.text.strip() for d_element in date_elements]

    link_elements = soup.find_all('a', class_='artclLinkView')[num:]
    link = ["https://www.sungshin.ac.kr{}".format(l_element['href']) for l_element in link_elements]

    # 데이터프레임 생성
    df = pd.DataFrame({
        'Major': major * len(title),
        'Date': date,
        'Title': title,
        'Link': link
    })

    # RabbitMQ 연결 설정
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()
    channel.queue_declare(queue='univ_activity_queue')

    # 데이터를 RabbitMQ에 publish
    for index, row in df.iterrows():
        message = row.to_json()  # 행을 JSON 문자열로 변환
        channel.basic_publish(exchange='', routing_key='univ_activity_queue', body=message)
        print(" [x] Sent %r" % message)

    # RabbitMQ 연결 닫기
    connection.close()

# 스크립트 파일을 직접 실행할 때 crawl_and_publish_to_rabbitmq() 함수 호출
if __name__ == "__main__":
    crawl_and_publish_to_rabbitmq()