from urllib.request import urlopen
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.alert import Alert
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.common.exceptions import NoSuchElementException
import time
import random
import pandas as pd
import os


os.chdir("/Users/jun/GitStudy/Data_4/Data/project5/tiktok")
key_word = ""


# 크롬 오픈
driver = webdriver.Chrome()
driver.maximize_window()
driver.implicitly_wait(5)

# 틱톡 오픈
url = 'https://www.tiktok.com/ko-KR'
driver.get(url)
driver.implicitly_wait(5)
wait = wait = WebDriverWait(driver, 5)

# 파서 지정
page = driver.page_source # page_source : selenium으로 불러온 페이지의 html코드 저장
# parser = BeautifulSoup(page,'html.parser')
# parser

# 로그인 버튼 클릭
driver.find_element(by='xpath', value='//*[@id="header-login-button"]/div').click()

# 전화/이메일/아이디 사용 버튼 클릭
driver.find_element(by='xpath', value='//*[@id="loginContainer"]/div/div/div/div[2]/div[2]').click()

# 이메일 또는 아이디로 로그인 클릭
driver.find_element(by='xpath', value='//*[@id="loginContainer"]/div/form/div[1]/a').click()

# 이메일 입력
input_email = driver.find_element(by='xpath', value='//*[@id="loginContainer"]/div[2]/form/div[1]/input')
input_email.send_keys('chameleo1022@naver.com')

# 비밀번호 입력
input_password = driver.find_element(by='xpath', value='//*[@id="loginContainer"]/div[2]/form/div[2]/div/input')
input_password.send_keys('#project5')

# 로그인버튼 클릭
driver.find_element(by='xpath', value='//*[@id="loginContainer"]/div[2]/form/button').click() #추후 돌아가는지 확인
wait_time = random.uniform(2,2.4)
time.sleep(wait_time)
time.sleep(wait_time)
time.sleep(15)

# 검색 아이콘 클릭
wait = WebDriverWait(driver, 30)  # 최대 10초 기다림
search_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="app"]/div[2]/div[1]/div/div[2]/div[2]/button/div/div[2]'))).click()

# 검색어 입력
search = driver.find_element(By.XPATH, '//*[@id="app"]/div[2]/div[1]/div/div[5]/div[1]/div[2]/form/input')
search.send_keys(key_word)

# 키보드 엔터
search.send_keys(Keys.ENTER)

# 동영상 탭 클릭
driver.find_element(by='xpath', value='//*[@id="tabs-0-tab-search_video"]').click()

# 사람인거 인증하는 창 나옴 -> 대기 10초 걸어줌 / 최대한 빨리 수동으로 그림 맞추기 
driver.implicitly_wait(30)

# 페이지 로딩 대기 (동적으로 로드될 수 있음)
wait_time = random.uniform(0.5, 1.5)
time.sleep(wait_time)

time.sleep(wait_time)


wait = WebDriverWait(driver, 7)
search_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="tabs-0-panel-search_video"]/div/div/div[1]/div[1]'))).click()

# 첫번 째 동영상 클릭

# for문을 이용하여 n개의 게시물에서 좋아요수를 추출하여 리스트에 저장하기
like_list = []
comment_list = []
save_list = []
name_list = []
date_list = []
infos_tags_list =[]
hash_tag_list = []



for i in range(250):
    try:
    # '자세히' 버튼이 존재하면 클릭
        expand_button = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'css-1r94cis-ButtonExpand'))
        )
        expand_button.click()
        print(i,'번:',"자세히 버튼 클릭 성공")
    except Exception as e:
        # 버튼이 없거나 클릭할 수 없을 경우 처리
        print(i,'번:',"자세히 버튼이 없거나 클릭할 수 없습니다.")

    # 영상설명 추출
    try:
        infos_tags = driver.find_element(By.CSS_SELECTOR, value = 'h1[data-e2e="browse-video-desc"]')
        infos_tags_text = infos_tags.text
        infos_tags_list.append(infos_tags_text)
    except NoSuchElementException:
        infos_tags_list.append('')   

    # 잠시 멈춤
    driver.implicitly_wait(5)

    #업로드 날짜 추출
    try:
        date = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '.css-gg0x0w-SpanOtherInfos.evv7pft3'))
            )
        
        # 잠시 멈춤
        driver.implicitly_wait(5)

        date_text = date.text
        date_text = date_text.split('·')[1].strip()
        date_list.append(date_text)

    except StaleElementReferenceException:
        print("StaleElementReferenceException 발생: 요소가 더 이상 유효하지 않습니다.")
        date = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '.css-gg0x0w-SpanOtherInfos.evv7pft3'))
            )
        
        # 잠시 멈춤
        driver.implicitly_wait(5)

        date_text = date.text
        date_text = date_text.split('·')[1].strip()
        date_list.append(date_text)
    
    except TimeoutException:
        print("업로드 날짜를 찾을 수 없습니다.")

    # 틱톡커 이름 추출 
    name = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, 'span[data-e2e="browse-username"]'))
    )
    name_text = name.text
    name_list.append(name_text)

    # 좋아요수 추출
    like = WebDriverWait(driver,10).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'strong[data-e2e="browse-like-count"]'))
    )
    like_text = like[0].text #각 게시물에서 첫번째 요소만 처리/게시물 댓글의 좋아요까지 같은 셀렉터 이름을 사용함
    like_list.append(like_text)

    # 댓글수 추출
    comment = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, 'strong[data-e2e="browse-comment-count"]'))
    )
    comment_text = comment.text
    comment_list.append(comment_text)

    # 저장수 추출
    save = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, 'strong[data-e2e="undefined-count"]'))
    )
    save_text = save.text
    save_list.append(save_text)

    time.sleep(wait_time)

    #if i < n:
    driver.find_element(By.TAG_NAME,'body').send_keys(Keys.ARROW_DOWN)
    #    time.sleep(random.randint(2,5))

#print('조회수 리스트:',view_list)
print('좋아요수 리스트:',like_list)
print('댓글수 리스트:',comment_list)
print('저장수 리스트:',save_list)
print('틱톡커 이름 리스트:',name_list)
print('업로드 날짜 리스트:',date_list)
print('영상 설명,해시태그 리스트:',infos_tags_list)

# 데이터 프레임으로 만들기

df = pd.DataFrame({#'view':view_list,
'like':like_list,
'comment':comment_list,
'save':save_list,
'titoker_name':name_list,
'date':date_list,
'info':infos_tags_list,
#'hash_tag':hash_tag_list
})

df.to_csv(key_word+'.csv',index=False, encoding="utf-8-sig")