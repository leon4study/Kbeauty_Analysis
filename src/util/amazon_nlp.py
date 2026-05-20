"""
File: src/util/amazon_nlp.py

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
무엇인가 (What)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Amazon 리뷰 텍스트 전처리에 공통으로 쓰이는 NLP 헬퍼 모음. clean_text /
tokenize_text / remove_stopwords / stem_tokens / lemmatize_tokens /
bigram_filter / trigram_filter / replace_ngram 8 개 함수.

왜 있는가 (Why)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
*1) notebooks/amazon/01, 02, 03 세 노트북에 동일 함수가 중복 정의돼 있었음.*
   - clean_text / tokenize_text / stem_tokens: 01 + 02 동일
   - replace_ngram: 03 노트북 12 cell 에 *복붙* (cells 48/64/69/74/79/84/89/93/98/103/108/113)
   같은 버그 수정 시 12+곳 동시 수정 필요 = 유지보수 악몽.

*2) 옛 구현은 stop_words / bigrams / trigrams / stemmer / lemmatizer 같은
   *전역 변수에 의존* 했음.* 함수만 import 해도 동작 X (전역 없음).
   → 이 모듈은 *명시적 인자* 로 받아 self-contained:
     ``remove_stopwords(tokens, stop_words)`` 처럼.
   호출부 변경량 작음 + 함수가 isolated 단위 검증 가능.

*3) 옛 ``remove_stopwords`` 가 01 은 ``stop_words``, 02 는 ``custom_stopwords``*
   *전역 변수 의존이라 같은 함수명이지만 다른 동작.* 인자화 시 *한 함수로 통합*
   가능 — 어느 set 전달하는지가 명시적.

어디에 쓰이는가 (Where)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- ``notebooks/amazon/01_amazon_preprocessing.ipynb`` — 5브랜드 리뷰 전처리
- ``notebooks/amazon/02_amazon_eda.ipynb`` — silver 소비 + EDA
- ``notebooks/amazon/03_amazon_topic_modeling.ipynb`` — LDA 토픽 모델 (replace_ngram
  반복 사용)
- ``src/util/negation.py`` 와 별개 (negation 은 *부정 표현 정규화* 4단계 파이프라인.
  이 모듈은 *기본* 텍스트 전처리)

사용법 (How)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    import sys
    from pathlib import Path
    REPO_ROOT = next(p for p in [Path.cwd().resolve()] + list(Path.cwd().resolve().parents)
                     if (p / ".git").is_dir())
    sys.path.insert(0, str(REPO_ROOT / "src"))
    from util.amazon_nlp import (
        clean_text, tokenize_text, remove_stopwords,
        stem_tokens, lemmatize_tokens,
        bigram_filter, trigram_filter, replace_ngram,
    )

    # NLTK + custom stopwords set 준비 (호출부에서)
    from nltk.corpus import stopwords as nltk_stopwords
    from nltk.stem import PorterStemmer, WordNetLemmatizer
    stop_words = set(nltk_stopwords.words("english"))
    stemmer, lemmatizer = PorterStemmer(), WordNetLemmatizer()

    # 파이프라인
    df["cleaned"]   = df["review_content"].apply(clean_text)
    df["tokenized"] = df["cleaned"].apply(tokenize_text)
    df["no_stop"]   = df["tokenized"].apply(lambda t: remove_stopwords(t, stop_words))
    df["stemmed"]   = df["no_stop"].apply(lambda t: stem_tokens(t, stemmer))
    df["lemm"]      = df["no_stop"].apply(lambda t: lemmatize_tokens(t, lemmatizer))

    # n-gram 치환 (bigrams/trigrams 는 gensim Phrases 등에서 얻은 리스트)
    df["with_ngram"] = df["lemm"].apply(
        lambda x: replace_ngram(x, bigrams, trigrams) if isinstance(x, str) else x
    )

설계 노트
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- *모든 함수는 입력이 예상 타입 아닐 때 입력 그대로 반환* — 옛 노트북의 동작
  보존 (NaN / None / list-not-str 같은 mixed dtype DataFrame 컬럼 안전 처리).
- *Stateless* — 호출 간 의존 없음. 같은 입력 → 같은 출력. 단위 검증 용이.
- *Stop_words / stemmer / lemmatizer / bigrams / trigrams 는 모두 명시적 인자*
  — 전역 의존 제거.

관련 파일 (Related)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- src/util/negation.py  ← 부정 표현 정규화 (별개 도메인)
- src/util/tiktok_metrics.py  ← TikTok 도메인 헬퍼 (이 모듈과 패턴 동일)
- docs/refactor/18_vectorization_and_constants.md  ← 같은 정신의 util 추출 사례
"""
from __future__ import annotations

import re
import string
from typing import Any

import nltk
from nltk.tokenize import word_tokenize


# ─────────────────────────────────────────────────────────────────────────────
# 1. 기본 텍스트 정제
# ─────────────────────────────────────────────────────────────────────────────


def clean_text(text: Any) -> Any:
    """소문자 변환 + URL/markdown link/@mention/구두점 제거.

    무엇 (What)
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    Amazon 리뷰 / Skinsort 성분 텍스트의 가장 첫 단계 정제. URL, markdown
    링크, @mention, 구두점 제거 + 소문자 통일.

    왜 있는가 (Why)
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    노트북 01 + 02 에 동일 함수가 *중복 정의* 됨 (빈 줄만 다름, 로직 100% 동일).
    util 로 추출 → 한 곳 수정 시 모든 호출부 자동 반영.

    언제 호출하나 (When)
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    - 텍스트 컬럼 (review_content, title, ingredients) 의 *가장 먼저* 전처리.
    - 이후 ``tokenize_text`` → ``remove_stopwords`` → ``stem/lemmatize`` 순.

    Args:
        text: 정제할 문자열. str 아니면 (NaN 등) 입력 그대로 반환.

    Returns:
        정제된 lowercase 문자열 또는 원본 (str 아닐 때).

    Note:
        - punctuation 제거에 ``str.maketrans`` 사용 — char-by-char replace 보다 빠름.
        - URL/markdown 정규식 순서는 의도적: markdown ``[text](url)`` 가 그냥 URL
          제거보다 *먼저* 잡혀야 ``[text]`` 부분이 살아남음.

    Examples:
        >>> clean_text("Check out https://x.com #great product!!")
        'check out  great product'
        >>> clean_text("[link](url) hi")
        ' hi'
        >>> clean_text(None)  # NaN safe
        None
    """
    if isinstance(text, str):
        text = text.lower()
        # URL 제거.
        text = re.sub(r"http\S+|www\S+|https\S+", "", text, flags=re.MULTILINE)
        # markdown 스타일 링크 ``[text](url)`` 제거 — 전체 패턴 통째 삭제.
        text = re.sub(r"\[.*?\]\(.*?\)", "", text)
        # @mention 제거.
        text = re.sub(r"@\w+", "", text)
        # 구두점·특수문자 제거 (``str.maketrans`` 가 char-by-char 보다 빠름).
        text = text.translate(str.maketrans("", "", string.punctuation))
        return text
    return text


# ─────────────────────────────────────────────────────────────────────────────
# 2. 토큰화 / Stopword / Stem / Lemmatize
# ─────────────────────────────────────────────────────────────────────────────


def tokenize_text(text: Any) -> Any:
    """NLTK ``word_tokenize`` 로 문자열 → 토큰 list.

    무엇 (What)
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    ``clean_text`` 결과 문자열을 단어 단위 token list 로 분할.

    왜 있는가 (Why)
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    노트북 01 + 02 에 동일 함수 중복. ``word_tokenize`` 가 *단순 split 보다 더
    영리* (don't → "do", "n't" 등) — punctuation tokenization rule 적용.

    언제 호출하나 (When)
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    ``clean_text`` 결과에 대해. ``remove_stopwords`` 직전.

    Args:
        text: 토큰화할 문자열. str 아니면 입력 그대로.

    Returns:
        token list (예: ``["hello", "world"]``) 또는 원본.

    Note:
        ``nltk.download('punkt')`` 가 사전에 호출돼야 함 (호출부 책임).
    """
    if isinstance(text, str):
        return word_tokenize(text)
    return text


def remove_stopwords(tokens: Any, stop_words: set | list) -> Any:
    """token list 에서 stopword 제거.

    무엇 (What)
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    list 안의 각 token 이 ``stop_words`` 에 *없는* 것만 남김. set 검색이 O(1)
    이라 list 검색보다 빠름 — 가능하면 set 으로 넘김.

    왜 있는가 (Why)
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    *옛 노트북 01 vs 02 의 ``remove_stopwords`` 함수가 같은 이름이지만 다른
    전역 변수 의존* (01 ``stop_words``, 02 ``custom_stopwords``) — 같은 함수
    명이 다른 동작이라 혼동. 인자화 시 *한 함수로 통합* + 어느 set 쓰는지 명시.

    언제 호출하나 (When)
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    ``tokenize_text`` 직후. ``stem_tokens`` / ``lemmatize_tokens`` 직전.

    Args:
        tokens: 토큰 list. list 아니면 입력 그대로.
        stop_words: 제거할 단어 set 또는 list. set 권장 (O(1) 검색).

    Returns:
        stopword 제거된 token list 또는 원본.

    Examples:
        >>> remove_stopwords(["this", "is", "good"], {"is", "the"})
        ['this', 'good']
    """
    if isinstance(tokens, list):
        return [word for word in tokens if word not in stop_words]
    return tokens


def stem_tokens(tokens: Any, stemmer: Any) -> Any:
    """각 token 을 stemmer 로 어간 추출 (예: ``running`` → ``run``).

    무엇 (What)
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    PorterStemmer 등 stemmer 의 ``.stem(token)`` 을 모든 token 에 적용.

    왜 있는가 (Why)
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    옛 노트북에서 ``stemmer`` 전역 의존. 인자로 받으면:
    - 다른 stemmer (Snowball, Lancaster 등) 교체 가능
    - test 시 mock stemmer 주입 가능

    Args:
        tokens: 토큰 list. list 아니면 입력 그대로.
        stemmer: NLTK Stemmer 객체 (``.stem(word) → str`` 인터페이스).

    Returns:
        stem 처리된 token list 또는 원본.

    Note:
        Stemming 은 lemmatization 보다 빠르지만 *덜 정확* (예: ``ponies`` →
        ``poni``). 정확도 중요한 LDA / sentiment 분석은 ``lemmatize_tokens`` 권장.
    """
    if isinstance(tokens, list):
        return [stemmer.stem(token) for token in tokens]
    return tokens


def lemmatize_tokens(tokens: Any, lemmatizer: Any) -> Any:
    """각 token 을 lemmatizer 로 표제어 추출 (예: ``ponies`` → ``pony``).

    무엇 (What)
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    WordNetLemmatizer 등 lemmatizer 의 ``.lemmatize(token)`` 을 모든 token 에
    적용. Stemming 보다 문법적으로 정확한 어형 복원.

    왜 있는가 (Why)
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    옛 노트북 ``lemmatizer`` 전역 의존. 명시적 인자로 받아 호출부 의도 명확화.

    Args:
        tokens: 토큰 list.
        lemmatizer: WordNetLemmatizer 등. ``.lemmatize(word) → str`` 인터페이스.

    Returns:
        lemma 처리된 token list 또는 원본.

    Note:
        ``nltk.download('wordnet')`` 사전 호출 필요.
    """
    if isinstance(tokens, list):
        return [lemmatizer.lemmatize(token) for token in tokens]
    return tokens


# ─────────────────────────────────────────────────────────────────────────────
# 3. N-gram 필터 + 치환
# ─────────────────────────────────────────────────────────────────────────────


def bigram_filter(bigram: tuple[str, str], stop_words: set | list) -> bool:
    """noun-phrase 형태의 bigram 만 통과시키는 필터.

    무엇 (What)
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    bigram (단어 2개 튜플) 이 *유의미한 noun phrase* 인지 판단:
    - 첫 단어: 형용사 (JJ) 또는 명사 (NN)
    - 둘째 단어: 명사 (NN)
    - 양쪽 모두 stopword 아님 + 단일 letter (n / t) 아님 + 대명사 (PRON) 아님

    왜 있는가 (Why)
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    ``gensim.models.Phrases`` 결과 bigram 후보 중 *의미 있는 명사구* 만
    채택하려고. 예: ``"hyaluronic acid"`` ✓, ``"is good"`` ✗.

    언제 호출하나 (When)
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    Phrases 후보 → ``filter()`` 또는 list comprehension 안에서.

    Args:
        bigram: 단어 2개 튜플 (``("hyaluronic", "acid")`` 등).
        stop_words: 제외할 stopword set/list.

    Returns:
        True 면 noun phrase, False 면 제외.

    Note:
        ``nltk.pos_tag`` 사전 호출 필요. 영어 기준.
    """
    tag = nltk.pos_tag(bigram)
    if tag[0][1] not in ["JJ", "NN"] and tag[1][1] not in ["NN"]:
        return False
    if bigram[0] in stop_words or bigram[1] in stop_words:
        return False
    if "n" in bigram or "t" in bigram:
        return False
    if "PRON" in bigram:
        return False
    return True


def trigram_filter(trigram: tuple[str, str, str], stop_words: set | list) -> bool:
    """noun-phrase 형태의 trigram 만 통과시키는 필터.

    Args:
        trigram: 단어 3개 튜플.
        stop_words: 제외할 stopword set/list.

    Returns:
        True 면 noun phrase, False 면 제외.

    Note:
        bigram_filter 의 trigram 버전 — 첫 둘 다 JJ/NN 이어야 + 셋 다 stopword
        아닌 추가 조건.
    """
    tag = nltk.pos_tag(trigram)
    if tag[0][1] not in ["JJ", "NN"] and tag[1][1] not in ["JJ", "NN"]:
        return False
    if trigram[0] in stop_words or trigram[-1] in stop_words or trigram[1] in stop_words:
        return False
    if "n" in trigram or "t" in trigram:
        return False
    if "PRON" in trigram:
        return False
    return True


def replace_ngram(x: str, bigrams: list[str], trigrams: list[str]) -> str:
    """문자열 안 bigram/trigram 을 underscore-joined 단일 토큰으로 치환.

    무엇 (What)
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    ``"hyaluronic acid moisturizer"`` 안의 ``"hyaluronic acid"`` 를 검출해
    ``"hyaluronic_acid moisturizer"`` 로 만듦. LDA / TF-IDF 에서 multi-word
    개념을 *단일 token* 으로 다루기 위함.

    왜 있는가 (Why)
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    *옛 ``notebooks/amazon/03`` 노트북 12 cell 에 동일 함수가 복붙* (cells
    48/64/69/74/79/84/89/93/98/103/108/113 — 100% 동일 hash). 같은 버그 수정
    시 12 곳 수정. util 추출 시 1 곳.
    옛 구현은 ``bigrams``/``trigrams`` 전역 의존. 명시적 인자로 받아 호출부
    의도 명확화.

    언제 호출하나 (When)
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    Lemmatize 후, LDA 토픽 모델링 *직전* 단계.
    *trigram 먼저 치환 후 bigram* — 순서 중요! "great natural ingredient" 가
    trigram 매칭되면 그것 우선, 안 되면 bigram ("great natural" + "ingredient")
    시도.

    Args:
        x: 치환할 문자열 (lemmatize 결과).
        bigrams: bigram 문자열 리스트 (예: ``["hyaluronic acid", ...]``).
            공백 구분 2 단어 형식.
        trigrams: trigram 문자열 리스트. 공백 구분 3 단어 형식.

    Returns:
        bigram/trigram 이 underscore-joined 된 결과 문자열.

    Examples:
        >>> replace_ngram(
        ...     "hyaluronic acid is great",
        ...     bigrams=["hyaluronic acid"],
        ...     trigrams=[],
        ... )
        'hyaluronic_acid is great'

    Note:
        - 단순 ``str.replace`` 라 substring 매칭이 *전체 단어 경계* 무시.
          ``"hyaluronic acids"`` 도 ``"hyaluronic_acids"`` 됨. 원본 동작 보존.
        - 호출부에서 빈 리스트 ``[]`` 넘기면 그쪽 단계 skip.
    """
    for gram in trigrams:
        x = x.replace(gram, "_".join(gram.split()))
    for gram in bigrams:
        x = x.replace(gram, "_".join(gram.split()))
    return x
