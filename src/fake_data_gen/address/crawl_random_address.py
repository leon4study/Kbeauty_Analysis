"""postcodebase.com 에서 미국 50개 주의 랜덤 주소를 크롤링.

K-beauty 합성 customer 프로필 만들 때 인구 비율과 비슷하게 주소를 분포시키기
위해 사용. 한 주를 다 받으면 csv (``random_address_<주코드>.csv``) 로 저장하고
이전 주의 임시 csv는 삭제 — 마지막 주가 끝나면 누적 csv 한 개만 남는다.

설계 가정:
- 단일 머신 + 사람이 옆에서 모니터링 (캡차나 차단 시 수동 개입)
- 한 번 돌리면 모든 주 다 끝낼 것 — 중간 재시작 지원 X (필요해지면 추가)

env (`.env`):
- ``SLACK_WEBHOOK_URL`` — 진행/오류 알림용 (없으면 send_msg 호출 시 에러)

확장 힌트:
- 중단 후 재개: 저장된 csv에서 주별 진척도 읽고 미완성 주만 재크롤
- 캡차 자동 풀이: 2captcha 등 외부 서비스 연동
"""
from __future__ import annotations

import random
import time

import pandas as pd
import pyperclip
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from fake_data_gen.address.address_utils import addr_to_df, compute_state_quotas
from util import slack
from util.repo_paths import DATA


# 출력 디렉터리 — 우리 repo의 표준 데이터 위치 (`data/address/`).
ADDRESS_DIR = DATA / "address"

# postcodebase 의 페이지당 표시 주소 개수. 한 클립보드 복사 시 9개씩 들어옴.
ADDRESSES_PER_COPY = 9


def _click_copy_button(driver: webdriver.Chrome) -> None:
    """페이지의 "주소 복사" 버튼을 JS로 클릭 (selenium 기본 click이 막힐 때 우회).

    한 번 누르면 ``ADDRESSES_PER_COPY`` 개의 주소가 클립보드에 복사된다.
    """
    btn = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located(
            (By.XPATH, '//*[@id="random_anchor_page"]/div[2]/p/a')
        )
    )
    driver.execute_script("arguments[0].click();", btn)
    time.sleep(0.5)


def _click_regen_button(driver: webdriver.Chrome) -> None:
    """페이지의 "재생성" 버튼 클릭 → 다음 ``ADDRESSES_PER_COPY`` 개를 새로 받음."""
    btn = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located(
            (By.XPATH, '//*[@id="res_li"]/li[4]/button')
        )
    )
    driver.execute_script("arguments[0].click();", btn)
    time.sleep(0.5)


def crawl_state(driver: webdriver.Chrome, quota: int) -> pd.DataFrame:
    """현재 페이지에서 시작해 한 주에 대해 ``quota`` 개 이상 모일 때까지 반복 수집.

    클립보드 복사 → 파싱 → 누적 → 재생성 → 반복. 파서가 빈 결과를 돌려주면
    Slack 알림 + 사용자 입력 대기 (수동 회복 후 계속).

    Args:
        driver: 해당 주의 postcodebase 페이지에 진입한 webdriver.
        quota: 모을 최소 주소 개수. 한 번에 ``ADDRESSES_PER_COPY`` 씩 늘어남.

    Returns:
        해당 주의 누적 주소 DataFrame.
    """
    state_df = pd.DataFrame()
    count = 0
    while count < quota:
        time.sleep(random.uniform(0.8, 1.6))
        _click_copy_button(driver)
        copied_text = pyperclip.paste()
        chunk_df = addr_to_df(copied_text)
        # 파서가 빈 결과 → 페이지 구조 변경 가능성, 사람 개입 대기
        if chunk_df.empty:
            slack.send_msg("crawling address 중 오류 발생!")
            input("계속하려면 엔터 키를 누르세요...")
            continue
        state_df = pd.concat([state_df, chunk_df], ignore_index=True)
        _click_regen_button(driver)
        time.sleep(random.uniform(0.8, 1.6))
        count += ADDRESSES_PER_COPY
    return state_df


def main() -> pd.DataFrame:
    """엔드투엔드 크롤링 — 모든 주를 순회하며 누적 csv 저장.

    페이지 흐름:
        1. 첫 주 (AK) 는 메인 페이지에서 바로 크롤
        2. 나머지 주는 메인 페이지의 주별 링크를 새 탭에서 열어 크롤
        3. 각 주 끝나면 누적 csv 저장, 이전 주의 임시 csv 삭제

    Returns:
        모든 주의 주소를 합친 DataFrame.
    """
    quotas = compute_state_quotas(total_count=12797)
    ADDRESS_DIR.mkdir(parents=True, exist_ok=True)

    driver = webdriver.Chrome()
    driver.get("https://ak.postcodebase.com/ko/randomaddress")
    time.sleep(5)

    # 1) 첫 주 (AK) 크롤
    first_state, first_quota = quotas[0]
    accumulated = crawl_state(driver, first_quota)
    prev_csv = ADDRESS_DIR / f"random_address_{first_state}.csv"
    accumulated.to_csv(prev_csv, index=False)

    # 2) 나머지 주 — 메인 페이지의 주별 링크를 새 탭에서 처리
    state_links = driver.find_elements(
        By.XPATH,
        '//*[@id="block-system-main"]/div/div[2]/div[2]/div[2]/div/ul/li/a',
    )
    for idx, link in enumerate(state_links):
        state_code, quota = quotas[idx + 1]
        print(f"crawling {state_code} (quota={quota})")

        href = link.get_attribute("href")
        time.sleep(random.uniform(0.8, 1.6))
        driver.execute_script("window.open(arguments[0], '_blank');", href)
        driver.switch_to.window(driver.window_handles[-1])

        new_state_df = crawl_state(driver, quota)
        accumulated = pd.concat([accumulated, new_state_df], ignore_index=True)

        # 누적 csv 저장 + 이전 주의 임시 csv 삭제
        new_csv = ADDRESS_DIR / f"random_address_{state_code}.csv"
        accumulated.to_csv(new_csv, index=False)
        print(f"saved {new_csv}")
        if prev_csv.exists():
            prev_csv.unlink()
            print(f"deleted {prev_csv}")
        prev_csv = new_csv

        driver.close()
        driver.switch_to.window(driver.window_handles[0])

    slack.send_msg("crawling address 완료!")
    return accumulated


if __name__ == "__main__":
    main()