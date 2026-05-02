"""미국 주소 데이터 합성에 필요한 공통 유틸 (파서 + 인구 쿼터).

``crawl_random_address.py`` (실제 크롤러) 와 ``address_ratio.ipynb`` (분석)
양쪽이 같은 코드를 갖고 있던 걸 한 곳으로 모은 모듈. 새 노트북/스크립트가
주소 데이터 다룰 때 이 모듈을 거치도록 하면 (1) 데이터 모양/쿼터 변경이 한 곳에서만,
(2) 의도가 명확해진다 (`from address_utils import addr_to_df`).
"""
from __future__ import annotations

import math
import re

import pandas as pd


# 미국 주별 전체 인구 비율 (%, 합산 ~100). 합성 데이터 quota를 인구
# 비율과 비슷하게 맞추기 위해 사용. 출처는 정부 추계 근사치.
STATE_POPULATION_PCT: dict[str, float] = {
    "AK": 0.3, "AL": 1.5, "AR": 1.2, "AZ": 2.2, "CO": 1.7, "CT": 1.1,
    "DC": 0.2, "DE": 0.3, "FL": 6.5, "GA": 3.2, "HI": 0.4, "IA": 1.0,
    "ID": 0.6, "IL": 3.9, "IN": 2.1, "KS": 1.0, "KY": 1.6, "LA": 1.3,
    "MA": 2.0, "MD": 1.9, "ME": 0.4, "MI": 3.6, "MN": 1.8, "MO": 2.2,
    "MS": 1.1, "MT": 0.3, "NC": 3.2, "ND": 0.2, "NE": 0.9, "NH": 0.4,
    "NJ": 2.8, "NM": 0.9, "NV": 1.0, "NY": 6.1, "OH": 3.5, "OK": 1.3,
    "OR": 1.3, "PA": 4.1, "RI": 0.3, "SC": 2.0, "SD": 0.3, "TN": 2.2,
    "TX": 8.7, "UT": 1.0, "VA": 2.5, "VT": 0.1, "WA": 2.3, "WI": 2.3,
    "WV": 0.6, "WY": 0.1,
}


# postcodebase.com 같은 사이트가 한 줄로 주는 주소 형식 파싱.
# 예: ``"445 S ARDMORE AVE LOS ANGELES CA 90020-3265 USA"``
# → ``detailed_address``, ``city``, ``state``, ``zipcode`` 4개 named group.
_ADDRESS_PATTERN = re.compile(
    r"(?P<detailed_address>.+?)\s"
    r"(?P<city>[A-Za-z\s]+)\s"
    r"(?P<state>[A-Z]{2})\s"
    r"(?P<zipcode>\d{5}-\d{4}|\d{5})\s"
    r"USA"
)


def addr_to_df(address_block: str) -> pd.DataFrame:
    """줄바꿈으로 구분된 미국 주소 텍스트 블록을 DataFrame으로 파싱.

    각 줄이 ``"<번지+도로명> <도시> <주> <zip> USA"`` 형식이라 가정.
    매칭 실패하는 줄은 결과에서 조용히 누락 (입력에 잡음 라인이 있어도 robust).

    Args:
        address_block: 줄바꿈으로 여러 주소가 구분된 큰 문자열.

    Returns:
        ``detailed_address, city, state, zipcode`` 4개 컬럼을 가진 DataFrame.
        매칭 0건이면 빈 DataFrame.
    """
    rows: list[dict] = []
    for line in address_block.strip().splitlines():
        m = _ADDRESS_PATTERN.match(line)
        if m:
            rows.append(m.groupdict())
    return pd.DataFrame(rows)


def compute_state_quotas(total_count: int) -> list[tuple[str, int]]:
    """전체 합성 주소 개수에서 주별 쿼터를 인구 비율로 분배.

    합성 데이터가 미국 전체 인구 분포와 비슷하게 보이도록, ``total_count`` 를
    ``STATE_POPULATION_PCT`` 비율로 나눠 ``(주코드, 쿼터)`` 리스트를 반환.
    각 quota는 올림(``ceil``) 처리해 과소 표집을 막는다.

    Args:
        total_count: 합성하고 싶은 전체 주소 개수.

    Returns:
        ``[(state_code, quota), ...]`` — ``STATE_POPULATION_PCT`` 의 순서를 따름.
        예: ``total_count=12797`` 이면 ``[("AK", 39), ("AL", 192), ...]``.
    """
    return [
        (state, math.ceil(total_count * pct * 0.01))
        for state, pct in STATE_POPULATION_PCT.items()
    ]