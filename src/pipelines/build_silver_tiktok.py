"""TikTok bronze → silver 변환 파이프라인.

**현재 silver 파일 상태**
``data/silver/tiktok/tiktok_videos_silver.csv`` 는 원본 4개 raw csv 를 외부
환경(작성자 로컬 크롤러)에서 변환한 *historical artifact* 다. 이 스크립트는
그 결과를 재현하는 게 아니라, **신규 raw csv 가 추가됐을 때** 동일 스키마의
silver 를 새로 생성하기 위한 canonical 파이프라인이다.

**실행 방법**
    python src/pipelines/build_silver_tiktok.py

**입력** (``data/bronze/tiktok/``)
    파일명 패턴: ``tiktok_search_<search_term>.csv``
    필수 컬럼: like, comment, save, tiktoker_name, date, info

**출력** (``data/silver/tiktok/``)
    ``tiktok_videos_silver.csv`` — 9 컬럼 고정 스키마:
    search_term, vedio_order, tiktoker_name, upload_date,
    like_cnt, comment_cnt, save_cnt, info, hash_tag
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pandas as pd

# repo root 기준 import
_HERE = Path(__file__).resolve()
REPO_ROOT = next(p for p in _HERE.parents if (p / ".git").is_dir())
sys.path.insert(0, str(REPO_ROOT / "src"))

from util.repo_paths import BRONZE_TIKTOK, SILVER_TIKTOK

# bronze 파일명 → search_term 매핑.
# 새 파일 추가 시 여기에 등록.
_FILENAME_TO_SEARCH_TERM: dict[str, str] = {
    "tiktok_search_cleanbeauty.csv": "clean_beauty",
    "tiktok_search_cleanbeauty_v2_0124.csv": "clean_beauty",
    "tiktokers_raw.csv": None,  # 영상 데이터 아님 — 변환 대상 제외
}

# silver 고정 컬럼 순서
_SILVER_COLUMNS = [
    "search_term", "vedio_order", "tiktoker_name", "upload_date",
    "like_cnt", "comment_cnt", "save_cnt", "info", "hash_tag",
]


def extract_hashtags(text: str) -> str:
    """info 문자열에서 #hashtag 패턴을 추출해 공백 구분 문자열로 반환.

    Args:
        text: TikTok 영상 설명 원문.

    Returns:
        ``"#cleanskin #kbeauty"`` 형식 문자열. 없으면 빈 문자열.

    Note:
        historical silver 의 hash_tag 컬럼은 @mention 을 포함하는 등
        추출 로직이 불명확하다. 신규 데이터는 이 함수 기준으로 통일한다.
    """
    tags = re.findall(r"#\w+", str(text))
    return " ".join(tags)


def load_one(path: Path, search_term: str) -> pd.DataFrame:
    """bronze csv 한 파일을 읽어 silver 스키마로 변환.

    Args:
        path: bronze csv 경로.
        search_term: 이 파일에 해당하는 TikTok 검색어 (silver ``search_term`` 컬럼).

    Returns:
        silver 스키마 DataFrame (hash_tag, vedio_order 포함).
    """
    df = pd.read_csv(path)

    # 컬럼 rename: raw → silver 명명 규칙
    df = df.rename(columns={
        "like":    "like_cnt",
        "comment": "comment_cnt",
        "save":    "save_cnt",
        "date":    "upload_date",
    })

    # vedio_order: 크롤링 수집 순서 (1-based)
    df["vedio_order"] = range(1, len(df) + 1)
    df["search_term"] = search_term
    df["hash_tag"] = df["info"].apply(extract_hashtags)

    return df[_SILVER_COLUMNS]


def build_silver(overwrite: bool = False) -> None:
    """BRONZE_TIKTOK 의 등록된 csv 를 읽어 silver 로 저장.

    Args:
        overwrite: True 면 기존 silver 파일 덮어씀.
            False(기본) 이면 이미 존재할 경우 중단.

    Raises:
        FileExistsError: overwrite=False 인데 silver 파일이 이미 존재할 때.
        FileNotFoundError: BRONZE_TIKTOK 에 등록된 파일이 하나도 없을 때.
    """
    out_path = SILVER_TIKTOK / "tiktok_videos_silver.csv"

    if out_path.exists() and not overwrite:
        raise FileExistsError(
            f"{out_path} 이미 존재. 덮어쓰려면 overwrite=True 로 실행.\n"
            "  python build_silver_tiktok.py --overwrite"
        )

    frames: list[pd.DataFrame] = []

    for filename, search_term in _FILENAME_TO_SEARCH_TERM.items():
        # search_term=None 은 영상 데이터가 아닌 파일 (tiktokers_raw 등) — 건너뜀
        if search_term is None:
            continue
        path = BRONZE_TIKTOK / filename
        if not path.exists():
            print(f"[skip] {filename} — 파일 없음")
            continue
        df = load_one(path, search_term)
        print(f"[load] {filename} → search_term={search_term!r}, {len(df)} rows")
        frames.append(df)

    if not frames:
        raise FileNotFoundError(
            "변환할 bronze 파일을 하나도 찾지 못함. "
            "_FILENAME_TO_SEARCH_TERM 등록 확인."
        )

    # 같은 search_term 의 여러 파일은 concat 후 dedup
    silver = pd.concat(frames, ignore_index=True)
    before = len(silver)
    silver = silver.drop_duplicates(
        subset=["tiktoker_name", "upload_date", "search_term"]
    )
    print(f"dedup: {before} → {len(silver)} rows")

    # vedio_order 는 dedup 후 search_term 내에서 재부여
    silver["vedio_order"] = (
        silver.groupby("search_term").cumcount() + 1
    )

    SILVER_TIKTOK.mkdir(parents=True, exist_ok=True)
    silver.to_csv(out_path, index=False)
    print(f"saved → {out_path}  ({len(silver)} rows)")


if __name__ == "__main__":
    # --overwrite 플래그 지원
    _overwrite = "--overwrite" in sys.argv
    build_silver(overwrite=_overwrite)
