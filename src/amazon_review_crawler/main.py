"""
File: src/amazon_review_crawler/main.py

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
무엇인가 (What)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Amazon K-Beauty 5개 브랜드(COSRX, Beauty of Joseon, Dr. Jart+, PURITO,
I'm from) 의 상품 메타데이터와 리뷰를 Selenium으로 수집하고 MySQL에 적재하는
엔드투엔드 크롤링 스크립트.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
왜 필요한가 (Why)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
신규 인디 K-Beauty 브랜드(3-beaty)의 미국 Amazon 진출 전략 수립을 위해
경쟁사 리뷰 raw data를 수집. 이 데이터가 EDA / LDA 토픽 모델 / GraphRAG
챗봇 지식그래프의 입력 원천이 된다.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
어디서 쓰이는가 (Where)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
단독 실행 스크립트 (``python main.py``). 수집 결과는 MySQL ``items`` /
``reviews`` 테이블에 적재되고, 이후 노트북에서 SELECT 해 분석에 사용.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
언제 실행되는가 (When)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
수동 배치 실행. 브랜드 추가·재수집이 필요할 때 하단 ``crawl_amazon()``
호출 인자를 변경하고 실행.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
흐름 (How)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Selenium Chrome 실행
  → ``open_amazon_keyword()``  : 키워드 검색
  → ``amazon_login()``         : 계정 로그인 (.env CRAWLER_ID/PW)
  → ``brand_filter_refresh()`` : 브랜드 사이드바 필터 클릭
  → ``select_best_sellers()``  : Best Sellers 정렬
  → 카테고리 × 아이템 이중 루프
      - 상품 메타데이터 수집 → ``load_items()``  → MySQL items
      - 리뷰 페이지 수집    → ``load_reviews()`` → MySQL reviews
  → ``send_msg()``             : Slack 완료 알림

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
관련 모듈 (Related)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- mysql.py       : MySqlClient — DB 연결·upsert·insert-ignore
- items.py       : load_items() — items 테이블 스키마 + 적재
- reviews.py     : load_reviews() — reviews 테이블 스키마 + 적재
- util/slack.py  : send_msg() — Slack 완료/에러 알림
"""
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import Select
from mysql import MySqlClient
from reviews import load_reviews
from items import load_items
from util.slack import send_msg
import os
import json
import time
import pandas as pd
import random
from dotenv import find_dotenv, load_dotenv
load_dotenv(find_dotenv())

# ─────────────────────────────────────────────────────────────────────────────
# Selenium 튜닝 상수
# ─────────────────────────────────────────────────────────────────────────────
# 이전에는 wait/sleep 값들이 파일 전체에 흩어져 있어서 (15+ 위치) 튜닝 시 grep
# 으로 일일이 찾아야 했음. 한 곳에 모아 두면 anti-bot 회피 / 안정성 튜닝 시 한 번
# 만 수정. 새 값 추가도 여기에 등록 후 참조.

# WebDriverWait 의 explicit wait timeout (sec). 페이지 element 가 나타나길 기다리는
# 최대 시간. 너무 짧으면 timeout, 길면 실패 감지 늦음.
WAIT_TIMEOUT_SEC = 3

# 짧은 click-to-click 간격 (sec). anti-bot 감지 회피용 jitter — 너무 일정한 클릭
# 패턴은 봇으로 의심받음. 0.05~0.15 = 50~150ms 범위에서 randomize.
SHORT_JITTER_RANGE = (0.05, 0.15)

# 페이지 전환 (검색 결과 → 상품 페이지 등) 후 안정화 대기 (sec).
# 0.7~1.0 = 700~1000ms. DOM 렌더링 완료 + script 실행 여유.
PAGE_LOAD_JITTER_RANGE = (0.7, 1.0)

# 스크롤 / 페이지네이션 클릭 후 짧은 안정 대기 (sec). 고정값 (jitter 불필요한 위치).
SCROLL_PAUSE_SEC = 0.2

# 페이지 완전 로드 (네트워크 트래픽 끝남 추정) 대기 (sec).
HEAVY_PAGE_LOAD_SEC = 2

# 페이지 점프 (다음 페이지 클릭) 대기 (sec). HEAVY_PAGE_LOAD 보다 약간 짧음.
NEXT_PAGE_LOAD_SEC = 1.5

# Amazon "Brand" 필터의 체크박스 ID prefix. 각 브랜드별 ID 는 `BRAND_FILTER_IDS`
# dict 에 매핑.
#
# 왜 prefix 만 상수로? Amazon UI 가 가끔 prefix 를 갱신해도 dict 의 값 (브랜드별
# 숫자 코드) 는 안 바뀌어서. 갱신 시 여기 한 곳만 수정.
BRAND_FILTER_CSS_PREFIX = r"#p_123\/"
BRAND_FILTER_CSS_SUFFIX = " > span > a > span"

# 브랜드별 Amazon "Brand" 필터의 고유 ID. Amazon 이 internal 로 부여하는 hash 라
# refresh-stable 함. 새 브랜드 추가 시 Amazon 사이트에서 "Inspect" 로 확인 후 등록.
BRAND_FILTER_IDS: dict[str, str] = {
    "COSRX":            "241477",
    "Beauty of Joseon": "591445",
    "Dr. Jart+":        "452045",
    "PURITO":           "312482",
    "I'm from":         "654399",
}


# 아마존 크롤링 함수

driver = webdriver.Chrome()
wait = WebDriverWait(driver, WAIT_TIMEOUT_SEC)


# Amazon 로그인 자격증명 (.env 의 CRAWLER_* 사용 — env-prefix 규칙)
ID = os.environ.get("CRAWLER_ID")
PW = os.environ.get("CRAWLER_PW")

# DB 연결 정보 — split form 그대로 .env 에 유지하고 여기서 URL 조립
_DB_HOST = os.environ.get("CRAWLER_DB_HOST")
_DB_USER = os.environ.get("CRAWLER_DB_USER")
_DB_PW   = os.environ.get("CRAWLER_DB_PASSWORD")
_DB_NAME = os.environ.get("CRAWLER_DB_NAME")
_DB_PORT = os.environ.get("CRAWLER_DB_PORT", "3306")

_master_url = (
    f"mysql+mysqlconnector://{_DB_USER}:{_DB_PW}@{_DB_HOST}:{_DB_PORT}/{_DB_NAME}"
)
# replica는 옵셔널 — .env 에 CRAWLER_DB_REPLICA_URL 있을 때만 활성화
_replica_url = os.environ.get("CRAWLER_DB_REPLICA_URL") or None

# MySqlClient 생성 시 즉시 preflight ping → DB 안 켜져있으면 여기서 친절한 에러로 멈춤
my_sql_client = MySqlClient(master_url=_master_url, replica_url=_replica_url)

ASIN_list = []

def amazon_login(id: str, pw: str):
    """
    Amazon 계정으로 로그인하는 함수.

    Args:
        id (str): Amazon 계정의 이메일 또는 아이디.
        pw (str): Amazon 계정의 비밀번호.
    """
    try:
        # 'Sign in' 버튼에 마우스를 올려 드롭다운 메뉴를 표시
        account_element = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "nav-link-accountList"))
        )
        ActionChains(driver).move_to_element(account_element).perform()

        # 'Sign in' 버튼 클릭
        sign_in_button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "#nav-flyout-ya-signin a.nav-action-signin-button"))
        )
        sign_in_button.click()

        # 이메일 입력 필드 대기
        email_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "ap_email"))
        )
        email_input.send_keys(id + Keys.RETURN)
        print("email end")

        # QR 코드 팝업 확인 및 닫기 처리
        try:
            qr_popup_close_button = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Close']"))  # 팝업 닫기 버튼의 Xpath
            )
            qr_popup_close_button.click()  # 팝업 닫기
        except Exception:
            print("QR 코드 팝업이 없습니다. 진행합니다.")

        password_input = WebDriverWait(driver, 2).until(
            EC.presence_of_element_located((By.ID, "ap_password"))
        )
        password_input.send_keys(pw + Keys.RETURN)

    except Exception as e:
        print(f"오류 발생: {e}")


def set_sort_by_most_recent_with_scroll():
    """
    스크롤을 내려 'Sort by' 드롭다운에서 'Most recent' 옵션을 선택하는 함수.
    """
    try:
        # 'Sort by' 드롭다운 버튼 대기
        dropdown = wait.until(
            EC.presence_of_element_located((By.ID, "sort-order-dropdown"))
        )
        
        # 드롭다운이 화면에 보이도록 스크롤
        driver.execute_script("arguments[0].scrollIntoView();", dropdown)
        
        # Select 객체를 사용해 드롭다운 조작
        select = Select(dropdown)
        
        # 'Most recent' 옵션 선택
        select.select_by_value("recent")
    except Exception as e:
        print(f"Error setting sort by with scroll: {e}")
        

def click_next_item_page():
    """
    "다음 아이템 페이지" 버튼을 찾아 클릭하여 다음 아이템 페이지로 이동하는 함수.

    Returns:
        bool: "다음 페이지" 버튼 클릭 성공 여부 (성공 시 True, 실패 시 False).
    """
    wait_time = random.uniform(*SHORT_JITTER_RANGE)
    time.sleep(wait_time)
    try:
        # Next page 버튼 기다리기
        next_page_button = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'li.s-list-item-margin-right-adjustment > span > a.s-pagination-next'))
        )
        
        # execute_script를 사용해 클릭
        driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'nearest'});", next_page_button)
        time.sleep(0.1)  # 스크롤 후 잠시 대기
        driver.execute_script("arguments[0].click();", next_page_button)

        print("Successfully clicked the Next Item Page button.")
        return True
    except Exception as e:
        print(f"Error clicking Next Page button: {e}")
        return False


def click_next_review_page():
    """
    "다음 리뷰 페이지" 버튼을 찾아 클릭하여 다음 아이템 페이지로 이동하는 함수.

    Returns:
        bool: "다음 페이지" 버튼 클릭 성공 여부 (성공 시 True, 실패 시 False).
    """
    try:
        # Next page 버튼 기다리기
        time.sleep(SCROLL_PAUSE_SEC)
        next_page_button = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".a-pagination .a-last a"))
        )
        # 버튼 클릭
        next_page_button.click()
        print("Successfully clicked the Next Review Page button.")
    except Exception as e:
        print(f"Error clicking Next Page button: {e}")
        return False
    return True
    

def score_filter():
    """
    상품 리뷰의 별점 필터(예: 4성)를 클릭하여 필터링하는 함수.
    
    Returns:
        None
    """
    star_filter_selector = '.a-icon.a-icon-star-medium.a-star-medium-4'
    try:
        # 요소가 로드될 때까지 기다림
        star_filter_element = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, star_filter_selector))
        )
        # 요소 클릭
        star_filter_element.click()
        print("Star filter clicked successfully.")
    except Exception as e:
        print(f"Error while waiting for or clicking the star filter: {e}")


def select_best_sellers():
    """
    Selenium을 사용해 드롭다운 메뉴에서 'Best Sellers' 옵션을 선택한 후 페이지 로드를 기다리는 함수.
    
    Args:
        driver (webdriver): Selenium WebDriver 객체.
        wait_time (int): 대기 시간 (초) 기본값은 10초.
    Returns:
        None
    """
    try:
        # WebDriverWait 객체 생성
        # 드롭다운 메뉴 요소 기다림
        dropdown_element = wait.until(EC.presence_of_element_located((By.ID, "s-result-sort-select")))
        # 드롭다운 메뉴 초기화
        select = Select(dropdown_element)
        
        # "Best Sellers" 옵션 선택 (value 사용)
        select.select_by_value("exact-aware-popularity-rank")
        
        # 다음 페이지 로드를 기다림
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.s-main-slot")))
        print("Successfully selected 'Best Sellers' and waited for the next page to load.")
    except Exception as e:
        print(f"An error occurred: {e}")


def open_amazon_keyword(keyword="skin+care"):
    """
    Amazon 웹사이트에서 특정 키워드로 검색을 수행

    Args:
        keyword (str, optional): 검색하고싶은 아이템 키워드
    
    Returns:
        None
    """
    try:
        # 아마존 검색 페이지 열기
        driver.get("https://www.amazon.com")
        driver.implicitly_wait(5)  # 페이지 로딩 대기
        wait_time = random.uniform(*SHORT_JITTER_RANGE)
        time.sleep(wait_time)

        wait_time = random.uniform(*SHORT_JITTER_RANGE)
        time.sleep(wait_time)
        
        search_box = driver.find_element(By.ID, 'twotabsearchtextbox')

        # 검색어 입력
        search_box.clear()  # 혹시 검색창에 이전 텍스트가 있다면 삭제
        search_box.send_keys(keyword)  # "skin care" 입력

        # 검색 실행 (Enter 키 사용 또는 검색 버튼 클릭)
        search_box.send_keys(Keys.RETURN)
    except Exception as e:
        print(f"error occurred in open_amazon_keyword, error : {e}")


def get_asin_from_sql():
    """
    get_asin_from_sql 함수는 데이터베이스에서 'ASIN' 리스트를 조회하여 반환합니다. 
    조회된 결과가 없으면 빈 리스트를 반환합니다.

    Returns:
        list: 데이터베이스에서 조회한 'ASIN' 값들의 리스트 (없으면 빈 리스트).

    예외 처리:
        데이터베이스 쿼리 실행 중 오류 발생 시 예외 메시지가 출력됩니다.
    """
    asin_list =[]
    try :
        query = "SELECT ASIN FROM items"  # items 테이블에서 모든 데이터를 조회
        df = my_sql_client.fetch_as_dataframe(query)
        asin_list = df['ASIN'].to_list()
    except Exception as e:
        print(f"error occurred from get_asin_from_sql {e}")
    finally : return asin_list


def check_DrJart():
    """
    현재 페이지에 Dr. Jart+ 브랜드 필터 요소가 존재하는지 확인하는 함수.

    Returns:
        bool: Dr. Jart+ 필터 요소 존재 여부 (True / False).
    """
    # Dr. Jart+ 셀렉터를 BRAND_FILTER_IDS 에서 재사용 (이중 하드코딩 방지).
    drjart_id = BRAND_FILTER_IDS["Dr. Jart+"]
    drjart_css = f"{BRAND_FILTER_CSS_PREFIX}{drjart_id}{BRAND_FILTER_CSS_SUFFIX}"
    # JS querySelector 용은 escape 한 번 더 (Python \\ → JS \).
    drjart_css_js = drjart_css.replace("\\", "\\\\")
    try:
        # 요소가 로드될 때까지 기다림
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, drjart_css)))

        # JavaScript를 사용해 해당 요소를 찾음
        element = driver.execute_script(
            f"return document.querySelector('{drjart_css_js}');"
        )
        # 요소 존재 여부 확인
        if element:
            print("요소를 성공적으로 찾았습니다.")
            return True
        else:
            print("요소를 찾을 수 없습니다.")
            return False
    except Exception as e:
        # 예외 처리
        print(f"오류 발생: {e}")
        return False
    


def brand_filter_refresh(brand: str):
    """
    Amazon 검색 결과 사이드바에서 특정 브랜드 필터 체크박스를 클릭하는 함수.

    브랜드별 CSS 셀렉터(``#p_123\\/...``)가 하드코딩되어 있으며, 클릭 후
    페이지 리프레시가 완료될 때까지 대기한다.

    Args:
        brand (str): 필터링할 브랜드명.
            지원 값: "COSRX", "Beauty of Joseon", "Dr. Jart+", "PURITO", "I'm from"

    Returns:
        bool: 필터 클릭 및 페이지 리프레시 성공 여부.
    """
    # brands 필터 — 체크하면 해당 브랜드만 나옴. 브랜드별 CSS 셀렉터는 파일 상단
    # `BRAND_FILTER_IDS` dict 참조 (Amazon UI 갱신 시 한 곳만 수정).
    try:
        brand_id = BRAND_FILTER_IDS.get(brand)
        if brand_id is None:
            raise KeyError(
                f"등록 안 된 브랜드: {brand!r}. `BRAND_FILTER_IDS` 에 추가 필요."
            )
        element_locator = (
            By.CSS_SELECTOR,
            f"{BRAND_FILTER_CSS_PREFIX}{brand_id}{BRAND_FILTER_CSS_SUFFIX}",
        )
    
            
        # 클릭할 요소의 CSS 셀렉터
        
        # 요소가 클릭 가능할 때까지 기다림
        element = wait.until(EC.element_to_be_clickable(element_locator))

        # 현재 페이지 상태를 저장
        old_page = driver.find_element(By.TAG_NAME, 'html')

        # 요소 클릭
        element.click()
        print("요소를 클릭했습니다. 페이지 리프레시를 기다리는 중...")

        # 페이지 리프레시 대기
        wait.until(EC.staleness_of(old_page))  # 기존 페이지가 사라질 때까지 대기
        print("페이지 리프레시 완료.")
        return True

    except TimeoutException:
        print("페이지 리프레시가 완료되지 않았습니다.")
        return False

    except NoSuchElementException:
        print("클릭할 요소를 찾을 수 없습니다.")
        return False

    except Exception as e:
        print(f"오류 발생: {e}")
        return False



def get_description():
    """
    현재 Amazon 상품 페이지의 "About this item" 섹션 텍스트를 JSON 문자열로 추출.

    ``feature-bullets`` ID 아래 ``li`` 항목들을 수집해 줄바꿈으로 합친 뒤
    ``{"description": "..."}`` 형태의 JSON 문자열로 반환.

    Returns:
        str | None: JSON 문자열. 요소 부재 또는 오류 시 None.
    """
    try :
        result = {}
        # "feature-bullets" ID가 있는 요소를 기다린 후 가져오기
        feature_bullets = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "feature-bullets"))
        )
        # "About this item" 섹션에서 텍스트 추출
        feature_items = feature_bullets.find_elements(By.CSS_SELECTOR, "ul.a-unordered-list li span.a-list-item")

        # 텍스트를 추출하고 한 문자열로 합침
        description = "\n".join([item.text.strip() for item in feature_items])
        result["description"] = description

        json_result = json.dumps(result, ensure_ascii=False, indent=4)
        return json_result
    except Exception as e:
        print(f"scrape_product_details 오류 발생: {e}")
        return None


def cosrx_description_to_json():
    """
    COSRX 상품 상세 페이지의 visual-rich-product-description 섹션을 JSON으로 추출.

    COSRX는 일반 ``feature-bullets`` 대신 ``visual-rich-product-description``
    컨테이너를 사용하므로 별도 함수로 분리. 섹션 제목(h4)–내용(visualRpdText)
    쌍을 dict로 구성해 JSON 문자열로 반환.

    Returns:
        str | None: JSON 문자열. 요소 부재 또는 오류 시 None.
    """
    try:
        # 결과를 저장할 딕셔너리
        result = {}
        # visual-rich-product-description 안의 모든 섹션 가져오기
        container = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "visual-rich-product-description"))
        )
        sections = container.find_elements(By.CSS_SELECTOR, ".a-column.a-span4")
        for section in sections:
            try:
                # 제목 (h4)와 내용 (span) 추출
                time.sleep(SCROLL_PAUSE_SEC)  # 페이지 로드 안정성을 위해 짧은 대기
                title = section.find_element(By.CSS_SELECTOR, "h4").text.strip()
                content = section.find_element(By.CSS_SELECTOR, ".visualRpdText").text.strip()
                result[title] = content
            except Exception as e:
                # 일부 섹션에서 데이터가 없을 경우 무시
                print(f"섹션에서 데이터 추출 실패: {e}")
                continue

        # JSON 형식으로 변환하여 반환
        json_result = json.dumps(result, ensure_ascii=False, indent=4)
        return json_result
    except Exception as e:
        print(f"scrape_product_details 오류 발생: {e}")
        return None


def is_sponsored(item):
    """
    검색 결과 아이템 요소에 Sponsored 라벨이 있는지 확인하는 함수.

    Args:
        item: Selenium WebElement — 검색 결과 리스트의 단일 아이템.

    Returns:
        bool: Sponsored 라벨 존재 시 True, 없거나 확인 불가 시 False.
    """
    try:
        if item.find_elements(By.CLASS_NAME, "puis-sponsored-label-text"):  # Sponsored 라벨 존재 확인
            ("Sponsored_passed")
            return True  # Sponsored 항목은 건너뜀
    except Exception as e:
        print(f"Sponsored 라벨 확인 중 에러 발생: {e}")
        # 에러가 발생하면 Sponsored 여부를 무시하고 다음 로직 실행
    return False

def click_BeautyPersonalCareDepartment():
    """
    Amazon 사이드바에서 'Beauty & Personal Care' 카테고리 필터를 클릭하는 함수.

    크롤링 대상 카테고리를 Beauty & Personal Care 로 좁히기 위해 사용.
    현재 ``crawl_amazon()`` 내에서 직접 호출하진 않으나, 수동 실행 시 활용 가능.
    """
    # Beauty & Personal Care Department 선택 (클릭))
    category_Department = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#n\\/3760911')))
    # 요소를 클릭하거나 원하는 작업 수행
    category_Department.click()

def _scrape_item_details(asin: str, category_name: str, cnt: int) -> dict:
    """현재 driver 탭이 *Amazon 상품 상세 페이지* 라는 가정 하에 메타데이터 추출.

    원본 ``crawl_amazon`` 안에 inline 으로 들어있던 약 120 줄의 selector 시퀀스
    를 단일 함수로 분리. nested loop 안에서 실패 시 어떤 selector 가 깨졌는지
    구분 가능하게 됨.

    Args:
        asin: 상품 ASIN (호출부에서 이미 추출 — 재추출 안 함).
        category_name: 현재 카테고리명 (수집 결과에 함께 저장).
        cnt: 현재 카테고리 내 누적 순서 (1-based, best-seller 정렬 기준).

    Returns:
        ``load_items`` 가 받는 schema dict. 부가로 ``_has_ratings`` 키 포함 —
        호출부가 review 수집 여부 판단용 (downstream 저장 직전 drop).

    Note:
        실패한 selector 는 fallback 문자열 (``"No brand"``, ``"No star"`` 등)
        대입 — 원본 동작 보존. price 만 number 변환 시 NaN 처리.
    """
    # 상품 페이지 완전 로드 대기 (productTitle = key 식별자).
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "productTitle")))

    # detail bullets — "Brand: COSRX", "Origin: Korea" 같은 key:value 페어 추출.
    detail_bullets = driver.find_element(By.ID, "detailBullets_feature_div")
    product_details = detail_bullets.find_elements(By.CSS_SELECTOR, "li span.a-list-item")
    detail_dict = {}
    for detail in product_details:
        try:
            key = detail.find_element(By.TAG_NAME, "span").text.split(":")[0].strip()
            value = detail.text.split(":")[1].strip()
            detail_dict[key] = value
        except Exception:
            # selector 못 찾은 element 는 skip — 다음 detail 시도.
            continue

    # 기본 메타데이터 (selector 없을 수도 있어 len 체크 + fallback).
    title = driver.find_element(By.ID, "productTitle").text
    print(f"Title: {title}")
    reviews = (
        driver.find_element(By.ID, "acrCustomerReviewText").text
        if len(driver.find_elements(By.ID, "acrCustomerReviewText")) > 0
        else "No ratings"
    )
    brand = (
        driver.find_element(By.CSS_SELECTOR, "tr.po-brand .po-break-word").text
        if len(driver.find_elements(By.CSS_SELECTOR, "tr.po-brand .po-break-word")) > 0
        else "No brand"
    )
    description = get_description()
    print(description[:5])

    special_feature = (
        driver.find_element(By.CSS_SELECTOR, "tr.po-special_feature .po-break-word").text
        if len(driver.find_elements(By.CSS_SELECTOR, "tr.po-special_feature .po-break-word")) > 0
        else "No special feature"
    )

    # 가격 — Amazon 가격 표시가 single / bundle 두 종류라 fallback 체인.
    is_bundle = False
    try:
        price_whole = driver.find_element(
            By.CSS_SELECTOR, "#corePrice_feature_div span.a-price span.a-price-whole"
        ).text
        price_fraction = driver.find_element(
            By.CSS_SELECTOR, "#corePrice_feature_div span.a-price span.a-price-fraction"
        ).text
        price = price_whole + "." + price_fraction
        print(price, "1")
    except:
        # 번들 가격일 가능성 — 별도 selector 시도.
        try:
            price = driver.execute_script("""
                var priceElement = document.querySelector("#corePrice_desktop > div > table > tbody > tr:nth-child(2) > td.a-span12 > span.a-price.a-text-price.a-size-medium.apexPriceToPay > span:nth-child(2)");
                return priceElement ? priceElement.textContent : null;
            """)
            if price:
                is_bundle = True
                price = price.split("$")[1]
            else:
                is_bundle = False
        except:
            price = None
            is_bundle = False
        print("가격:", price)
        print("번들 여부:", is_bundle)

    # 평점 + 리뷰 수.
    total_star = (
        driver.find_element(By.CSS_SELECTOR, ".a-popover-trigger .a-size-small.a-color-base").text
        if len(driver.find_elements(By.CSS_SELECTOR, ".a-popover-trigger .a-size-small.a-color-base")) > 0
        else "No star"
    )
    total_rating_counts = (
        driver.find_element(By.CSS_SELECTOR, "#acrCustomerReviewText").text
        if len(driver.find_elements(By.CSS_SELECTOR, "#acrCustomerReviewText")) > 0
        else "No rating"
    )
    global_rating_count = (
        total_rating_counts.strip("()").replace(",", "")
        if total_rating_counts != "No rating"
        else "No rating"
    )
    print(f"global_rating_count: {global_rating_count}")

    # Ingredients — 필수 정보 (GraphRAG entity extraction 의 입력). 부재 시 None.
    try:
        ingredients_elements = driver.find_elements(
            By.CSS_SELECTOR, "#important-information > div:nth-child(3) > p:nth-child(3)"
        )
        if ingredients_elements:
            ingredients_text = ingredients_elements[0].text.strip()
        else:
            ingredients_text = None
    except Exception as e:
        print(f"Error occurred while fetching Ingredients: {e}")
        ingredients_text = None
    print(f"Ingredients: {ingredients_text}")

    # Best Sellers Rank — detail-bullet-list 안에서 "Best Sellers Rank" 키워드 검색.
    best_sellers_elements = driver.find_elements(
        By.CSS_SELECTOR, "ul.detail-bullet-list > li > span.a-list-item"
    )
    best_sellers_rank_text = "No result"
    for element in best_sellers_elements:
        if "Best Sellers Rank" in element.text:
            try:
                best_sellers_rank_text = element.text.split(":")[1].strip()
                break
            except Exception:
                best_sellers_rank_text = "No result"
                break

    print()
    print(f"ASIN: {asin}")
    print(f"Title: {title}")
    print(f"global_rating_count: {global_rating_count}")
    print(f"price: {price}")
    print()

    return {
        "ASIN": asin,
        "title": title,
        "order": cnt,
        "category": category_name,
        "brand": brand,
        "price": price,
        "global_rating_count": global_rating_count,
        "description": description,
        "Special_Feature": special_feature,
        "total_star_mean": total_star,
        "detail_dict": detail_dict,
        "best_sellers_rank_Feature": best_sellers_rank_text,
        "Ingredients": ingredients_text,
        "is_bundle": is_bundle,
        # 호출부가 review 수집 여부 판단 + downstream 저장 직전 drop.
        "_has_ratings": reviews != "No ratings",
    }


def _scrape_item_reviews(asin: str, title: str, max_reviews: int = 20000) -> list[dict]:
    """현재 driver 탭이 *Amazon 상품 상세 페이지* 라는 가정 하에 review pagination.

    "See all reviews" 링크 클릭 → "Most recent" 정렬 → review 페이지 순회.
    원본 ``crawl_amazon`` 안의 review 수집 80 줄을 단일 함수로 분리.

    Args:
        asin: 상품 ASIN (review_num key 생성용).
        title: 상품 제목 (review row 에 함께 저장).
        max_reviews: 최대 수집 review 수. 기본 20,000.

    Returns:
        review dict list. 실패 / "See all reviews" 링크 부재 시 빈 리스트.
    """
    reviews_list: list[dict] = []
    try:
        more_reviews_link = wait.until(
            EC.presence_of_element_located((
                By.CSS_SELECTOR,
                "#reviews-medley-footer > div.a-row.a-spacing-medium > a[data-hook='see-all-reviews-link-foot']",
            ))
        )
        print("스크롤 이동")
        time.sleep(0.5)
        more_reviews_link.click()
        print("링크 클릭")
        set_sort_by_most_recent_with_scroll()
        print("스크롤 실행 완료")

        review_count = 0
        try:
            while review_count < max_reviews:
                wait_time = random.uniform(*PAGE_LOAD_JITTER_RANGE)
                time.sleep(wait_time)
                try:
                    detail_reviews = driver.find_elements(
                        By.CSS_SELECTOR, 'div[class="a-section celwidget"]'
                    )
                except Exception as e:
                    print(f"뭔가 잘못됐네 단단히 : {e}")
                    break

                for detail_review in detail_reviews:
                    try:
                        time.sleep(0.03)
                        # review 안의 profile-name 이 보일 때까지 대기 — Amazon 의
                        # lazy-load 우회.
                        WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, "span.a-profile-name"))
                        )
                        review_div_id = detail_review.get_attribute("id")
                        customer_id = (
                            review_div_id.split("-")[-1]
                            if "customer_review" in review_div_id
                            else "No customer ID"
                        )
                        customer_name = (
                            detail_review.find_element(By.CSS_SELECTOR, "span[class='a-profile-name']").text
                            if len(detail_review.find_elements(By.CSS_SELECTOR, "span[class='a-profile-name']")) > 0
                            else "No Name"
                        )
                        date = (
                            detail_review.find_element(By.CSS_SELECTOR, "span[data-hook='review-date']").text
                            if len(detail_review.find_elements(By.CSS_SELECTOR, "span[data-hook='review-date']")) > 0
                            else "No date"
                        )
                        review_title = (
                            detail_review.find_element(By.CLASS_NAME, "review-title").text
                            if len(detail_review.find_elements(By.CLASS_NAME, "review-title")) > 0
                            else "No title"
                        )
                        review_rating_element = detail_review.find_elements(By.CSS_SELECTOR, "span.a-icon-alt")
                        review_rating = (
                            driver.execute_script(
                                "return arguments[0].innerText;", review_rating_element[0]
                            )
                            if len(review_rating_element) > 0
                            else "No review"
                        )
                        content = (
                            detail_review.find_element(By.CSS_SELECTOR, "span[data-hook='review-body']").text
                            if len(detail_review.find_elements(By.CSS_SELECTOR, "span[data-hook='review-body']")) > 0
                            else "No content"
                        )

                        print(
                            f"Review {review_count} - customer_id: {customer_id}, "
                            f"customer_name: {customer_name}, review_title: {review_title}, "
                            f"review_rating: {review_rating}"
                        )
                        reviews_list.append({
                            "review_num": asin + "__" + str(review_count),
                            "ASIN": asin,
                            "customer_id": customer_id,
                            "customer_name": customer_name,
                            "title": title,
                            "date": date,
                            "review_rating": review_rating,
                            "content": content,
                        })
                        review_count += 1
                    except Exception as e:
                        print(f"Error extracting review {review_count + 1}: {e}")
                        continue
                if review_count >= max_reviews:
                    break
                if not click_next_review_page():
                    break
        except Exception as e:
            print(f"Error retrieving reviews: {e}")
    except Exception as e:
        # "See all reviews" 링크 자체가 없는 경우 (리뷰 0 인 신상품 등) — 정상 흐름.
        print(f"see_more_reviews ERROR : {e}")

    return reviews_list


def _save_single_item(item_dict: dict, reviews_list: list[dict]) -> None:
    """단일 item + 그 review 들을 MySQL 에 upsert.

    원본의 DataFrame 변환 + load_items / load_reviews 흐름 (~30 줄) 을 분리.
    ``detail_dict`` 가 nested 라 json_normalize 후 JSON 문자열로 평탄화.

    Args:
        item_dict: ``_scrape_item_details`` 반환 dict.
        reviews_list: ``_scrape_item_reviews`` 반환 list. 빈 리스트면 호출부에서
            "No content" placeholder 1 row 채워서 넘김 (review_id FK 보장).
    """
    item_df = pd.json_normalize([item_dict])

    # detail_dict.X 컬럼들을 다시 nested dict 로 묶음.
    detail_cols = [col for col in item_df.columns if col.startswith("detail_dict.")]
    if detail_cols:
        item_df["detail_dict"] = item_df[detail_cols].apply(
            lambda row: {col.split(".")[1]: row[col] for col in detail_cols if pd.notnull(row[col])},
            axis=1,
        )
        item_df.drop(columns=detail_cols, inplace=True)

    # JSON 문자열로 변환 (MySQL TEXT 컬럼 저장용).
    item_df["detail_dict"] = item_df["detail_dict"].apply(json.dumps)
    # 숫자 컬럼 강제 변환 (NaN 허용).
    item_df["price"] = pd.to_numeric(item_df["price"], errors="coerce")
    item_df["total_star_mean"] = pd.to_numeric(item_df["total_star_mean"], errors="coerce")

    # _has_ratings 는 schema 에 없는 control flow 용 컬럼 — drop.
    if "_has_ratings" in item_df.columns:
        item_df.drop(columns=["_has_ratings"], inplace=True)

    load_items(df=item_df, my_sql_client=my_sql_client)

    review_df = pd.json_normalize(reviews_list)
    print()
    print(review_df.columns)
    load_reviews(df=review_df, my_sql_client=my_sql_client)
    print("=" * 50)


def _process_one_item(
    item, idx: int, ASIN_list: list[str], cnt: int,
    category_name: str, sponsored_filter: bool,
) -> int:
    """단일 search-result row 처리 — 탭 열기 → 스크래핑 → 저장 → 탭 닫기.

    원본 ``crawl_amazon`` 안 nested for-loop body (~280 줄) 를 분리. 각 item
    처리가 독립 함수가 되면서 예외 격리 + 단위 검증 가능.

    Args:
        item: search 결과 row WebElement (``role="listitem"``).
        idx: 현재 페이지 내 idx (디버깅 출력용).
        ASIN_list: 누적 ASIN 리스트 (이 호출에서 새 ASIN 추가됨, mutable).
        cnt: 현재 카테고리 누적 수집 count.
        category_name: 현재 카테고리명.
        sponsored_filter: True 면 sponsored item skip *should be*. 단 원본 동작
            은 ``pass`` 였어서 *계속 수집함* — 의도된 버그인지 불명, 그대로 보존.

    Returns:
        새로 갱신된 cnt (이 item 처리됐으면 +1, ASIN duplicate 면 그대로).

    Note:
        탭 정리 (실패 시에도 close) 책임. crawl_amazon 의 메인 흐름에서 탭이
        무한 누적되지 않도록.
    """
    print(f"index: {idx}")
    try:
        ASIN = item.get_attribute("data-asin")
        print(f"ASIN: {ASIN}")
        if ASIN in ASIN_list:
            print("ASIN PASSED")
            return cnt
        if sponsored_filter and is_sponsored(item):
            # 원본 동작 보존 — `pass` 였어서 sponsored 라도 *계속 수집됨*.
            # TODO(behavior): sponsored 시 `return cnt` 가 의도?
            pass

        cnt += 1
        ASIN_list.append(ASIN)

        # 새 탭에서 상세 페이지 열기.
        item_link = item.find_element(By.CSS_SELECTOR, "a.a-link-normal")
        item_url = item_link.get_attribute("href")
        time.sleep(0.4)
        driver.execute_script("window.open(arguments[0], '_blank');", item_url)
        driver.switch_to.window(driver.window_handles[-1])

        # 스크래핑.
        item_dict = _scrape_item_details(ASIN, category_name, cnt)
        if item_dict["_has_ratings"]:
            print(f"{category_name} 리뷰 크롤링")
            reviews_list = _scrape_item_reviews(ASIN, item_dict["title"])
        else:
            print("No ratings")
            # placeholder — items 테이블에 review FK 없어도 row 1개 유지.
            reviews_list = [{
                "review_num": ASIN + "__0",
                "ASIN": ASIN,
                "customer_id": "No customer",
                "customer_name": "No customer",
                "title": item_dict["title"],
                "date": "No date",
                "review_rating": "No review",
                "content": "No content",
            }]

        # 저장 + 탭 닫기.
        _save_single_item(item_dict, reviews_list)
        driver.close()
        driver.switch_to.window(driver.window_handles[1])
        return cnt

    except Exception as e:
        print(f"Error processing item {idx + 1}: {e}")
        # 탭 정리 — 실패 시에도 close 해서 무한 탭 누적 방지.
        try:
            driver.close()
            driver.switch_to.window(driver.window_handles[1])
        except Exception:
            pass
        return cnt


def crawl_amazon(keyword="skin+care", asin_skip=True, sponsored_filter=False):
    """
    Amazon 키워드 검색 → 브랜드 필터 → 카테고리 루프 → 아이템·리뷰 수집의
    메인 크롤링 함수.

    Args:
        keyword (str): Amazon 검색 키워드. 기본값 ``"skin+care"``.
            브랜드명(예: ``"I'm from"``)을 직접 넘겨도 됨.
        asin_skip (bool): True 이면 이미 MySQL ``items`` 테이블에 있는 ASIN을
            건너뜀 — 중복 수집 방지. False 이면 전부 재수집.
        sponsored_filter (bool): True 이면 Sponsored 아이템을 *수집 대상에서
            제외하려는 의도* — 단 현재 ``_process_one_item`` 의 sponsored 분기는
            원본 동작 보존으로 `pass` 인 상태. 의도된 동작인지 별도 검증 필요.

    Returns:
        None — 수집 결과는 MySQL에 직접 적재됨 (``load_items``, ``load_reviews``).

    Note:
        M3 리팩터로 옛 monolithic 398 줄 → 4 헬퍼 + 단축된 본체 ~80 줄.
        finally 블록으로 driver.quit 보장 (예외 발생 시에도).
    """
    open_amazon_keyword(keyword)
    amazon_login(ID, PW)
    brands = ["COSRX", "Beauty of Joseon", "Dr. Jart+", "PURITO", "I'm from"]
    brand_filter_refresh(brands[4])

    try:
        time.sleep(NEXT_PAGE_LOAD_SEC)
        select_best_sellers()
        time.sleep(1)

        # 크롤링 대상 카테고리 list. 사이드바 navigation indent-2 = sub-category 수준.
        # (Makeup / Skin Care / Hair Care / Personal Care 등)
        categories = wait.until(EC.presence_of_all_elements_located(
            (By.CSS_SELECTOR, ".a-spacing-micro.s-navigation-indent-2")
        ))

        for category in categories:
            try:
                link = category.find_element(By.TAG_NAME, "a")
                category_name = link.text
                driver.execute_script(
                    "window.open(arguments[0], '_blank');", link.get_attribute("href")
                )
                time.sleep(HEAVY_PAGE_LOAD_SEC)
                driver.switch_to.window(driver.window_handles[-1])

                # "Showing results from All Departments" 메시지 = 카테고리 필터링이
                # 실패했다는 의미 (Amazon UI 가 일부 카테고리에서 broad-match fallback).
                # → skip 후 다음 카테고리로.
                try:
                    time.sleep(0.5)
                    all_dept_message = driver.find_element(
                        By.CSS_SELECTOR,
                        "#search > div.s-desktop-width-max.s-desktop-content.s-opposite-dir.s-wide-grid-style.sg-row > div.sg-col-20-of-24.s-matching-dir.sg-col-16-of-20.sg-col.sg-col-8-of-12.sg-col-12-of-16 > div > span.rush-component.s-latency-cf-section > div.s-main-slot.s-result-list.s-search-results.sg-row > div:nth-child(1) > div > div > div > h2 > span",
                    )
                    if all_dept_message.text.strip() == "Showing results from All Departments":
                        print("Found 'Showing results from All Departments', closing the tab.")
                        driver.close()
                        driver.switch_to.window(driver.window_handles[0])
                        continue
                except Exception:
                    print("'Showing results from All Departments' 메시지 없음, 계속 진행합니다.")

                # 카테고리 페이지 paginate — cnt 1000 도달 또는 다음 페이지 없을 때까지.
                cnt = 0
                while cnt < 1000:
                    time.sleep(0.5)
                    time.sleep(random.uniform(*PAGE_LOAD_JITTER_RANGE))

                    ASIN_list = get_asin_from_sql() if asin_skip else []
                    items = driver.find_elements(By.CSS_SELECTOR, '[role="listitem"]')
                    print("\n", len(items), "\n")

                    for idx, item in enumerate(items):
                        cnt = _process_one_item(
                            item, idx, ASIN_list, cnt,
                            category_name, sponsored_filter,
                        )

                    if not click_next_item_page():
                        break

                # 카테고리 탭 닫고 메인 검색결과 탭으로 복귀.
                print("driver_close1")
                driver.close()
                driver.switch_to.window(driver.window_handles[0])
                time.sleep(HEAVY_PAGE_LOAD_SEC)
            except Exception as e:
                print(f"Error processing category {category_name}: {e}")

    except Exception as e:
        print(f"Error occurred: {e}")
    finally:
        driver.quit()




# 함수 실행



crawl_amazon("I'm from", asin_skip =  True, sponsored_filter= False)
send_msg("크롤링 완료!!!")


