"""
File: src/pipelines/build_silver_amazon.py

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
무엇인가 (What)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Amazon bronze(브랜드별 items/reviews CSV) → silver(분석 입력용 통합본) 변환
파이프라인. ``notebooks/amazon/01_amazon_preprocessing.ipynb`` 의 시각화를
제외한 순수 변환 로직만 추출한 CLI 실행 가능 버전.

출력 3파일:
- ``data/silver/amazon/amazon_reviews_lemmatized.csv``  — 5 브랜드 통합 리뷰
- ``data/silver/amazon/amazon_items_processed.csv``     — 5 브랜드 통합 아이템
- ``data/silver/amazon/skinsort_processed.csv``         — Skinsort 정제본

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
왜 있는가 (Why)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
노트북을 직접 열지 않고 silver 를 재생성해야 할 때 (예: 새 브랜드 추가,
크롤링 후 자동화 배치). 노트북은 run-all 시 시각화가 함께 실행되어 무겁고,
의도치 않은 덮어쓰기 위험이 있다. 이 스크립트는 overwrite 플래그 필수.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
어디에 쓰이는가 (Where)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- ``data/bronze/amazon/`` → 읽기
- ``data/silver/amazon/`` → 쓰기
- 생성된 silver 파일은 ``notebooks/amazon/02_*``, ``03_*`` 노트북이 읽어 사용.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
어떤 상황 (When)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. ``data/bronze/amazon/`` 에 새 브랜드 items/reviews CSV 추가
2. ``_BRANDS`` 에 새 브랜드 등록
3. ``python src/pipelines/build_silver_amazon.py --overwrite``
4. 생성된 silver 파일로 02/03 노트북 재실행

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
사용법 (How)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # silver 파일이 없을 때 (처음 생성)
    python src/pipelines/build_silver_amazon.py

    # 기존 silver 덮어쓰기 (신규 데이터 추가 후)
    python src/pipelines/build_silver_amazon.py --overwrite

입력 파일 패턴 (bronze/amazon/):
    {prefix}_items.csv, {prefix}_reviews.csv  — 브랜드별 크롤링 결과
    skinsort_0115.csv                          — Skinsort 한국 브랜드 데이터

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
설계 노트
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- 언어 감지(langdetect) + 번역(deep_translator)은 시간이 오래 걸리므로 기본
  비활성. ``--translate`` 플래그로 활성화 가능.
- bigram/trigram PMI 임계값(pmi_threshold=5, freq_filter=40)은 01 노트북의
  탐색 결과를 그대로 고정. 데이터가 크게 바뀌면 노트북에서 재탐색 필요.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
관련 파일 (Related)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- src/util/repo_paths.py                      ← BRONZE_AMAZON, SILVER_AMAZON
- notebooks/amazon/01_amazon_preprocessing.ipynb ← 이 스크립트의 원본 노트북
- notebooks/amazon/02_amazon_eda.ipynb        ← silver 읽는 다음 노트북
- src/amazon_review_crawler/                  ← bronze CSV 생성 크롤러
"""
from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

# repo root 기준 import
_HERE = Path(__file__).resolve()
REPO_ROOT = next(p for p in _HERE.parents if (p / ".git").is_dir())
sys.path.insert(0, str(REPO_ROOT / "src"))

from util.repo_paths import BRONZE_AMAZON, SILVER_AMAZON

# 브랜드별 bronze 파일 prefix → 브랜드 표시명 매핑.
# 새 브랜드 추가 시 여기에 등록.
_BRANDS: dict[str, str] = {
    "Dr_jart":  "Dr.Jart+",
    "cosrx":    "COSRX",
    "imfrom":   "I'm from",
    "joseon":   "Beauty of Joseon",
    "purito":   "PURITO",
}

_SKINSORT_FILE = "skinsort_0115.csv"

# bigram/trigram PMI 파라미터 — 01 노트북 탐색 결과 고정값
_FREQ_FILTER = 40
_PMI_THRESHOLD = 5


# ─── 로드 ────────────────────────────────────────────────────────────────────

def load_brand(prefix: str, brand_name: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """브랜드 prefix 로 items + reviews CSV 를 로드해 반환.

    Args:
        prefix: bronze 파일명 prefix (예: ``"Dr_jart"``).
        brand_name: silver 에 기록할 브랜드 표시명 (예: ``"Dr.Jart+"``).

    Returns:
        (items_df, reviews_df) — 원본 그대로 (전처리 전).

    Raises:
        FileNotFoundError: bronze 파일이 없을 때.
    """
    items_path   = BRONZE_AMAZON / f"{prefix}_items.csv"
    reviews_path = BRONZE_AMAZON / f"{prefix}_reviews.csv"
    for p in (items_path, reviews_path):
        if not p.exists():
            raise FileNotFoundError(f"bronze 파일 없음: {p}")
    items   = pd.read_csv(items_path)
    reviews = pd.read_csv(reviews_path)
    # 크롤러가 'No brand' 로 채운 경우 실제 브랜드명으로 교체
    items["brand"].replace("No brand", brand_name, inplace=True)
    return items, reviews


def load_skinsort() -> pd.DataFrame:
    """Skinsort CSV 를 로드.

    Returns:
        skinsort 원본 DataFrame.

    Raises:
        FileNotFoundError: skinsort 파일이 없을 때.
    """
    path = BRONZE_AMAZON / _SKINSORT_FILE
    if not path.exists():
        raise FileNotFoundError(f"skinsort 파일 없음: {path}")
    return pd.read_csv(path)


# ─── 전처리 ──────────────────────────────────────────────────────────────────

def preprocess_items(df: pd.DataFrame) -> pd.DataFrame:
    """items DataFrame 결측치 표준화 + description/detail_dict JSON 전개.

    Args:
        df: items 원본 DataFrame.

    Returns:
        전처리된 items DataFrame.
    """
    df = df.copy()
    # 크롤러 sentinel 값 → NaN
    df["best_sellers_rank_Feature"].replace("No result", np.nan, inplace=True)
    df["global_rating_count"].replace("No rating",  np.nan, inplace=True)
    df["Special_Feature"].replace("No special feature", np.nan, inplace=True)

    # description JSON 문자열 → 컬럼 전개
    for i in range(len(df)):
        try:
            desc = ast.literal_eval(df["description"].iloc[i])
            for key, value in desc.items():
                if key not in df.columns:
                    df[key] = np.nan
                df.at[i, key] = value
        except Exception:
            continue
    df.drop(columns=["description"], errors="ignore", inplace=True)

    # detail_dict JSON 문자열 → 컬럼 전개
    for i in range(len(df)):
        try:
            detail = ast.literal_eval(df["detail_dict"].iloc[i])
            for key, value in detail.items():
                col = f"detail_{key}"
                if col not in df.columns:
                    df[col] = np.nan
                df.at[i, col] = value
        except Exception:
            continue
    df.drop(columns=["detail_dict"], errors="ignore", inplace=True)

    return df


def preprocess_reviews(df: pd.DataFrame) -> pd.DataFrame:
    """reviews DataFrame — date 파싱 + rating 숫자 변환.

    Args:
        df: reviews 원본 DataFrame.

    Returns:
        전처리된 reviews DataFrame.
    """
    df = df.copy()
    df["date"].replace("No date", np.nan, inplace=True)
    df["review_rating"].replace("No review", np.nan, inplace=True)

    # "Reviewed in ... on YYYY-MM-DD" → review_date 컬럼
    df["review_date"] = df["date"].apply(
        lambda x: pd.to_datetime(x.split("on")[1].strip(), errors="coerce")
        if isinstance(x, str) and "on" in x else pd.NaT
    )
    # "4.0 out of 5 stars" → float
    df["review_rating"] = df["review_rating"].apply(
        lambda x: float(x.split()[0]) if isinstance(x, str) and x[0].isdigit() else np.nan
    )
    return df


def merge_brand(items: pd.DataFrame, reviews: pd.DataFrame) -> pd.DataFrame:
    """items + reviews 를 ASIN 기준 merge 하고 컬럼명 정리.

    Args:
        items: preprocess_items() 결과.
        reviews: preprocess_reviews() 결과.

    Returns:
        merge 된 DataFrame.
    """
    df = pd.merge(items, reviews, on="ASIN")
    df.rename(columns={"content": "review_content", "title_x": "title"}, inplace=True)
    df.drop(columns=["title_y"], errors="ignore", inplace=True)
    df.reset_index(drop=True, inplace=True)
    return df


def preprocess_skinsort(df: pd.DataFrame) -> pd.DataFrame:
    """Skinsort DataFrame 결측치 제거 + 컬럼 포맷 정리.

    Args:
        df: skinsort 원본 DataFrame.

    Returns:
        정제된 skinsort DataFrame.
    """
    df = df.copy()
    df.dropna(subset=["country", "afterUse", "type"], inplace=True)
    df.reset_index(inplace=True)

    # "ingredient1,ingredient2" → "ingredient1, ingredient2" (가독성)
    for col in ("ingridients", "afterUse"):
        if col in df.columns:
            df[col] = df[col].apply(
                lambda x: re.sub(r",(?!\s)", ", ", str(x)) if isinstance(x, str) else x
            )
    return df


# ─── 텍스트 전처리 ───────────────────────────────────────────────────────────

def _detect_and_translate(df: pd.DataFrame) -> pd.DataFrame:
    """비영어 리뷰 감지 + 영어 번역 (옵션, --translate 플래그 시 호출).

    Args:
        df: review_content 컬럼이 있는 DataFrame.

    Returns:
        detected_language 컬럼 추가 + 비영어 리뷰 번역된 DataFrame.

    Note:
        langdetect / deep_translator 패키지 필요. 건당 네트워크 요청 발생 —
        수천 건 이상이면 수십 분 소요.
    """
    try:
        from langdetect import DetectorFactory, detect
        from langdetect.lang_detect_exception import LangDetectException
        from deep_translator import GoogleTranslator
        DetectorFactory.seed = 0
    except ImportError:
        print("[warn] langdetect / deep_translator 미설치 — 번역 건너뜀")
        return df

    def detect_lang(text: str) -> str:
        try:
            return detect(text)
        except LangDetectException:
            return "unknown"

    def translate_en(text: str) -> str:
        try:
            return GoogleTranslator(source="auto", target="en").translate(text)
        except Exception:
            return text

    df = df.copy()
    df["review_content"] = df["review_content"].fillna("").astype(str)
    df["detected_language"] = df["review_content"].apply(detect_lang)
    mask = df["detected_language"] != "en"
    df.loc[mask, "review_content"] = df.loc[mask, "review_content"].apply(translate_en)
    return df


def lemmatize_reviews(df: pd.DataFrame) -> pd.DataFrame:
    """review_content 를 lemmatize 해 lemmatized_review / cleaned_review 컬럼 추가.

    Args:
        df: review_content 컬럼이 있는 DataFrame.

    Returns:
        lemmatized_review (문자열), cleaned_review (문자열) 컬럼이 추가된 DataFrame.

    Note:
        NLTK punkt_tab / stopwords / wordnet / omw-1.4 다운로드 필요.
        처음 실행 시 자동 다운로드.
    """
    import nltk
    from nltk.corpus import stopwords
    from nltk.stem import WordNetLemmatizer
    from nltk.tokenize import word_tokenize

    for resource in ("punkt_tab", "stopwords", "wordnet", "omw-1.4"):
        nltk.download(resource, quiet=True)

    lemmatizer = WordNetLemmatizer()
    stop_words = set(stopwords.words("english"))

    def _lemmatize(text: str) -> str:
        if not isinstance(text, str):
            return ""
        tokens = word_tokenize(text.lower())
        tokens = [
            lemmatizer.lemmatize(w) for w in tokens
            if w.isalpha() and w not in stop_words and len(w) > 2
        ]
        return " ".join(tokens)

    df = df.copy()
    df["review_content"] = df["review_content"].fillna("").astype(str)
    df["lemmatized_review"] = df["review_content"].apply(_lemmatize)
    df["cleaned_review"] = df["lemmatized_review"]
    return df


def build_ngrams(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str], list[str]]:
    """PMI 기반 bigram / trigram 추출 후 리뷰에 결합.

    Args:
        df: cleaned_review 컬럼이 있는 DataFrame.

    Returns:
        (df_with_ngrams, bigrams, trigrams) —
        df_with_ngrams: n-gram 결합된 lemmatized_review 컬럼,
        bigrams / trigrams: 선택된 n-gram 문자열 리스트.

    Note:
        PMI 임계값과 빈도 필터는 모듈 상단 상수(_PMI_THRESHOLD, _FREQ_FILTER)
        에서 관리. 01 노트북 탐색으로 결정된 값이며, 데이터가 크게 바뀌면
        노트북에서 재탐색 후 갱신 필요.
    """
    import nltk

    nltk.download("averaged_perceptron_tagger_eng", quiet=True)

    stop_words = set(__import__("nltk").corpus.stopwords.words("english"))
    docs = [c.split() for c in df["cleaned_review"].dropna() if isinstance(c, str)]

    # bigram PMI
    bigram_measures = nltk.collocations.BigramAssocMeasures()
    bf = nltk.collocations.BigramCollocationFinder.from_documents(docs)
    bf.apply_freq_filter(_FREQ_FILTER)
    bigram_scores = bf.score_ngrams(bigram_measures.pmi)
    bigram_pmi = pd.DataFrame(bigram_scores, columns=["bigram", "pmi"])

    def bigram_filter(row: pd.Series) -> bool:
        bg = row["bigram"]
        tag = nltk.pos_tag(bg)
        if tag[0][1] not in ["JJ", "NN"] and tag[1][1] not in ["NN"]:
            return False
        if bg[0] in stop_words or bg[1] in stop_words:
            return False
        if "n" in bg or "t" in bg or "PRON" in bg:
            return False
        return row["pmi"] > _PMI_THRESHOLD

    filtered_bigram = bigram_pmi[bigram_pmi.apply(bigram_filter, axis=1)][:500]
    bigrams = [" ".join(bg) for bg in filtered_bigram["bigram"]]

    # trigram PMI
    trigram_measures = nltk.collocations.TrigramAssocMeasures()
    tf = nltk.collocations.TrigramCollocationFinder.from_documents(docs)
    tf.apply_freq_filter(_FREQ_FILTER)
    trigram_scores = tf.score_ngrams(trigram_measures.pmi)
    trigram_pmi = pd.DataFrame(trigram_scores, columns=["trigram", "pmi"])

    def trigram_filter(row: pd.Series) -> bool:
        tg = row["trigram"]
        tag = nltk.pos_tag(tg)
        if tag[0][1] not in ["JJ", "NN"] and tag[1][1] not in ["JJ", "NN"]:
            return False
        if tg[0] in stop_words or tg[-1] in stop_words:
            return False
        return row["pmi"] > _PMI_THRESHOLD

    filtered_trigram = trigram_pmi[trigram_pmi.apply(trigram_filter, axis=1)][:500]
    trigrams = [" ".join(tg) for tg in filtered_trigram["trigram"]]

    # n-gram 결합
    def replace_ngram(text: str) -> str:
        for gram in trigrams:
            text = text.replace(gram, "_".join(gram.split()))
        for gram in bigrams:
            text = text.replace(gram, "_".join(gram.split()))
        return text

    df = df.copy()
    df["lemmatized_review"] = df["lemmatized_review"].apply(
        lambda x: replace_ngram(x) if isinstance(x, str) else x
    )
    print(f"bigrams: {len(bigrams)}개, trigrams: {len(trigrams)}개 선택")
    return df, bigrams, trigrams


# ─── 메인 파이프라인 ─────────────────────────────────────────────────────────

def build_silver(overwrite: bool = False, translate: bool = False) -> None:
    """Amazon bronze → silver 전체 파이프라인 실행.

    Args:
        overwrite: True 면 기존 silver 파일 덮어씀.
            False(기본) 이면 이미 존재할 경우 중단.
        translate: True 면 비영어 리뷰를 Google Translate 로 번역.
            기본 False (시간 소요 + 네트워크 필요).

    Raises:
        FileExistsError: overwrite=False 인데 silver 파일이 이미 존재할 때.
        FileNotFoundError: bronze 파일이 하나라도 없을 때.
    """
    out_reviews  = SILVER_AMAZON / "amazon_reviews_lemmatized.csv"
    out_items    = SILVER_AMAZON / "amazon_items_processed.csv"
    out_skinsort = SILVER_AMAZON / "skinsort_processed.csv"

    if any(p.exists() for p in (out_reviews, out_items, out_skinsort)) and not overwrite:
        raise FileExistsError(
            "silver 파일이 이미 존재합니다. 덮어쓰려면 --overwrite 로 실행.\n"
            "  python src/pipelines/build_silver_amazon.py --overwrite"
        )

    # ── 1. 브랜드별 로드 + 전처리 + merge ──────────────────────────────────
    brand_frames: list[pd.DataFrame] = []
    items_frames: list[pd.DataFrame] = []

    for prefix, brand_name in _BRANDS.items():
        print(f"[load] {prefix} ({brand_name})")
        items_raw, reviews_raw = load_brand(prefix, brand_name)
        items_clean   = preprocess_items(items_raw)
        reviews_clean = preprocess_reviews(reviews_raw)
        merged = merge_brand(items_clean, reviews_clean)
        brand_frames.append(merged)
        items_frames.append(items_clean)
        print(f"       items={len(items_clean)}, reviews={len(reviews_clean)}, merged={len(merged)}")

    amazon_df       = pd.concat(brand_frames, ignore_index=True)
    amazon_items_df = pd.concat(items_frames, ignore_index=True)
    print(f"전체 merged: {len(amazon_df)} rows")

    # ── 2. 텍스트 전처리 ───────────────────────────────────────────────────
    if translate:
        print("[translate] 비영어 리뷰 감지 + 번역 중...")
        amazon_df = _detect_and_translate(amazon_df)

    print("[lemmatize] lemmatization 중...")
    amazon_df = lemmatize_reviews(amazon_df)

    print("[ngram] bigram/trigram PMI 계산 중...")
    amazon_df, bigrams, trigrams = build_ngrams(amazon_df)

    # ── 3. Skinsort ────────────────────────────────────────────────────────
    print("[skinsort] 로드 + 전처리 중...")
    skinsort_copy = preprocess_skinsort(load_skinsort())

    # ── 4. 저장 ────────────────────────────────────────────────────────────
    SILVER_AMAZON.mkdir(parents=True, exist_ok=True)
    amazon_df.to_csv(out_reviews,  index=False)
    amazon_items_df.to_csv(out_items,    index=False)
    skinsort_copy.to_csv(out_skinsort, index=False)
    print(f"\nsilver 저장 완료 → {SILVER_AMAZON}")
    print(f"  {out_reviews.name}  ({len(amazon_df)} rows)")
    print(f"  {out_items.name}    ({len(amazon_items_df)} rows)")
    print(f"  {out_skinsort.name} ({len(skinsort_copy)} rows)")


if __name__ == "__main__":
    _overwrite  = "--overwrite"  in sys.argv
    _translate  = "--translate"  in sys.argv
    build_silver(overwrite=_overwrite, translate=_translate)
