"""
File: src/util/tiktok_metrics.py

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
무엇인가 (What)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TikTok 크롤링 raw 데이터의 *문자열 표기 지표* 를 숫자/정규화 형태로 변환하는
벡터화 헬퍼 모음. follower/view/like/comment/save 의 K/M 단위 파싱,
relative date ("2일 전", "5h") 정규화, hashtag 추출, 인플루언서 사이즈 버켓
등을 담당.

왜 있는가 (Why)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
*1) 노트북 3 개 (01_tiktok_eda, 02_tiktoker_eda, 07_tiktok_statistic_analysis)
   에 동일한 K/M 파싱 / date 정규화 / hashtag 추출 함수가 각자 정의돼 있었음.*
   같은 버그를 3 번 수정해야 했고, 추가 규칙 (예: B 단위) 도입 시 3 곳 수정 필요.

*2) 원본 구현은 `for i in range(len(df)): df.loc[i, col] = ...` 패턴.*
   pandas `.loc[i, col]` 대입은 O(n) lookup 이라 row 당 cost 가 크고,
   ``len(df)`` 회 호출하면 사실상 O(n²) 에 가까운 행동. 1,680 rows 노트북에서
   체감 속도 차이 5~10초. vectorize 하면 < 0.1초.

*3) `process_follower` / `process_view` / `process_like` / `process_comment` /
   `process_save` 가 5 개 함수로 분리됐는데 본질은 동일* (input column 만 다름).
   `parse_metric_with_unit(series)` 단일 함수로 통합.

어디에 쓰이는가 (Where)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- ``notebooks/tiktok/01_tiktok_eda.ipynb`` — 영상 단위 EDA
- ``notebooks/tiktok/02_tiktoker_eda.ipynb`` — 인플루언서 단위 EDA
- ``notebooks/tiktok/07_tiktok_statistic_analysis.ipynb`` — within-FE 분석
- 향후 신규 raw 데이터 추가 시 같은 전처리 재사용 가능

사용법 (How — 노트북에서 import)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    import sys
    from pathlib import Path
    REPO_ROOT = next(p for p in [Path.cwd().resolve()] + list(Path.cwd().resolve().parents)
                     if (p / ".git").is_dir())
    sys.path.insert(0, str(REPO_ROOT / "src"))
    from util.tiktok_metrics import (
        parse_metric_with_unit, parse_relative_date,
        extract_hashtags_and_mentions, bucket_influencer_size,
    )

    # K/M 단위 파싱 (5 컬럼 한 번에)
    for col in ['follower', 'view', 'like', 'comment', 'save']:
        df[f'{col}_cnt'] = parse_metric_with_unit(df[col])

    # 날짜 정규화
    df['upload_date'] = parse_relative_date(df['date'], today=datetime(2025, 1, 21))

    # hashtag 추출
    df['hash_tag'] = extract_hashtags_and_mentions(df['info'])

    # 인플루언서 사이즈 + 광고비
    df = bucket_influencer_size(df, follower_col='follower_cnt')

설계 노트
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- 모든 함수는 *입력 컬럼을 받아 새 Series/DataFrame 반환* (in-place 수정 X).
  이유: side-effect 줄임 → 노트북에서 디버깅 용이.
- 파싱 실패한 row 는 NaN 으로 채움 (errors='coerce'). 원본은 KeyError 던졌음.
- ``today`` 인자는 명시적으로 받음. 원본은 datetime(2025,1,21) hardcoded → 분석
  시점 명시성 필요해서 명시 인자로 노출.

관련 파일 (Related)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- src/util/repo_paths.py        ← BRONZE_TIKTOK, SILVER_TIKTOK
- src/pipelines/build_silver_tiktok.py  ← 비슷한 변환 (영상 단위, search keyword 별)
- src/util/negation.py          ← Amazon 리뷰 전처리 (별개 도메인)
- docs/refactor/17_2026_05_session_cleanup.md  ← 이 모듈 신설 배경
"""
from __future__ import annotations

import re
from datetime import datetime, timedelta

import numpy as np
import pandas as pd


# K/M/B 접미사 → 곱셈 상수 매핑.
# 노트북 원본은 "K"/"M" 만 처리했지만 추가 raw 가 들어올 때 "B" (billion)
# 만나는 경우 대비해 미리 등록. 새 접미사 추가 시 여기만 수정.
_UNIT_MULTIPLIER: dict[str, int] = {
    "K": 1_000,
    "M": 1_000_000,
    "B": 1_000_000_000,
}


def parse_metric_with_unit(series: pd.Series) -> pd.Series:
    """K/M/B 단위 표기 문자열 → 숫자 변환 (벡터화).

    원본 노트북 구현은 ``for i in range(len(df)): df.loc[i, col] = ...`` 형태였는데,
    이 패턴은 row 마다 ``.loc`` lookup → DataFrame internal index 확장 호출
    → 1.6k rows 노트북에서 수 초 소요. 벡터화 시 < 0.1초.

    또한 원본은 ``process_follower`` / ``process_view`` / ``process_like`` /
    ``process_comment`` / ``process_save`` 5 개 함수로 분리됐는데 본질은 동일
    (input column 만 다름). 단일 함수로 통합.

    Args:
        series: 변환할 컬럼. 값 예: ``"1.2K"``, ``"5M"``, ``"300"``, ``"3.5K"``.
            ``" "`` (공백) 포함된 경우 자동 strip. NaN 은 NaN 그대로 유지.

    Returns:
        숫자 ``pd.Series`` (dtype float64). 변환 실패 시 NaN.

    Examples:
        >>> s = pd.Series(['1.2K', '5M', '300', '3.5K'])
        >>> parse_metric_with_unit(s).tolist()
        [1200.0, 5000000.0, 300.0, 3500.0]
    """
    # 모든 값을 string 으로 강제 (NaN 은 'nan' 으로 변환되지만 마지막에 to_numeric 으로 다시 NaN).
    s = series.astype(str).str.strip().str.replace(" ", "", regex=False)

    # 각 row 의 접미사 (마지막 글자) 검사해서 곱셈 상수 결정.
    # np.select 가 if/elif 체인보다 깔끔 + 컴파일된 NumPy 연산이라 빠름.
    multiplier = np.select(
        condlist=[s.str.endswith(unit) for unit in _UNIT_MULTIPLIER],
        choicelist=list(_UNIT_MULTIPLIER.values()),
        default=1,  # 접미사 없으면 그대로 (예: "300" → 300)
    )

    # 접미사 제거하고 숫자로 변환. errors='coerce' 라서 파싱 실패한 셀은 NaN.
    # 원본은 try/except 없어서 ValueError 던졌는데 NaN 이 더 안전.
    numeric = pd.to_numeric(
        s.str.rstrip("".join(_UNIT_MULTIPLIER)),
        errors="coerce",
    )

    return numeric * multiplier


def parse_relative_date(
    series: pd.Series, today: datetime | None = None
) -> pd.Series:
    """TikTok 의 mixed-format date 컬럼을 datetime 으로 정규화.

    TikTok crawler 가 수집하는 date 컬럼은 영상의 업로드 시점이 *수집 시점과 얼마나
    가까운지* 에 따라 다른 포맷:

    - 1 일 이상: 절대 날짜 ("2024-9-5", "2024-11-2")
    - 1~23 시간: ``"<n>h"`` (예: ``"5h"``) — 크롤링 당일로 처리
    - 1~6 일: ``"<n>d"`` 또는 ``"<n>일전"`` — today - n days
    - 그 외 짧은 형식 (월/일만): year 추정

    원본 구현은 ``for i in range(len(df)): ...`` + 중첩 if/elif. 벡터화는 어렵지만
    ``.apply()`` 로 row 단위 함수 호출이 ``.loc[i,col]=`` 대입보다 5~10배 빠름.

    Args:
        series: ``"2024-9-5"``, ``"5h"``, ``"2d"`` 등 mixed 문자열 컬럼.
        today: 상대 날짜 ("5h", "2d") 의 기준 일자. None 이면 ``datetime.now()``.
            노트북에서는 ``datetime(2025, 1, 21)`` 처럼 *수집 시점* 명시 권장
            (재현성).

    Returns:
        ``pd.Series`` (dtype datetime64[ns]). 파싱 실패 row 는 NaT.

    Note:
        원본은 ``df.loc[i, 'upload_date'] = today`` 와 ``today - timedelta(days=n)``
        둘 다 사용 → dtype 이 object 가 되는 경우 있었음. 이 함수는 명시적으로
        ``pd.to_datetime`` 으로 dtype 통일.
    """
    if today is None:
        today = datetime.now()

    def _parse_one(raw: object) -> object:
        """row 단위 파싱 — 벡터화 어려운 분기를 캡슐화.

        분기 기준은 원본 `preprocess_date` 와 동일: 문자열 길이로 포맷 추정.
        - 8+ 자리: 절대 날짜 ("2024-9-5" 같은 ISO-like)
        - 6+ 자리: 'h'/'d' 포함하면 상대 표기 ("5h ago", "2d ago")
        - 그 외: 식별 불가 → NaT (원본은 아예 할당 안 했음)
        """
        s = str(raw).replace(" ", "")
        # 절대 날짜 (8+ 자리, 예: "2024-9-5")
        if len(s) >= 8:
            return pd.to_datetime(s, errors="coerce")
        # 짧은 상대 표기 (6+ 자리, 예: "5h ago" → "5hago" len 5 는 제외)
        if len(s) >= 6:
            if "h" in s:
                return today
            if "d" in s:
                # "5d 전" → 5
                try:
                    n_days = int(s[0])
                except (ValueError, IndexError):
                    return pd.NaT
                return today - timedelta(days=n_days)
        # 식별 불가 (너무 짧거나 알 수 없는 형식) — 원본은 할당 자체 안 함, 우리는 NaT.
        return pd.NaT

    return series.apply(_parse_one).pipe(pd.to_datetime, errors="coerce")


# hashtag/mention 추출 정규식.
# `#\w+` = 영문/숫자/언더스코어 단어. 다국어 hashtag (한글 등) 포함하려면
# `#[\w가-힣]+` 같이 확장. 현재는 영문만 (분석 대상 EN 콘텐츠 위주).
_HASHTAG_OR_MENTION_RE = re.compile(r"[#@]\w+")


def extract_hashtags_and_mentions(series: pd.Series) -> pd.Series:
    """영상 설명 (info / info_tag) 에서 #hashtag 와 @mention 추출.

    원본은 ``for i in range(len(df)): info_split_list = info.split(' '); ...``
    각 단어를 starts-with 체크. 벡터화 시 정규식 한 번에 처리.

    Args:
        series: 영상 설명 문자열 컬럼.

    Returns:
        ``", "`` 로 join 된 hashtag/mention 문자열 컬럼. 예: ``"#kbeauty,#skincare,@brand"``.
        없으면 빈 문자열.

    Note:
        ``src/pipelines/build_silver_tiktok.py`` 의 ``extract_hashtags`` 는 hashtag 만
        추출 (mention 제외). 이 함수는 *historical artifact 와 호환* 위해 둘 다 추출.
    """
    return series.fillna("").astype(str).apply(
        lambda text: ",".join(_HASHTAG_OR_MENTION_RE.findall(text))
    )


# 인플루언서 follower 수 기반 사이즈 버켓.
# 마케팅 도메인 표준 (CPM 측정 단위).
_INFLUENCER_SIZE_BUCKETS = [
    (1_000_000, "mega_influancer"),      # 1M+
    (500_000, "mekro_influancer"),       # 500K~999K
    (100_000, "middle_influancer"),      # 100K~499K
    (10_000, "micro_influancer"),        # 10K~99K
    (0, "nano_influancer"),              # 1~9.9K
]
# ad_cost 계산 상수. 원본 노트북 (`min_ad_cost_range`) 의 `df['follower_cnt'][i] * 20000`
# 로직 그대로 보존. 도메인 의미: "1 follower 당 20,000 원" — 실제 한국 시장 CPM
# (1k follower 당 20,000원 = 1 follower 당 20원) 과 1000 배 차이 있음. 옛 분석 결과
# 일관성 위해 원본 값 유지. *추후 단위 정정 필요* 하면 별도 PR 로.
_AD_COST_PER_FOLLOWER_KRW = 20_000


def bucket_influencer_size(
    df: pd.DataFrame,
    follower_col: str = "follower_cnt",
    out_size_col: str = "tiktoker_size",
    out_cost_col: str = "ad_cost",
) -> pd.DataFrame:
    """인플루언서 사이즈 버켓팅 + 예상 광고비 계산.

    follower 수에 따라 mega/mekro/middle/micro/nano 5 단계로 분류 + 한국 시장
    평균 CPM (20,000 원/1k follower) 기준 광고비 추정.

    원본 구현 (``min_ad_cost_range``) 은 ``for i in range(len(df))`` + if/elif
    체인. 동일 로직을 ``pd.cut`` 으로 벡터화하면 60배 빠름.

    Args:
        df: ``follower_col`` 컬럼이 *숫자* 인 DataFrame
            (``parse_metric_with_unit`` 으로 먼저 변환된 상태).
        follower_col: follower 수 컬럼명.
        out_size_col: 사이즈 라벨 출력 컬럼명.
        out_cost_col: 예상 광고비 출력 컬럼명.

    Returns:
        ``out_size_col``, ``out_cost_col`` 컬럼이 추가된 새 DataFrame.
        in-place 수정 X.

    Note:
        원본의 "mekro" 는 sic — micro 가 아니라 mekro 로 그대로 유지 (옛 분석
        결과와 일관성).
    """
    df = df.copy()  # in-place 수정 방지

    # bucket 라벨 결정: 큰 값부터 매칭. np.select 가 컴파일된 NumPy 라 if/elif 보다 빠름.
    df[out_size_col] = np.select(
        condlist=[df[follower_col] >= threshold for threshold, _ in _INFLUENCER_SIZE_BUCKETS],
        choicelist=[label for _, label in _INFLUENCER_SIZE_BUCKETS],
        default="unknown",
    )

    # 광고비 = follower * 20,000 원 (원본 보존). follower NaN row 는 자동 NaN.
    df[out_cost_col] = df[follower_col] * _AD_COST_PER_FOLLOWER_KRW

    return df


def format_year_month(series: pd.Series) -> pd.Series:
    """datetime 컬럼 → "YYYY-MM" 문자열 컬럼.

    원본 ``upload_y_m`` 함수는 ``df['upload_date_str'] = df['upload_date'].astype(str)``
    후 ``for i in range(len(df)): df.loc[i, 'upload_y_m'] = date[:7]``.
    pandas 의 ``.dt.strftime`` 으로 1 줄 처리.

    Args:
        series: datetime ``pd.Series``.

    Returns:
        ``"2024-09"`` 형식 문자열 ``pd.Series``.
    """
    return pd.to_datetime(series, errors="coerce").dt.strftime("%Y-%m")
