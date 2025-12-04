from selenium.webdriver import Remote, ChromeOptions
from selenium.webdriver.chromium.remote_connection import ChromiumRemoteConnection
from selenium.webdriver.common.by import By 
from bs4 import BeautifulSoup
import requests 
import warnings 
import time 
import random 
import csv

warnings.filterwarnings("ignore", category=requests.packages.urllib3.exceptions.InsecureRequestWarning)

# 새 프록시 정보 설정
host = "45.234.61.229"
port = 999
proxy_url = f"socks4://{host}:{port}"
proxies = {"http": proxy_url, "https": proxy_url}
print(proxy_url)

keyword = input("검색할 제품 입력 : ")

link_list = []
with open(f"coupang_{keyword}.csv", "w", newline="", encoding="utf-8") as csv_file:
    writer = csv.writer(csv_file)
    writer.writerow(["제품명", "가격", "링크"])
    for page_num in range(1, 3):
        print(f"<<<<<{page_num}페이지>>>>>")

        url = f"https://www.coupang.com/np/search?q={keyword}&page={page_num}&listSize=36"
        print(url)
        print()

        response = requests.get(url, proxies=proxies, verify=False)
        html = response.text
        soup = BeautifulSoup(html, "html.parser")
        items = soup.select("[class=search-product]")
        print(len(items))

        for item in items:
            name = item.select_one(".name").text
            price = item.select_one(".price-value")
            if not price:
                continue
            else:
                price = price.text
            link = f"https://coupang.com{item.a['href']}"

            link_list.append(link)
            writer.writerow([name, price, link])
            print(f" {name} : {price}")
            print(link)
            print()

print(link_list)
print(len(link_list))

with open(f"coupang_{keyword}_detail_page.csv", "w", newline="", encoding="utf-8") as csv_file:
    writer = csv.writer(csv_file)
    writer.writerow(["브랜드", "제품명", "판매자", "현재 판매가", "회원 판매가", "옵션", "상세정보", "url"])
    for e, url in enumerate(link_list, 1):
        print(f' {e}...Connecting to Scraping Browser...')
        sbr_connection = ChromiumRemoteConnection(proxy_url, 'goog', 'chrome')
        with Remote(sbr_connection, options=ChromeOptions()) as driver:
            print('Connected! Navigating...')
            driver.implicitly_wait(5)
            driver.get(url)
            html = driver.page_source
            soup = BeautifulSoup(html, "html.parser")

