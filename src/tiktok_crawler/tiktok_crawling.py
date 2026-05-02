"""TikTok 영상 검색 결과 메타데이터 크롤러.

특정 키워드로 TikTok 검색 → 결과 영상 N개에서 좋아요/댓글/저장수/설명/
업로드 날짜/틱톡커 이름 수집 → CSV 저장.

설계 가정:
- 단일 머신, 수동 실행 (cron 자동화 X)
- 캡차/사람인증 창이 뜨면 사람이 수동으로 풀어야 함 (sleep으로 시간 확보)
- 한 번에 한 키워드씩 처리. 멀티 키워드는 외부 루프로

Env (`.env`):
- ``TIKTOK_EMAIL`` / ``TIKTOK_PASSWORD`` — 로그인 자격증명. 코드에 절대 박지 말 것.

확장 힌트:
- 캡차 자동 풀이: 2captcha 등 외부 서비스 연동
- 멀티 키워드 batch: ``main()`` 을 keyword 리스트 받게 확장
"""
from __future__ import annotations

import os
import random
import time
from pathlib import Path

import pandas as pd
from dotenv import find_dotenv, load_dotenv
from selenium import webdriver
from selenium.common.exceptions import (
    NoSuchElementException,
    StaleElementReferenceException,
    TimeoutException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from util.repo_paths import TIKTOK

load_dotenv(find_dotenv())


def setup_driver() -> webdriver.Chrome:
    """Chrome WebDriver 초기화 + 기본 implicit wait 설정 (5초).

    개별 액션은 ``WebDriverWait`` 로 별도 timeout 지정.
    """
    driver = webdriver.Chrome()
    driver.maximize_window()
    driver.implicitly_wait(5)
    return driver


def login_tiktok(driver: webdriver.Chrome, email: str, password: str) -> None:
    """TikTok에 이메일/비밀번호로 로그인.

    UI 흐름: 헤더 로그인 → "전화/이메일/아이디 사용" → "이메일로 로그인" →
    이메일/비밀번호 입력 → 로그인 클릭. 로그인 직후 페이지 안정화 + 캡차 가능성을
    고려해 15초 sleep.

    Args:
        driver: 활성화된 webdriver.
        email: TikTok 계정 이메일.
        password: 비밀번호.
    """
    driver.find_element(By.XPATH, '//*[@id="header-login-button"]/div').click()
    driver.find_element(By.XPATH, '//*[@id="loginContainer"]/div/div/div/div[2]/div[2]').click()
    driver.find_element(By.XPATH, '//*[@id="loginContainer"]/div/form/div[1]/a').click()
    driver.find_element(
        By.XPATH, '//*[@id="loginContainer"]/div[2]/form/div[1]/input'
    ).send_keys(email)
    driver.find_element(
        By.XPATH, '//*[@id="loginContainer"]/div[2]/form/div[2]/div/input'
    ).send_keys(password)
    driver.find_element(By.XPATH, '//*[@id="loginContainer"]/div[2]/form/button').click()

    # 로그인 후 페이지 안정화 + 캡차 인증 시간 확보
    time.sleep(15)


def search_videos(driver: webdriver.Chrome, keyword: str) -> None:
    """검색어로 TikTok 검색 → 동영상 탭 전환 → 첫 영상 진입.

    검색 → "동영상" 탭 클릭 → 첫 영상 클릭 순. 사람인 인증 캡차가 뜰 수 있어
    ``implicitly_wait(30)`` 으로 사람이 수동 처리할 시간을 확보.

    Args:
        driver: 로그인된 webdriver.
        keyword: 검색어.
    """
    wait = WebDriverWait(driver, 30)

    # 검색 아이콘
    wait.until(EC.element_to_be_clickable(
        (By.XPATH, '//*[@id="app"]/div[2]/div[1]/div/div[2]/div[2]/button/div/div[2]')
    )).click()

    # 검색어 입력 + 엔터
    search = driver.find_element(
        By.XPATH, '//*[@id="app"]/div[2]/div[1]/div/div[5]/div[1]/div[2]/form/input'
    )
    search.send_keys(keyword)
    search.send_keys(Keys.ENTER)

    # 동영상 탭
    driver.find_element(By.XPATH, '//*[@id="tabs-0-tab-search_video"]').click()

    # 사람 인증 캡차 등장 시 수동 풀이 시간 확보
    driver.implicitly_wait(30)
    time.sleep(random.uniform(0.5, 1.5))

    # 검색 결과 첫 영상 클릭
    WebDriverWait(driver, 7).until(EC.element_to_be_clickable(
        (By.XPATH, '//*[@id="tabs-0-panel-search_video"]/div/div/div[1]/div[1]')
    )).click()


def collect_video_metadata(
    driver: webdriver.Chrome, n_videos: int = 250
) -> dict[str, list]:
    """현재 영상에서 시작해 N개 영상의 메타데이터 수집.

    각 영상에서 좋아요/댓글/저장수, 틱톡커 이름, 업로드 날짜, 설명 추출.
    수집 후 키보드 ``ARROW_DOWN`` 으로 다음 영상 이동.

    Args:
        driver: 영상 상세 페이지에 진입한 webdriver.
        n_videos: 수집할 영상 개수.

    Returns:
        DataFrame 만들기 직전 형태의 dict — 컬럼:
        ``like, comment, save, tiktoker_name, date, info``.
    """
    data: dict[str, list] = {
        "like": [],
        "comment": [],
        "save": [],
        "tiktoker_name": [],
        "date": [],
        "info": [],
    }

    for i in range(n_videos):
        # '자세히' 버튼 (영상 설명 펼치기) — 없을 수 있어서 try/except
        try:
            expand = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CLASS_NAME, "css-1r94cis-ButtonExpand"))
            )
            expand.click()
            print(f"{i}번: 자세히 버튼 클릭 성공")
        except Exception:
            print(f"{i}번: 자세히 버튼 없음/클릭 불가")

        # 영상 설명 (없으면 빈 문자열)
        try:
            info_text = driver.find_element(
                By.CSS_SELECTOR, 'h1[data-e2e="browse-video-desc"]'
            ).text
        except NoSuchElementException:
            info_text = ""
        data["info"].append(info_text)

        driver.implicitly_wait(5)

        # 업로드 날짜 — "조회수 · 2024-3-21" 형식, "·" 뒤만 사용
        try:
            date_elem = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, ".css-gg0x0w-SpanOtherInfos.evv7pft3")
                )
            )
            data["date"].append(date_elem.text.split("·")[1].strip())
        except (StaleElementReferenceException, TimeoutException):
            print(f"{i}번: 업로드 날짜 추출 실패")
            data["date"].append("")

        # 틱톡커 이름
        name_text = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, 'span[data-e2e="browse-username"]')
            )
        ).text
        data["tiktoker_name"].append(name_text)

        # 좋아요 — 같은 셀렉터가 페이지에 여러 개라 첫 번째만 사용
        likes = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, 'strong[data-e2e="browse-like-count"]')
            )
        )
        data["like"].append(likes[0].text)

        # 댓글
        data["comment"].append(
            WebDriverWait(driver, 10)
            .until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, 'strong[data-e2e="browse-comment-count"]')
                )
            )
            .text
        )

        # 저장
        data["save"].append(
            WebDriverWait(driver, 10)
            .until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, 'strong[data-e2e="undefined-count"]')
                )
            )
            .text
        )

        # 페이지 안정화 + 다음 영상으로 이동
        time.sleep(random.uniform(0.5, 1.5))
        driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ARROW_DOWN)

    return data


def save_to_csv(data: dict, output_path: Path) -> pd.DataFrame:
    """수집 결과 dict를 CSV로 저장 + DataFrame 반환.

    한글 깨짐 방지로 ``utf-8-sig`` 인코딩 사용 (Excel에서도 깨끗하게 열림).

    Args:
        data: ``collect_video_metadata()`` 반환 dict.
        output_path: 저장할 CSV 경로.
    """
    df = pd.DataFrame(data)
    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    return df


def main(keyword: str, n_videos: int = 250) -> pd.DataFrame:
    """엔드투엔드 진입점: 로그인 → 검색 → 수집 → 저장.

    .env에서 ``TIKTOK_EMAIL`` / ``TIKTOK_PASSWORD`` 읽어 자동 로그인.
    수집 결과는 ``data/tiktok/{keyword}.csv`` 로 저장.

    Args:
        keyword: TikTok 검색어. 빈 문자열이면 검색 단계 skip (디버깅용).
        n_videos: 수집할 영상 개수.

    Returns:
        수집된 DataFrame (CSV 저장도 함께 수행).

    Raises:
        RuntimeError: 자격증명 env가 비어있을 때 — 잡 시작 전 fail-fast.
    """
    email = os.environ.get("TIKTOK_EMAIL")
    password = os.environ.get("TIKTOK_PASSWORD")
    if not email or not password:
        raise RuntimeError(
            "TIKTOK_EMAIL / TIKTOK_PASSWORD 가 .env 에 없음. "
            ".env.example 참고해서 설정하세요."
        )

    driver = setup_driver()
    driver.get("https://www.tiktok.com/ko-KR")
    driver.implicitly_wait(5)

    login_tiktok(driver, email, password)
    if keyword:
        search_videos(driver, keyword)

    data = collect_video_metadata(driver, n_videos=n_videos)

    output_path = TIKTOK / f"{keyword or 'tiktok_crawl'}.csv"
    df = save_to_csv(data, output_path)
    print(f"saved {len(df)} rows → {output_path}")
    return df


if __name__ == "__main__":
    # CLI 실행 시 keyword 직접 지정 (모듈 import 시엔 main() 호출자가 지정)
    main(keyword="")