"""반복되는 비자명한 데이터 로딩만 함수로 묶어둔 모듈.

원칙: 단순한 ``pd.read_csv(PATH / "foo.csv")`` 한 줄짜리는 인라인으로 두고,
**여러 파일/단계를 함께 로드해야 한다거나 변환이 필요한 경우만** 함수로
분리한다 — 의미 없는 wrapping은 만들지 않는다.
"""
from __future__ import annotations

import pandas as pd

from util.repo_paths import SILVER_TIKTOK


# Amazon 분석 대상 5개 K-뷰티 브랜드 슬러그.
# CSV 파일명은 ``{brand}_items.csv`` / ``{brand}_reviews.csv`` 패턴.
# 노트북에서 5개 브랜드를 순회하며 일괄 처리할 때 import 해서 사용.
AMAZON_BRANDS = ("Dr_jart", "cosrx", "imfrom", "joseon", "purito")


# `tiktok_post_final_df.csv` 안의 search_term 컬럼 unique 값 매핑.
# 'clean_beauty'만 underscore이고 나머지 3개는 공백 — 크롤링 시점의 검색어 그대로다.
# (key는 변수명에 쓰기 좋게 underscore로 통일했다.)
_TIKTOK_SEARCH_TERMS = {
    "clean_beauty":      "clean_beauty",
    "glow_skin":         "glow skin",
    "kbeauty_skin_care": "kbeauty skin care",
    "korean_skincare":   "korean skincare",
}


def load_keyword_dfs() -> dict[str, pd.DataFrame]:
    """4개 검색어로 크롤링한 TikTok post 데이터를 search_term별로 분리해 반환.

    원본 4개 raw csv (`tiktok_post_clean_beauty_0124.csv` 등)는 분실됐기에
    이미 처리/dedup이 끝난 통합본 ``tiktok_videos_silver.csv`` 한 번만 읽고
    `search_term` 컬럼으로 split한다. 노트북마다 같은 split 코드를 반복하는
    걸 막기 위함 — 단일 read_csv보다 진짜 절약 효과가 있어서 함수로 묶는다.

    silver 단계 = raw 4 → final 변환 결과의 *historical artifact*. 변환 코드
    자체는 외부 환경 의존으로 reproduce 불가. 자세히는 docs 참조.

    Returns:
        dict — key 목록:
            - ``"all"``: split 전 전체 DataFrame
            - ``"clean_beauty"``, ``"glow_skin"``,
              ``"kbeauty_skin_care"``, ``"korean_skincare"``:
              각 검색어로 필터링한 subset (.copy() 적용으로 SettingWithCopy 방지)
    """
    df = pd.read_csv(SILVER_TIKTOK / "tiktok_videos_silver.csv")
    out: dict[str, pd.DataFrame] = {"all": df}
    for key, search_term in _TIKTOK_SEARCH_TERMS.items():
        out[key] = df[df["search_term"] == search_term].copy()
    return out