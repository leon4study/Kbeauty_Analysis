from selenium import webdriver
from selenium.webdriver.common.by import By
import pyperclip
import time
import pandas as pd
import re
import os
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import random
import slack1


path = "/Users/jun/GitStudy/Data_4/Data/project5/address"
os.chdir(path)

result_df = pd.DataFrame()


def delete_prev_csv(filename):
    # 기존 파일이 존재하면 삭제
    if os.path.exists(filename):
        os.remove(filename)
    else:
        print("No such file")


def addr_to_df(address):
    # 주소를 줄 바꿈 기준으로 나누기
    addresses = address.strip().split('\n')

    # 주소를 나누는 패턴 (정규 표현식)
    pattern = r"(?P<detailed_address>.+?)\s(?P<city>[A-Za-z\s]+)\s(?P<state>[A-Z]{2})\s(?P<zipcode>\d{5}-\d{4}|\d{5})\sUSA"

    # 각 주소에서 정보 추출하기
    address_data = []
    for address in addresses:
        match = re.match(pattern, address)
        if match:
            address_data.append(match.groupdict())
    df = pd.DataFrame(address_data)
    return df


def click_regen_b():
    regen_b = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.XPATH, '''//*[@id="res_li"]/li[4]/button'''))
    )
    driver.execute_script("arguments[0].click();", regen_b)
    time.sleep(0.5)
    


def click_copy_b():
    copy_b = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.XPATH, '''//*[@id="random_anchor_page"]/div[2]/p/a'''))
    )
    driver.execute_script("arguments[0].click();", copy_b)
    time.sleep(0.5)

states_population = [['AK', 39],['AL', 192],['AR', 154],['AZ', 282],['CO', 218],
['CT', 141],['DC', 26],['DE', 39],['FL', 832],['GA', 410],['HI', 52],
['IA', 128],['ID', 77],['IL', 500],['IN', 269],['KS', 128],['KY', 205],
['LA', 167],['MA', 256],['MD', 244],['ME', 52],['MI', 461],['MN', 231],
['MO', 282],['MS', 141],['MT', 39],['NC', 410],['ND', 26],['NE', 116],
['NH', 52],['NJ', 359],['NM', 116],['NV', 128],['NY', 781],['OH', 448],
['OK', 167],['OR', 167],['PA', 525],['RI', 39],['SC', 256],['SD', 39],
['TN', 282],['TX', 1114],['UT', 128],['VA', 320],['VT', 13],['WA', 295],
['WI', 295],['WV', 77],['WY', 13]]

# 셀레니움 웹 드라이버 설정 (예: Chrome)
driver = webdriver.Chrome()
wait = WebDriverWait(driver, 3)

# 웹페이지 열기
driver.get('https://ak.postcodebase.com/ko/randomaddress')

time.sleep(5)
# 클립보드에 복사 버튼 클릭 (버튼을 찾는 방식에 따라 수정 필요)

count = 0
while count < 70:
    time.sleep(0.7)
    click_copy_b()
    wait_time = random.uniform(1.7,2.6)
    # 클립보드에서 텍스트 가져오기
    copied_text = pyperclip.paste()
    result_df = pd.concat([result_df, addr_to_df(copied_text)], ignore_index=True)
    
    click_regen_b()

    time.sleep(wait_time)
    count += 9
result_df.to_csv(f"random_address_AK.csv",index=False)

prev_c = 'AK'  # 이전 c 값을 저장할 변수

links = driver.find_elements(By.XPATH, '//*[@id="block-system-main"]/div/div[2]/div[2]/div[2]/div/ul/li/a')

for idx, link in enumerate(links):
    c,pop = states_population[idx+1]
    print(c)
    count = 0
    new_df = pd.DataFrame()
    href = link.get_attribute("href")
    # 새 창 열기
    time.sleep(wait_time)
    time.sleep(0.5)  # 페이지 로딩 대기

    driver.execute_script("window.open(arguments[0], '_blank');", href)
    driver.switch_to.window(driver.window_handles[-1])
    
    while count < pop:
        wait_time = random.uniform(0.8,1.6)
        time.sleep(wait_time)
        click_copy_b()

        # 클립보드에서 텍스트 가져오기
        copied_text = pyperclip.paste()
        
        temp_df = addr_to_df(copied_text)
        print(temp_df)
        if temp_df.empty:
            slack1.send_msg("crawling address 중 오류 발생!")
            input("계속하려면 엔터 키를 누르세요...")
            continue

        new_df = pd.concat([new_df, temp_df], ignore_index=True)
        
        
        click_regen_b()
        time.sleep(wait_time)
        count += 9
    

    # 새로 생성된 파일 저장
    new_filename = f"random_address_{c}.csv"
    result_df = pd.concat([result_df,new_df],ignore_index=True)
    result_df.to_csv(new_filename, index=False)
    print(f"saved {new_filename}")
    
    # 이전 파일 삭제
    delete_prev_csv(f"random_address_{prev_c}.csv")
    print(f"deleted {prev_c}.csv")
    driver.close()
    driver.switch_to.window(driver.window_handles[0])
    prev_c = c


slack1.send_msg("crawling address 완료!")