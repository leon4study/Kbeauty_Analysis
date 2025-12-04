from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import Select
from mysql1 import MySqlClient
from reviews import load_reviews
from items import load_items
import os, json, time
import pandas as pd
import random
from dotenv import load_dotenv
from bs4 import BeautifulSoup
load_dotenv()

# 아마존 크롤링 함수

driver = webdriver.Chrome()
wait = WebDriverWait(driver, 4)

makeup= f"https://www.amazon.com/s?k=k-beauty&i=beauty&rh=n%3A3760911%2Cn%3A11058281&s=exact-aware-popularity-rank&dc&ds=v1%3AvPiGbavgDFIyPyjYujQrFyTUdwlvSHtmji89fdD8MDk&crid=211V8ZUP739J0&qid=1736829016&rnid=3760911&sprefix=%2Cbeauty%2C277&ref=sr_nr_n_1"
skin_care_products = f"https://www.amazon.com/s?k=k-beauty&i=beauty&rh=n%3A3760911%2Cn%3A11060451&s=exact-aware-popularity-rank&dc&ds=v1%3AE2wkD1ErgjZLUVbnPFvTiM%2FAqPTSq5bBJsnVDFteHyY&crid=211V8ZUP739J0&qid=1736828868&rnid=3760911&sprefix=%2Cbeauty%2C277&ref=sr_nr_n_2"
hair_care_products = f"https://www.amazon.com/s?k=k-beauty&i=beauty&rh=n%3A3760911%2Cn%3A11057241&s=exact-aware-popularity-rank&dc&ds=v1%3ALHjK%2F0MQ%2FJxHOUMf1%2Fdu8MTzC7YxlYkookAlVYCDjH4&crid=211V8ZUP739J0&qid=1736828920&rnid=3760911&sprefix=%2Cbeauty%2C277&ref=sr_nr_n_3"
perfumes_Fragrances = f"https://www.amazon.com/s?k=k-beauty&i=beauty&rh=n%3A3760911%2Cn%3A11056591&s=exact-aware-popularity-rank&dc&ds=v1%3Axt%2Fx7smHW0dCWlDxFqvF%2B0%2BBw9EVrYvMdZmwoG3umJo&crid=211V8ZUP739J0&qid=1736828952&rnid=3760911&sprefix=%2Cbeauty%2C277&ref=sr_nr_n_4"
FootHand_Nail_Care_Products = f"https://www.amazon.com/s?k=k-beauty&i=beauty&rh=n%3A3760911%2Cn%3A17242866011&s=exact-aware-popularity-rank&dc&ds=v1%3Atz8Q%2BcU6Q%2BQ4AyzrbA2R4yZ1Ocyq5HesJtk%2BOOHdqnk&crid=211V8ZUP739J0&qid=1736829047&rnid=3760911&sprefix=%2Cbeauty%2C277&ref=sr_nr_n_5"
BeautyTools_Accessories = f"https://www.amazon.com/s?k=k-beauty&i=beauty&rh=n%3A3760911%2Cn%3A17242866011&s=exact-aware-popularity-rank&dc&ds=v1%3Atz8Q%2BcU6Q%2BQ4AyzrbA2R4yZ1Ocyq5HesJtk%2BOOHdqnk&crid=211V8ZUP739J0&qid=1736829047&rnid=3760911&sprefix=%2Cbeauty%2C277&ref=sr_nr_n_6"
Shaving_HairRemoval_Products = f"https://www.amazon.com/s?k=k-beauty&i=beauty&rh=n%3A3760911%2Cn%3A17242866011&s=exact-aware-popularity-rank&dc&ds=v1%3Atz8Q%2BcU6Q%2BQ4AyzrbA2R4yZ1Ocyq5HesJtk%2BOOHdqnk&crid=211V8ZUP739J0&qid=1736829047&rnid=3760911&sprefix=%2Cbeauty%2C277&ref=sr_nr_n_7"
Personal_Care_Products = f"https://www.amazon.com/s?k=k-beauty&i=beauty&rh=n%3A3760911%2Cn%3A17242866011&s=exact-aware-popularity-rank&dc&ds=v1%3Atz8Q%2BcU6Q%2BQ4AyzrbA2R4yZ1Ocyq5HesJtk%2BOOHdqnk&crid=211V8ZUP739J0&qid=1736829047&rnid=3760911&sprefix=%2Cbeauty%2C277&ref=sr_nr_n_8"
Salon_SpaEquipment = f"https://www.amazon.com/s?k=k-beauty&i=beauty&rh=n%3A3760911%2Cn%3A15144566011&s=exact-aware-popularity-rank&dc&ds=v1%3Af34O4VqqjIRQvabsv%2F6BGhU%2FLlFijWzSc5qa%2B%2FspLy8&crid=211V8ZUP739J0&qid=1736829124&rnid=3760911&sprefix=%2Cbeauty%2C277&ref=sr_nr_n_9"


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


def amazon_login(id : str ,pw : str):
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


def set_sort_by_most_recent_with_scroll(driver, wait):
    """
    스크롤을 내려 'Sort by' 드롭다운에서 'Most recent' 옵션을 선택하는 함수.
    
    Args:
        driver: Selenium WebDriver 객체.
        wait: WebDriverWait 객체.
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
    wait_time = random.uniform(0.1, 0.2)
    time.sleep(wait_time)
    try:
        next_page_button = driver.find_element(By.CSS_SELECTOR, 'a.s-pagination-button')
        next_page_button.click()
        time.sleep(0.4)
        print("Successfully clicked the Next Item Page button.")
    except Exception as e:
        print(f"Error clicking Next Page button: {e}")



def click_next_item_page2():
    # 랜덤 대기 시간 추가
    wait_time = random.uniform(0.1, 0.2)
    time.sleep(wait_time)
    
    try:
        # 'Next' 버튼이 클릭 가능할 때까지 대기
        next_page_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'a.s-pagination-button'))
        )
        next_page_button.click()
        print("Successfully clicked the Next Item Page button.")
    except TimeoutException:
        print("Error: Next Page button is not clickable or not found within the timeout.")
    except NoSuchElementException:
        print("Error: Next Page button is not found on the page.")
    except Exception as e:
        print(f"Unexpected error occurred while clicking Next Page button: {e}")



def click_next_review_page(driver, wait):
    try:
        # Next page 버튼 기다리기
        next_page_button = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".a-pagination .a-last a"))
        )
        # 버튼 클릭
        next_page_button.click()
        print("Successfully clicked the Next Review Page button.")
    except Exception as e:
        print(f"Error clicking Next Page button: {e}")




def click_next_review_page2():
    try:
        # "Next page" 버튼의 요소를 찾기
        next_page_button = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "ul.a-pagination li.a-last"))
        )

        next_page_button1 = driver.find_element(By.CSS_SELECTOR, "ul.a-pagination li.a-last")
        
        # 비활성화 상태 확인
        if "a-disabled" in next_page_button1.get_attribute("class"):
            print("Next page button is disabled. No more pages.")
            return False  # 반복문 종료를 위한 False 반환
        
        # 버튼 활성화 상태일 경우 클릭
        next_page_button.click()
        return True  # 다음 페이지로 이동
        
    except Exception as e:
        print("Next page button not found.")
        return False  # 반복문 종료를 위한 False 반환




def click_next_review_page3():
    try:
        # "Next page" 버튼이 DOM에 나타날 때까지 대기
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "ul.a-pagination li.a-last")))

        # 요소 가져오기
        next_page_button = driver.find_element(By.CSS_SELECTOR, "ul.a-pagination li.a-last")

        # 비활성화 상태 확인
        if "a-disabled" in next_page_button.get_attribute("class"):
            print("Next page button is disabled. No more pages.")
            return False  # 반복문 종료를 위한 False 반환

        # 버튼이 활성화된 경우 클릭 가능할 때까지 대기
        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "ul.a-pagination li.a-last")))

        # 버튼 클릭
        next_page_button.find_element(By.TAG_NAME, "a").click()
        return True  # 다음 페이지로 이동

    except Exception as e:
        print(f"Error occurred in click_next_review_page3 : {e}")
        return False  # 반복문 종료를 위한 False 반환




def click_next_review_page4():
    try:
        time.sleep(0.3)
        # "Next page" 버튼의 요소를 찾기
        next_page_button = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "ul.a-pagination li.a-last"))
        )
        
        time.sleep(0.3)
        # 비활성화 상태 확인
        if "a-disabled" in next_page_button.get_attribute("class"):
            print("Next page button is disabled. No more pages.")
            return False  # 반복문 종료를 위한 False 반환
        
        # 버튼 클릭
        next_page_button.click()

        return True  # 다음 페이지로 이동
    except Exception as e:
        print(f"Error: {e}")
        return False  # 반복문 종료를 위한 False 반환


def score_filter():
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



def get_asin_from_sql():
    asin_list =[]
    try :
        query = "SELECT ASIN FROM items"  # items 테이블에서 모든 데이터를 조회
        df = my_sql_client.fetch_as_dataframe(query)
        asin_list = df['ASIN'].to_list()
    except Exception as e:
        print(f"error occurred from get_asin_from_sql {e}")
    finally : return asin_list


def select_best_sellers_with_click():
    """
    Selenium의 클릭 동작을 사용해 Amazon의 드롭다운 메뉴에서 'Best Sellers' 옵션을 선택.
    """
    try:
        # 드롭다운 메뉴 클릭
        dropdown_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "s-result-sort-select"))
        )
        dropdown_button.click()

        # "Best Sellers" 옵션 클릭
        best_sellers_option = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "option[value='exact-aware-popularity-rank']"))
        )
        best_sellers_option.click()

        # 새 페이지 로드를 기다림
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.s-main-slot"))
        )
        print("Successfully selected 'Best Sellers' using clicks.")
    except Exception as e:
        print(f"An error occurred: {e}")



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

def approaching_item(ASIN_list):

    ASIN_list = ASIN_list
    print(ASIN_list[:4])
    cnt = 0
    while cnt < 1000:
        time.sleep(0.7)
        wait_time = random.uniform(0.05, 0.15)
        time.sleep(wait_time)
        
        # 광고 아닌 item 리스트만 가져오기
        parent_selector = 'div.s-main-slot.s-result-list.s-search-results.sg-row'
        child_selector = '[role="listitem"]'
        selector = f"{parent_selector} > {child_selector}"
        items = driver.find_elements(By.CSS_SELECTOR, selector)

        print("\n", len(items), "\n")
        item_list = []
        opened = True

        # 각 아이템 클릭 및 상세 정보 크롤링
        for idx, item in enumerate(items):
            try:
                ASIN = item.get_attribute("data-asin")
                print("ASIN : ", ASIN)
                if ASIN in ASIN_list:
                    print("continued")
                    continue  # 이미 처리된 ASIN은 건너뜀

                try:
                    if item.find_elements(By.CLASS_NAME, "puis-sponsored-label-text"):  # Sponsored 라벨 존재 확인
                        continue  # Sponsored 항목은 건너뜀
                except Exception as e:
                    print(f"Sponsored 라벨 확인 중 에러 발생: {e}")
                    # 에러가 발생하면 Sponsored 여부를 무시하고 다음 로직 실행

                cnt += 1
                ASIN_list.append(ASIN)

                # 새 탭에서 열기 위해 Shift + Click
                item_link = item.find_element(By.CSS_SELECTOR, 'a.a-link-normal')
                item_url = item_link.get_attribute("href")
                print(item_url)
                
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
                reviews = driver.find_element(By.ID, "acrCustomerReviewText").text if len(driver.find_elements(By.ID, "acrCustomerReviewText")) > 0 else "No reviews"
                brand = driver.find_element(By.CSS_SELECTOR, "tr.po-brand .po-break-word").text  if len(driver.find_elements(By.CSS_SELECTOR, "tr.po-brand .po-break-word")) > 0 else "No brand"
                special_feature = driver.find_element(By.CSS_SELECTOR, "tr.po-special_feature .po-break-word").text if len(driver.find_elements(By.CSS_SELECTOR, "tr.po-special_feature .po-break-word")) > 0 else "No special feature"
                price = driver.find_element(By.CLASS_NAME, "a-price-whole").text + "." + driver.find_element(By.CLASS_NAME, "a-price-fraction").text
                total_star = driver.find_element(By.CSS_SELECTOR, ".a-popover-trigger .a-size-small.a-color-base").text if len(driver.find_elements(By.CSS_SELECTOR, ".a-popover-trigger .a-size-small.a-color-base")) > 0 else "No rating"
                
                # total_review counts
                totaL_review_counts = driver.find_element(By.CSS_SELECTOR, "#acrCustomerReviewText").text
                global_rating_count = int(totaL_review_counts.strip("()").replace(",", ""))
                
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
                                    "ASIN" : ASIN, 
                                    "title" : title,
                                    "brand" : brand, 
                                    "price" : price,
                                    "global_rating_count" : global_rating_count,
                                    "Special_Feature" : special_feature,
                                    "total_star_mean" : total_star,
                                    "detail_dict" : detail_dict,
                                    "best_sellers_rank_Feature" : best_sellers_rank_text
                                    })

                # 리뷰 있으면 리뷰 정보 가져오기
                if reviews != "No reviews":

                    print('리뷰 크롤링')
                    see_more_reviews_link = wait.until( EC.presence_of_element_located((By.CSS_SELECTOR, "a[data-hook='see-all-reviews-link-foot']")))
                    actions = ActionChains(driver)                    
                    actions.move_to_element(see_more_reviews_link).perform()  # 링크로 스크롤 이동
                    print("스크롤 이동")

                    # 약간의 추가 대기 후 클릭 (화면이 스크롤될 시간이 필요할 수 있음)
                    see_more_reviews_link.click()
                    print("링크 클릭")
                    
                    set_sort_by_most_recent_with_scroll(driver, wait)
                    print("스크롤 실행 완료")

                    try:
                        # 리뷰 데이터를 저장할 리스트
                        reviews_list = []
                        # 리뷰 요소를 모두 가져옵니다
                        review_count = 0  # 수집한 리뷰 개수를 관리하는 변수
                        max_reviews = 50  # 최대 수집 리뷰 수

                        while review_count < max_reviews:
                            #wait_time = random.uniform(0.02, 0.08)
                            driver.implicitly_wait(7)
                            detail_reviews = driver.find_elements(By.CSS_SELECTOR, 'div[class="a-section celwidget"]')

                            for detail_review in detail_reviews:  # 현재 페이지에서 모든 리뷰를 처리
                                if review_count >= max_reviews:  # 최대 리뷰 수에 도달하면 종료
                                    break
                                try:
                                    date = detail_review.find_element(By.CSS_SELECTOR, "span[data-hook='review-date']").text if len(detail_review.find_elements(By.CSS_SELECTOR, "span[data-hook='review-date']")) > 0 else "No date"
                                    review_title = detail_review.find_element(By.CLASS_NAME, "review-title").text if len(detail_review.find_elements(By.CLASS_NAME, "review-title")) > 0 else "No title"
                                    review_rating_element =  detail_review.find_element(By.CSS_SELECTOR, "span.a-icon-alt")
                                    review_rating = driver.execute_script("return arguments[0].innerText;", review_rating_element)
                                    content = detail_review.find_element(By.CSS_SELECTOR, "span[data-hook='review-body']").text if len(detail_review.find_elements(By.CSS_SELECTOR, "span[data-hook='review-body']")) > 0 else "No content"

                                    print(f"  Review {review_count + 1}")
                                    print(f"  Title: {review_title}")
                                    print("-" * 50)

                                    reviews_list.append({
                                                            "review_num" : ASIN+"__"+str(review_count),
                                                            "ASIN" : ASIN,"title" : title,
                                                            "date" : date, "review_rating" : review_rating,
                                                            "content" : content
                                    })

                                    review_count += 1  # 수집한 리뷰 개수 증가
                                except Exception as e:
                                    print(f"Error extracting review {review_count + 1}: {e}")
                                    continue

                            try:
                                if review_count >= max_reviews:  # 최대 리뷰 수에 도달하면 종료
                                    break
                                if not click_next_review_page4():
                                    break  # click_next_review_page()가 False를 반환하면 반복문 종료
                            except Exception as e:
                                print(f"error: {e}")
                                break  # 더 이상 페이지가 없거나 오류가 발생하면 종료

                    except Exception as e:
                        print(f"Error retrieving reviews: {e}")
                    
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

                    # DataFrame 변환

                    # detail_dict 열을 JSON 문자열로 변환
                    item_df["detail_dict"] = item_df["detail_dict"].apply(json.dumps)

                    # price 및 total_star_mean을 숫자형으로 변환
                    item_df["price"] = pd.to_numeric(item_df["price"], errors="coerce")
                    item_df["total_star_mean"] = pd.to_numeric(item_df["total_star_mean"], errors="coerce")

                    # MySQL에 item_df 로드
                    
                    load_items(df=item_df, my_sql_client=my_sql_client , method= "insert")
                    review_df = pd.json_normalize(reviews_list)
                    print()
                    print(review_df.columns)

                    load_reviews(df = review_df, my_sql_client = my_sql_client,method= "insert")
            
                    print("=" * 50)

            except Exception as e:
                print(f"Error processing item {idx + 1}: {e}")
                continue
            finally :
                if opened:
                    # 새 탭 닫기
                    driver.close()
                    driver.switch_to.window(driver.window_handles[0])  # 원래 탭으로 돌아가기
                    opened = False
        time.sleep(0.5)
        click_next_item_page2()
        

def search_amazon(keyword):
    try:
        # 아마존 검색 페이지 열기
        driver.get(f"https://www.amazon.com")
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
        print(f"Error occurred in search_amazon: {e}")
    finally:
        driver.quit()


def main():
    search_amazon("K-beauty")
    amazon_login(ID,PW)
    select_best_sellers()
    ASIN_list = get_asin_from_sql()
    approaching_item(ASIN_list)


# 함수 실행
if __name__ == "__main__":
    main()
