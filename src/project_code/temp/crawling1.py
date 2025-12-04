from selenium import webdriver 
import random
import string
from selenium.webdriver.common.by import By
import time
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.proxy import Proxy, ProxyType




def setup_driver():
    options = Options()
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0"
    ]
    options.add_argument(f"user-agent={random.choice(user_agents)}")
    return webdriver.Chrome(options=options)



def generate_random_term(length=3):
    # 랜덤 알파벳 문자열 생성
    return ''.join(random.choices(string.ascii_letters, k=length))



    """
    쿠팡 랭킹순 : 쿠팡광고 서비스 구매한 제휴업체 판매상품은 상위 노출 됨.
    <label for="sorter-scoreDesc" class="item-name" data-srp-log="{&quot;group&quot;:&quot;FILTER&quot;, &quot;filterType&quot;:&quot;SORT_KEY&quot;, &quot;id&quot;:&quot;scoreDesc&quot;}">쿠팡 랭킹순</label>
    낮은 가격순
    <label for="sorter-salePriceAsc" class="item-name" data-srp-log="{&quot;group&quot;:&quot;FILTER&quot;, &quot;filterType&quot;:&quot;SORT_KEY&quot;, &quot;id&quot;:&quot;salePriceAsc&quot;}">낮은가격순</label>
    판매량순
    <label for="sorter-saleCountDesc" class="item-name" data-srp-log="{&quot;group&quot;:&quot;FILTER&quot;, &quot;filterType&quot;:&quot;SORT_KEY&quot;, &quot;id&quot;:&quot;saleCountDesc&quot;}">판매량순</label>
    
    """



    """
    아이템 72개씩 보기
    <div id="searchSortingList" class="search-customized-selectbox">
        <ul class="selectbox-options">
            <li class="">
                <input type="radio" id="listSize-36" name="listSize" value="36">
                    <label for="listSize-36" data-srp-log="{&quot;group&quot;:&quot;LISTSIZE&quot;, &quot;listSize&quot;:&quot;36&quot;}">
                        36개씩 보기</label>
                    </li><li class="">
                    <input type="radio" id="listSize-48" name="listSize" value="48">
                    <label for="listSize-48" data-srp-log="{&quot;group&quot;:&quot;LISTSIZE&quot;, &quot;listSize&quot;:&quot;48&quot;}">
                    48개씩 보기</label>
                    </li><li class=""><input type="radio" id="listSize-60" name="listSize" value="60">
                    <label for="listSize-60" data-srp-log="{&quot;group&quot;:&quot;LISTSIZE&quot;, &quot;listSize&quot;:&quot;60&quot;}">60개씩 보기</label>
                    </li><li class="selected">
                    <input type="radio" id="listSize-72" name="listSize" value="72" checked="checked">
                    <label for="listSize-72" data-srp-log="{&quot;group&quot;:&quot;LISTSIZE&quot;, &quot;listSize&quot;:&quot;72&quot;}">
                    72개씩 보기</label></li></ul></div>
    """

def data_get(item: str):
    driver = setup_driver()
    driver.implicitly_wait(5)

    random_term = generate_random_term()
    search_query = f"{item} {random_term}"
    print(f"Searching for: {search_query}")
    
    driver.get(f"https://www.coupang.com/np/search?q={search_query}")
    time.sleep(random.uniform(2, 5))

    results = driver. find_elements(By.CLASS_NAME, "descriptions-inner")
    for rank, r in enumerate(results,1) :
        if rank > 10 :
            break
        try :
            name = r.find_element (By.CLASS_NAME, "name")
            price = r.find_element (By.CLASS_NAME, "price")
            print(f" {rank}위 {name.text} {price.text}")
            lb.insert(tk.END, f" {rank}위 {name.text} {price.text}")
        except :
            print("skip")


    driver.quit()

data_get("laptop")


from selenium.webdriver.common.proxy import Proxy, ProxyType

def setup_driver_with_proxy():
    proxy = Proxy()
    proxy.proxy_type = ProxyType.MANUAL
    proxy.http_proxy = "your_proxy:port"
    proxy.ssl_proxy = "your_proxy:port"

    capabilities = webdriver.DesiredCapabilities.CHROME
    proxy.add_to_capabilities(capabilities)
    
    options = Options()
    driver = webdriver.Chrome(desired_capabilities=capabilities, options=options)
    return driver
