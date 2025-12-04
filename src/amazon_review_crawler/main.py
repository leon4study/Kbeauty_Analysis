from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import Select
from mysql1 import MySqlClient
from reviews import load_reviews
from items import load_items
from slack1 import send_msg
import os
import json
import time
import pandas as pd
import random
from dotenv import load_dotenv
load_dotenv()

# 아마존 크롤링 함수

driver = webdriver.Chrome()
wait = WebDriverWait(driver, 3)


ID = os.environ.get('ID') 
PW = os.environ.get('PW')
DB_SERVER_HOST = os.environ.get("DB_SERVER_HOST")
DB_USERNAME = os.environ.get("DB_USERNAME")
DB_PASSWORD = os.environ.get("DB_PASSWORD")
DB_DATABASE = os.environ.get("DB_DATABASE")
DB_PORT = os.environ.get("DB_PORT")


my_sql_client = MySqlClient(
    server_name=DB_SERVER_HOST,
    database_name=DB_DATABASE,
    username=DB_USERNAME,
    password=DB_PASSWORD,
    port=DB_PORT
)

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
    wait_time = random.uniform(0.05, 0.15)
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
        time.sleep(0.2)
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
        wait_time = random.uniform(0.05, 0.15)
        time.sleep(wait_time)

        wait_time = random.uniform(0.05, 0.15)
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
    try:
        # 요소가 로드될 때까지 기다림
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#p_123\\/452045 > span > a > span")))

        # JavaScript를 사용해 해당 요소를 찾음
        element = driver.execute_script(
            "return document.querySelector('#p_123\\\\/452045 > span > a > span');"
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
    


def brand_filter_refresh(brand:str): #brands 필터. 체크하면 해당 브랜드만 나옴. (단 체크하려면 해당 브랜드 체크박스 알아야 함.)
    brands = ["COSRX","Beauty of Joseon","Dr. Jart+","PURITO","I'm from"]
    try:
        if brand == brands[0]:
            element_locator = (By.CSS_SELECTOR, "#p_123\\/241477 > span > a > span")  # cosRX
        elif brand == brands[1]:
            element_locator = (By.CSS_SELECTOR, "#p_123\\/591445 > span > a > span")
        elif brand == brands[2]:
            element_locator = (By.CSS_SELECTOR, "#p_123\\/452045 > span > a > span")
        elif brand == brands[3]:
            element_locator = (By.CSS_SELECTOR, "#p_123\\/312482 > span > a > span")
        elif brand == brands[4]:
            element_locator = (By.CSS_SELECTOR, "#p_123\\/654399 > span > a > span")
    
            
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
                time.sleep(0.2)  # 페이지 로드 안정성을 위해 짧은 대기
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
    try:
        if item.find_elements(By.CLASS_NAME, "puis-sponsored-label-text"):  # Sponsored 라벨 존재 확인
            ("Sponsored_passed")
            return True  # Sponsored 항목은 건너뜀
    except Exception as e:
        print(f"Sponsored 라벨 확인 중 에러 발생: {e}")
        # 에러가 발생하면 Sponsored 여부를 무시하고 다음 로직 실행
    return False

def click_BeautyPersonalCareDepartment():
    # Beauty & Personal Care Department 선택 (클릭))
    category_Department = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#n\\/3760911')))
    # 요소를 클릭하거나 원하는 작업 수행
    category_Department.click()

def crawl_amazon(keyword="skin+care", asin_skip = True , sponsored_filter = False):

    open_amazon_keyword(keyword)
    amazon_login(ID, PW)
    brands = ["COSRX","Beauty of Joseon","Dr. Jart+","PURITO","I'm from"]
    brand_filter_refresh(brands[4])
    

    try:
        time.sleep(1.5)
        select_best_sellers()
        time.sleep(1)

        # 크롤링할 요소 선택 (CSS Selector 사용)
        # Makeup
        #Skin Care Products
        #Hair Care Products
        #Perfumes & Fragrances
        #Foot, Hand & Nail Care Products
        #Beauty Tools & Accessories
        #Shaving & Hair Removal Products
        #Personal Care Products
        #Salon & Spa Equipment 
        categories = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.a-spacing-micro.s-navigation-indent-2')))

        # 각 카테고리 페이지 방문 및 크롤링
        for category in categories:
            try:
                # 링크 클릭
                link = category.find_element(By.TAG_NAME, 'a')  # 내부 'a' 태그 찾기
                category_name = link.text  # 카테고리 이름 저장
                
                # 새 창 열기
                driver.execute_script("window.open(arguments[0], '_blank');", link.get_attribute("href"))
                time.sleep(2)  # 페이지 로딩 대기

                # 새 창으로 전환
                driver.switch_to.window(driver.window_handles[-1])

                # "Showing results from All Departments" 메시지 확인 및 창 닫기 로직
                try:
                    time.sleep(0.5)
                    all_dept_message = driver.find_element(
                        By.CSS_SELECTOR,
                        '#search > div.s-desktop-width-max.s-desktop-content.s-opposite-dir.s-wide-grid-style.sg-row > div.sg-col-20-of-24.s-matching-dir.sg-col-16-of-20.sg-col.sg-col-8-of-12.sg-col-12-of-16 > div > span.rush-component.s-latency-cf-section > div.s-main-slot.s-result-list.s-search-results.sg-row > div:nth-child(1) > div > div > div > h2 > span'
                    )
                    if all_dept_message.text.strip() == "Showing results from All Departments":
                        print("Found 'Showing results from All Departments', closing the tab.")
                        driver.close()
                        driver.switch_to.window(driver.window_handles[0])
                        continue
                except :
                    print("'Showing results from All Departments' 메시지 없음, 계속 진행합니다.")


                # ===================================================
                cnt = 0
                while cnt < 1000:
                    time.sleep(0.5)
                    wait_time = random.uniform(0.7,1)
                    time.sleep(wait_time)

                    if asin_skip:
                        ASIN_list = get_asin_from_sql()
                    else :
                        ASIN_list = []
                    
                    # 모든 리스트 아이템 가져오기
                    items = driver.find_elements(By.CSS_SELECTOR, '[role="listitem"]')
                    print("\n", len(items), "\n")
                    item_list = []
                    # 리뷰 데이터를 저장할 리스트
                    reviews_list = []
                    
                    # 각 아이템 클릭 및 상세 정보 크롤링
                    for idx, item in enumerate(items):
                        is_bundle = False
                        print(f"index: {idx}")
                        try:
                            ASIN = item.get_attribute("data-asin")
                            print(f"ASIN: {ASIN}")
                            if ASIN in ASIN_list:
                                print("ASIN PASSED")
                                continue  # 이미 처리된 ASIN은 건너뜀
                            else:
                                if sponsored_filter : # sponsored_filter 옵션 켰을 경우, sponsored item인 경우 pass
                                    if is_sponsored(item) :
                                        pass

                                cnt += 1
                                ASIN_list.append(ASIN)

                                # 새 탭에서 열기 위해 Shift + Click
                                item_link = item.find_element(By.CSS_SELECTOR, 'a.a-link-normal')
                                item_url = item_link.get_attribute("href")

                                time.sleep(0.4)
                                # 새 탭에서 상세 정보 열기
                                driver.execute_script("window.open(arguments[0], '_blank');", item_url)
                                driver.switch_to.window(driver.window_handles[-1])  # 새 탭으로 전환

                                # 상세 정보 크롤링
                                # 추가 제품 세부 정보
                                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "productTitle"))) 

                                detail_bullets = driver.find_element(By.ID, "detailBullets_feature_div")
                                product_details = detail_bullets.find_elements(By.CSS_SELECTOR, "li span.a-list-item")
                                detail_dict = {}
                                for detail in product_details:
                                    try:
                                        # ':' 기준으로 나누어 key와 value 추출
                                        key = detail.find_element(By.TAG_NAME, "span").text.split(":")[0].strip()
                                        value = detail.text.split(":")[1].strip()
                                        detail_dict[key] = value
                                    except Exception:
                                        continue

                                # 상품 제목
                                title = driver.find_element(By.ID, "productTitle").text
                                print(f"Title: {title}")
                                reviews = driver.find_element(By.ID, "acrCustomerReviewText").text if len(driver.find_elements(By.ID, "acrCustomerReviewText")) > 0 else "No ratings"
                                brand = driver.find_element(By.CSS_SELECTOR, "tr.po-brand .po-break-word").text if len(driver.find_elements(By.CSS_SELECTOR, "tr.po-brand .po-break-word")) > 0 else "No brand"

                                description = get_description() # 일반 아이템들은 이거 써야함
                                print(description[:5])

                                #description = cosrx_description_to_json()
                                special_feature = driver.find_element(By.CSS_SELECTOR, "tr.po-special_feature .po-break-word").text if len(driver.find_elements(By.CSS_SELECTOR, "tr.po-special_feature .po-break-word")) > 0 else "No special feature"                                    
                                
                                try:
                                    # a-price-whole과 a-price-fraction에서 각각 가격 찾기 (CSS Selector로 변경)
                                    #price_whole = driver.find_element(By.CSS_SELECTOR, "#corePrice_feature_div > div > div > div > div > span.a-price.a-text-normal.aok-align-center.reinventPriceAccordionT2 > span:nth-child(2) > span.a-price-whole").text
                                    #price_fraction = driver.find_element(By.CSS_SELECTOR, "#corePrice_feature_div > div > div > div > div > span.a-price.a-text-normal.aok-align-center.reinventPriceAccordionT2 > span:nth-child(2) > span.a-price-fraction").text
                                    price_whole = driver.find_element(By.CSS_SELECTOR,"#corePrice_feature_div span.a-price span.a-price-whole").text
                                    price_fraction = driver.find_element(By.CSS_SELECTOR,"#corePrice_feature_div span.a-price span.a-price-fraction").text
                                    
                                    price = price_whole + "." + price_fraction
                                    print(price,"1")
                                except:
                                    # 번들 가격일 가능성 있음
                                    try : 
                                        price = driver.execute_script("""
                                            var priceElement = document.querySelector("#corePrice_desktop > div > table > tbody > tr:nth-child(2) > td.a-span12 > span.a-price.a-text-price.a-size-medium.apexPriceToPay > span:nth-child(2)");
                                            return priceElement ? priceElement.textContent : null;
                                        """)
                                        if price:
                                            is_bundle = True
                                            price = price.split("$")[1]
                                        else :
                                            is_bundle = False
                                    except : 
                                        price = None
                                        is_bundle = False

                                    # 결과 출력
                                    print("가격:", price)
                                    print("번들 여부:", is_bundle)
                                    
                                total_star = driver.find_element(By.CSS_SELECTOR, ".a-popover-trigger .a-size-small.a-color-base").text if len(driver.find_elements(By.CSS_SELECTOR, ".a-popover-trigger .a-size-small.a-color-base")) > 0 else "No star"
                                # total_star 설정
                                total_star = driver.find_element(By.CSS_SELECTOR, ".a-popover-trigger .a-size-small.a-color-base").text if len(driver.find_elements(By.CSS_SELECTOR, ".a-popover-trigger .a-size-small.a-color-base")) > 0 else "No star"
                                # total_rating_counts 설정
                                total_rating_counts = driver.find_element(By.CSS_SELECTOR, "#acrCustomerReviewText").text if len(driver.find_elements(By.CSS_SELECTOR, "#acrCustomerReviewText")) > 0 else "No rating"
                                # global_rating_count 설정
                                global_rating_count = total_rating_counts.strip("()").replace(",", "") if total_rating_counts != "No rating" else "No rating"
                                print(f"global_rating_count: {global_rating_count}")
                                # $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$                                
                                
                                try:
                                    # Ingredients 요소가 있는지 확인 후 텍스트 추출
                                    ingredients_elements = driver.find_elements(By.CSS_SELECTOR, "#important-information > div:nth-child(3) > p:nth-child(3)")
                                    if ingredients_elements:  # 요소가 존재하면 텍스트 추출
                                        ingredients_text = ingredients_elements[0].text.strip()
                                    else:  # 요소가 없으면 None으로 설정
                                        ingredients_text = None
                                except Exception as e:
                                    print(f"Error occurred while fetching Ingredients: {e}")
                                    ingredients_text = None  # 오류 발생 시에도 None으로 설정
                                    is_bundle = False


                                # 결과 출력 (디버깅용)
                                print(f"Ingredients: {ingredients_text}")

                                # Best Sellers Rank 정보 가져오기
                                best_sellers_elements = driver.find_elements(By.CSS_SELECTOR, "ul.detail-bullet-list > li > span.a-list-item")

                                best_sellers_rank_text = "No result"  # 기본값 설정
                                for element in best_sellers_elements:
                                    if "Best Sellers Rank" in element.text:
                                        try:
                                            # Best Sellers Rank가 포함된 텍스트에서 순위 추출
                                            best_sellers_rank_text = element.text.split(":")[1].strip()
                                            break  # 원하는 값을 찾으면 루프 종료
                                        except Exception:
                                            best_sellers_rank_text = "No result"
                                            break

                                print()
                                print(f"index: {idx}")
                                print(f"ASIN: {ASIN}")
                                print(f"Title: {title}")
                                print(f"global_rating_count: {global_rating_count}")
                                print(f"price: {price}")
                                print()

                                item_list.append({
                                    "ASIN": ASIN, "title": title,
                                    "order": cnt,
                                    "category": category_name,
                                    "brand": brand, "price": price,
                                    "global_rating_count": global_rating_count,
                                    "description": description,
                                    "Special_Feature": special_feature,
                                    "total_star_mean": total_star,
                                    "detail_dict": detail_dict,
                                    "best_sellers_rank_Feature": best_sellers_rank_text,
                                    "Ingredients": ingredients_text,
                                    "is_bundle": is_bundle
                                })

                                # rating 이력 있으면 리뷰 정보 가져오기
                                if reviews == "No ratings":
                                    print("No ratings")
                                    reviews_list.append({
                                        "review_num": ASIN + "__" + str(review_count),
                                        "ASIN": ASIN,
                                        "customer_id": "No customer",
                                        "customer_name": "No customer",
                                        "title": title,
                                        "date": "No date",
                                        "review_rating": "No review",
                                        "content": "No content"
                                    })
                                else:
                                    print(f"{category_name} 리뷰 크롤링")
                                    try:
                                        #more_reviews_link = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "a[data-hook='see-all-reviews-link-foot']")))
                                        #actions = ActionChains(driver)
                                        #actions.move_to_element(more_reviews_link).perform()  # 링크로 스크롤 이동


                                        more_reviews_link = wait.until(
                                        EC.presence_of_element_located(
                                            (By.CSS_SELECTOR, "#reviews-medley-footer > div.a-row.a-spacing-medium > a[data-hook='see-all-reviews-link-foot']")
                                            )
                                        )

                                        print("스크롤 이동")

                                        # 약간의 추가 대기 후 클릭 (화면이 스크롤될 시간이 필요할 수 있음)
                                        time.sleep(0.5)
                                        more_reviews_link.click()
                                        print("링크 클릭")
                                        
                                        set_sort_by_most_recent_with_scroll()
                                        print("스크롤 실행 완료")
                                        # 리뷰 요소를 모두 가져옵니다
                                        review_count = 0  # 수집한 리뷰 개수를 관리하는 변수
                                        max_reviews = 20000  # 최대 수집 리뷰 수
                                        
                                        try:
                                            
                                            while review_count < max_reviews:
                                                wait_time = random.uniform(0.7, 1)
                                                time.sleep(wait_time)
                                                try:
                                                    detail_reviews = driver.find_elements(By.CSS_SELECTOR, 'div[class="a-section celwidget"]')
                                                except Exception as e:
                                                    print(f"뭔가 잘못됐네 단단히 : {e}")
                                                    break
                                                
                                                for detail_review in detail_reviews:
                                                    try:
                                                        time.sleep(0.03)
                                                        # 각 필드를 추출하기 전에 대기 추가
                                                        WebDriverWait(driver, 10).until(
                                                            EC.presence_of_element_located((By.CSS_SELECTOR, "span.a-profile-name"))
                                                        )
                                                        review_div_id = detail_review.get_attribute("id")
                                                        customer_id = review_div_id.split("-")[-1] if "customer_review" in review_div_id else "No customer ID"
                                                        customer_name = detail_review.find_element(By.CSS_SELECTOR, "span[class='a-profile-name']").text if len(detail_review.find_elements(By.CSS_SELECTOR, "span[class='a-profile-name']")) > 0 else "No Name"
                                                        date = detail_review.find_element(By.CSS_SELECTOR, "span[data-hook='review-date']").text if len(detail_review.find_elements(By.CSS_SELECTOR, "span[data-hook='review-date']")) > 0 else "No date"
                                                        review_title = detail_review.find_element(By.CLASS_NAME, "review-title").text if len(detail_review.find_elements(By.CLASS_NAME, "review-title")) > 0 else "No title"
                                                        review_rating_element = detail_review.find_elements(By.CSS_SELECTOR, "span.a-icon-alt")
                                                        review_rating = (
                                                            driver.execute_script("return arguments[0].innerText;", review_rating_element[0])
                                                            if len(review_rating_element) > 0
                                                            else "No review"
                                                        )
                                                        content = detail_review.find_element(By.CSS_SELECTOR, "span[data-hook='review-body']").text if len(detail_review.find_elements(By.CSS_SELECTOR, "span[data-hook='review-body']")) > 0 else "No content"
                                                        
                                                        # 디버깅 출력
                                                        print(f"Review {review_count} - customer_id: {customer_id}, customer_name: {customer_name}, review_title: {review_title}, review_rating: {review_rating}")
                                                        reviews_list.append({
                                                            "review_num": ASIN + "__" + str(review_count),
                                                            "ASIN": ASIN,
                                                            "customer_id": customer_id,
                                                            "customer_name": customer_name,
                                                            "title": title,
                                                            "date": date,
                                                            "review_rating": review_rating,
                                                            "content": content
                                                        })
                                                        review_count += 1  # 수집한 리뷰 개수 증가
                                                    except Exception as e:
                                                        print(f"Error extracting review {review_count + 1}: {e}")
                                                        continue
                                                if review_count >= max_reviews:  # 최대 리뷰 수에 도달하면 종료
                                                    break
                                                if not click_next_review_page():  # 다음 페이지로 이동 불가 시 종료
                                                    break
                                        except Exception as e:
                                            print(f"Error retrieving reviews: {e}")
                                    except Exception as e:
                                        print(f"see_more_reviews ERROR : {e}")
                                
                                # DataFrame 변환
                                item_df = pd.json_normalize(item_list)

                                # `detail_dict` 관련 컬럼 병합
                                detail_cols = [col for col in item_df.columns if col.startswith("detail_dict.")]
                                if detail_cols:
                                    # `detail_dict` 관련 데이터를 다시 병합
                                    item_df["detail_dict"] = item_df[detail_cols].apply(
                                        lambda row: {col.split(".")[1]: row[col] for col in detail_cols if pd.notnull(row[col])},
                                        axis=1,
                                    )
                                    # 변환 완료 후 detail_dict 관련 컬럼 제거
                                    item_df.drop(columns=detail_cols, inplace=True)
                                
                                # detail_dict 열을 JSON 문자열로 변환
                                item_df["detail_dict"] = item_df["detail_dict"].apply(json.dumps)
                                # price 및 total_star_mean을 숫자형으로 변환
                                item_df["price"] = pd.to_numeric(item_df["price"], errors="coerce")
                                item_df["total_star_mean"] = pd.to_numeric(item_df["total_star_mean"], errors="coerce")

                                # MySQL에 item_df 로드
                                load_items(df=item_df, my_sql_client=my_sql_client)

                                review_df = pd.json_normalize(reviews_list)
                                print()
                                print(review_df.columns)

                                load_reviews(df=review_df, my_sql_client=my_sql_client)
                                print("=" * 50)
                                # 새 탭 닫기
                                driver.close()
                                driver.switch_to.window(driver.window_handles[1])  # 원래 탭으로 돌아가기

                        except Exception as e:
                            print(f"Error processing item {idx + 1}: {e}")
                            driver.close()
                            driver.switch_to.window(driver.window_handles[1])  # 원래 탭으로 돌아가기
                            continue
                    
                    if not click_next_item_page():
                        break
                # ===================================================
                # 새 창을 닫고 원래 창으로 돌아가기
                print("driver_close1")
                driver.close()
                driver.switch_to.window(driver.window_handles[0])
                time.sleep(2)  # 페이지 로딩 대기

            except Exception as e:
                print(f"Error processing category {category_name}: {e}")

    except Exception as e:
        print(f"Error occurred: {e}")
    finally:
        driver.quit()


# 함수 실행



crawl_amazon("I'm from", asin_skip =  True, sponsored_filter= False)
send_msg("크롤링 완료!!!")


