"""부정어 처리 (Negation Handling) 표준 방법 — Stage 1 ~ Stage 4 함수화.

화장품/뷰티 리뷰의 ``"not sticky"``, ``"no breakout"``, ``"non-comedogenic"`` 같은
부정 표현은 단순 토큰화 시 의미 반전이 사라진다. 이 모듈은 NLP 부정어 처리의
4 가지 표준 방법을 단일 책임 함수로 제공한다.

권장 단계적 적용:

* **Stage 1** — :func:`mark_negation_simple`: NLTK ``mark_negation`` 으로 부정어
  다음 토큰에 ``_NEG`` suffix. 1줄 적용, vocabulary 2배만 늘어 빠르게 효과 측정.
* **Stage 2** — :func:`extract_negation_bigrams`: 부정어 + 다음 1 토큰 bigram
  추출 + PMI / frequency filter. bigram 폭발 방지하면서 의미 있는 부정 표현만.
* **Stage 3** — :func:`apply_domain_negation_rules`: 화장품 도메인 lexicon 기반
  점수 반전 (``"sticky" (-2)`` → ``"not sticky" (+2)``).
* **Stage 4** — :func:`negation_scope_spacy`: SpaCy 의존 구문 분석으로 ``not`` 의
  head 토큰 (negate 대상) 정확히 식별.

이전 시도 (`amazon_tiktok_analysis_ngram_added.ipynb` 의 ``expand_negation`` /
``negation_aware_tokens_long``) 가 점수 안 나온 이유:

* PMI ``freq_filter=30`` 이 너무 높아 부정 bigram 빈도 < 30 이면 누락
* 모든 bigram 사용 시 vocabulary 폭발
* 부정어 scope 정의 없음 → ``"not very sticky"`` 같은 3+ token 부정 누락

→ 이 모듈에서는 단계적 보강 + 단일 책임으로 디버깅 용이하게.
"""

from __future__ import annotations

import re
from typing import Iterable, Sequence

# ---------------------------------------------------------------------------
# 부정어 사전 — 영어
# ---------------------------------------------------------------------------
# Stage 2 / 3 에서 공통 사용. NLTK ``mark_negation`` 의 내부 부정어보다 약간 확장.
NEGATION_WORDS: tuple[str, ...] = (
    "no", "not", "never", "neither", "nor", "none", "nothing", "nobody",
    "n't", "cannot", "without",
    "hardly", "barely", "scarcely", "rarely", "seldom",  # 약한 부정어
)

# 화장품 도메인 specific 부정 표현 — Stage 3 lexicon
# 일반 부정 룰로 잘 안 잡히는 도메인 specific 표현
COSMETIC_NEGATION_PHRASES: dict[str, str] = {
    "non-comedogenic": "POSITIVE_NEG",   # 모공 막지 않음 (positive)
    "non comedogenic": "POSITIVE_NEG",
    "alcohol-free": "POSITIVE_NEG",
    "alcohol free": "POSITIVE_NEG",
    "fragrance-free": "POSITIVE_NEG",
    "fragrance free": "POSITIVE_NEG",
    "redness reducing": "POSITIVE_NEG",
    "anti-aging": "POSITIVE_NEG",
    "anti aging": "POSITIVE_NEG",
    "anti-acne": "POSITIVE_NEG",
    "no breakout": "POSITIVE_NEG",
    "no irritation": "POSITIVE_NEG",
    "no fragrance": "POSITIVE_NEG",
    "no parabens": "POSITIVE_NEG",
}


# ---------------------------------------------------------------------------
# Stage 1 — NLTK mark_negation (가장 단순, 권장 시작점)
# ---------------------------------------------------------------------------
def mark_negation_simple(text: str, *, lowercase: bool = True) -> list[str]:
    """NLTK ``mark_negation`` 으로 부정어 다음 토큰들에 ``_NEG`` suffix 추가.

    부정어 (``"not"``, ``"no"``, ``"n't"`` 등) 다음 토큰들에 ``_NEG`` 를 붙여서
    TF-IDF / LDA / 추천 알고리즘 등이 ``"sticky"`` 와 ``"sticky_NEG"`` 를 다른
    토큰으로 인식하게 한다. 절 종료 (punctuation) 까지 적용.

    Args:
        text: 영어 리뷰 / TikTok 영상 설명 등 원본 텍스트.
        lowercase: 토큰화 전 소문자화 여부 (기본 ``True``).

    Returns:
        ``_NEG`` suffix 가 적용된 토큰 리스트. punctuation 제거됨.

    Example:
        >>> mark_negation_simple("This is not sticky and not greasy.")
        ['this', 'is', 'not', 'sticky_NEG', 'and_NEG', 'not_NEG', 'greasy_NEG']

    Note:
        NLTK ``punkt`` + ``stopwords`` 다운로드 필요 (``nltk.download('punkt')``).
        Vocabulary 가 거의 2배로 늘지만 (X / X_NEG) 단순한 1줄 효과 측정에 적합.
    """
    import nltk
    from nltk.sentiment.util import mark_negation

    if lowercase:
        text = text.lower()
    tokens = nltk.word_tokenize(text)
    # punctuation 제거 (단, mark_negation 은 punctuation 으로 절 경계 인식하므로 미리 제거 X)
    tagged = mark_negation(tokens)
    # 사후 punctuation 제거
    return [t for t in tagged if any(c.isalnum() for c in t)]


# ---------------------------------------------------------------------------
# Stage 2 — Negation-aware bigram + PMI filter (smart filter)
# ---------------------------------------------------------------------------
def extract_negation_bigrams(
    corpus: Sequence[Sequence[str]],
    *,
    top_n_pmi: int = 200,
    min_freq: int = 5,
    negation_words: Iterable[str] = NEGATION_WORDS,
) -> list[tuple[tuple[str, str], float]]:
    """부정어 + 다음 1 토큰 bigram 만 추출 + PMI 점수로 정렬.

    일반 bigram 추출은 vocabulary 폭발 (10K+) 문제 → **부정어를 첫 토큰으로
    가지는 bigram 만** 후보로 좁힘. PMI (Pointwise Mutual Information) 으로
    의미 있는 collocation 만 top_n_pmi 개 추출.

    이전 ``amazon_tiktok_analysis_ngram_added.ipynb`` 의 ``calculate_ngram_pmi``
    가 모든 bigram 대상 ``freq_filter=30`` → 부정 bigram 빈도 낮으면 누락된
    문제 해결.

    Args:
        corpus: 토큰화된 문서 리스트. 각 문서는 토큰 리스트.
        top_n_pmi: PMI 점수 상위 N 개 bigram 만 반환 (기본 200).
        min_freq: bigram 최소 등장 빈도. 너무 높으면 부정 표현 누락 (기본 5).
        negation_words: 부정어 후보. 기본 :data:`NEGATION_WORDS`.

    Returns:
        ``[((negation_word, next_token), pmi_score), ...]`` 형태 list.
        PMI 점수 내림차순 정렬.

    Example:
        >>> corpus = [['not', 'sticky'], ['no', 'breakout'], ['not', 'sticky'],
        ...           ['feels', 'good'], ['not', 'greasy']]
        >>> result = extract_negation_bigrams(corpus, min_freq=2, top_n_pmi=5)
        >>> [b for b, _ in result]  # bigram 순서는 PMI 에 따라 다름
        [('not', 'sticky'), ...]

    Note:
        Stage 1 (mark_negation) 와 결합 가능 — ``_NEG`` suffix 적용 후 추가로
        부정 bigram 도 features 로 사용하면 시너지.
    """
    from collections import Counter

    import numpy as np

    neg_set = set(negation_words)

    # 부정어 + 다음 1 토큰 bigram 만 후보로 (vocabulary 폭발 방지)
    bigram_freq: Counter[tuple[str, str]] = Counter()
    unigram_freq: Counter[str] = Counter()
    total_unigrams = 0

    for doc in corpus:
        for i, tok in enumerate(doc):
            unigram_freq[tok] += 1
            total_unigrams += 1
            if tok in neg_set and i + 1 < len(doc):
                bigram_freq[(tok, doc[i + 1])] += 1

    # min_freq 필터링
    bigram_freq = Counter({b: f for b, f in bigram_freq.items() if f >= min_freq})

    # PMI 계산
    # PMI(x, y) = log( P(x, y) / (P(x) * P(y)) )
    total_bigrams = sum(bigram_freq.values())
    scored: list[tuple[tuple[str, str], float]] = []
    for (w1, w2), f_xy in bigram_freq.items():
        p_xy = f_xy / total_bigrams
        p_x = unigram_freq[w1] / total_unigrams
        p_y = unigram_freq[w2] / total_unigrams
        if p_x == 0 or p_y == 0:
            continue
        pmi = float(np.log2(p_xy / (p_x * p_y)))
        scored.append(((w1, w2), pmi))

    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:top_n_pmi]


# ---------------------------------------------------------------------------
# Stage 3 — 화장품 도메인 lexicon 기반 부정 표현 점수 반전
# ---------------------------------------------------------------------------
def apply_domain_negation_rules(
    text: str,
    *,
    lexicon: dict[str, str] = COSMETIC_NEGATION_PHRASES,
    case_sensitive: bool = False,
) -> str:
    """도메인 specific 부정 표현을 단일 토큰으로 치환.

    일반 부정 룰 (Stage 1) 로 잘 안 잡히는 화장품 도메인 표현 (``non-comedogenic``,
    ``alcohol-free``, ``redness reducing``) 을 lexicon 기반 단일 토큰으로 치환.
    예: ``"This is non-comedogenic and alcohol-free"`` →
    ``"This is POSITIVE_NEG and POSITIVE_NEG"``.

    이렇게 치환하면 TF-IDF / LDA 가 ``"non"`` + ``"comedogenic"`` 별개 토큰으로
    분리하는 대신 도메인 의미 단위로 인식.

    Args:
        text: 원본 텍스트.
        lexicon: 부정 표현 → 치환 토큰 매핑. 기본 :data:`COSMETIC_NEGATION_PHRASES`.
        case_sensitive: 대소문자 구분 여부 (기본 ``False``).

    Returns:
        도메인 부정 표현이 치환된 텍스트.

    Example:
        >>> apply_domain_negation_rules("This product is non-comedogenic and alcohol-free.")
        'This product is POSITIVE_NEG and POSITIVE_NEG.'

    Note:
        Stage 1 + Stage 3 결합 권장 — 일반 부정 (``"not sticky"``) 은 Stage 1,
        도메인 표현 (``"non-comedogenic"``) 은 Stage 3.
    """
    flags = 0 if case_sensitive else re.IGNORECASE
    result = text
    # 긴 phrase 부터 매칭 (greedy 매칭 방지) — non-comedogenic 이 non 보다 먼저
    for phrase in sorted(lexicon.keys(), key=len, reverse=True):
        pattern = re.compile(r"\b" + re.escape(phrase) + r"\b", flags=flags)
        result = pattern.sub(lexicon[phrase], result)
    return result


# ---------------------------------------------------------------------------
# Stage 4 — SpaCy dependency parsing 기반 negation scope 식별 (정밀)
# ---------------------------------------------------------------------------
def negation_scope_spacy(
    text: str,
    *,
    spacy_model: str = "en_core_web_sm",
    suffix: str = "_NEG",
) -> list[str]:
    """SpaCy 의존 구문 분석으로 부정어가 수식하는 head 토큰 정확히 식별.

    Stage 1 의 ``mark_negation`` 은 부정어 다음 토큰들을 모두 ``_NEG`` 처리하지만
    실제로는 부정어가 수식하는 단일 head 노드만 부정 의미. 예:

    * ``"This is not very sticky"`` — Stage 1: ``not`` 다음 ``very_NEG sticky_NEG``
      모두 부정 처리. Stage 4: ``not`` 의 head 가 ``sticky`` 라 ``sticky_NEG`` 만.

    SpaCy 의 ``token.dep_ == 'neg'`` 로 부정 의존 관계 식별 → ``token.head`` 가
    부정 대상 noun/adj/verb.

    Args:
        text: 원본 텍스트.
        spacy_model: 사용할 SpaCy 모델 (기본 ``en_core_web_sm`` — 별도 설치 필요:
            ``python -m spacy download en_core_web_sm``).
        suffix: 부정 head 토큰에 붙일 suffix (기본 ``"_NEG"``).

    Returns:
        ``_NEG`` 가 적용된 토큰 리스트 (lemma form, punctuation 제거).

    Example:
        >>> negation_scope_spacy("This is not very sticky.")
        # ['this', 'be', 'not', 'very', 'sticky_NEG']
        # → 'sticky' 만 _NEG (not 의 의존 head)

    Note:
        Stage 1 보다 정밀하지만 SpaCy 모델 로드 비용 (수초). 큰 코퍼스에 적용 시
        ``nlp.pipe()`` batch 사용 권장.
    """
    import spacy

    try:
        nlp = spacy.load(spacy_model)
    except OSError as e:
        raise RuntimeError(
            f"SpaCy 모델 '{spacy_model}' 미설치. "
            f"설치: python -m spacy download {spacy_model}"
        ) from e

    doc = nlp(text)
    # 부정 의존 관계 식별 → head 토큰 indices 수집
    neg_heads: set[int] = set()
    for token in doc:
        if token.dep_ == "neg":
            neg_heads.add(token.head.i)

    # 토큰 lemma form 으로 출력 + neg_heads 인덱스에 suffix
    result: list[str] = []
    for token in doc:
        if not token.is_alpha:
            continue
        lemma = token.lemma_.lower()
        if token.i in neg_heads:
            lemma = lemma + suffix
        result.append(lemma)
    return result


# ---------------------------------------------------------------------------
# 통합 파이프라인 — Stage 1 + Stage 3 결합 (실용 권장)
# ---------------------------------------------------------------------------
def negation_aware_pipeline(
    text: str,
    *,
    apply_domain_lexicon: bool = True,
    lexicon: dict[str, str] = COSMETIC_NEGATION_PHRASES,
) -> list[str]:
    """Stage 1 (mark_negation) + Stage 3 (도메인 lexicon) 결합 파이프라인.

    실용적 권장 조합. 일반 부정 (Stage 1) + 화장품 도메인 부정 표현 (Stage 3)
    을 한 함수로 처리. SpaCy 같은 무거운 의존성 없이 NLTK 만으로 동작.

    Args:
        text: 원본 텍스트.
        apply_domain_lexicon: 도메인 lexicon 적용 여부 (기본 ``True``).
        lexicon: 도메인 부정 표현 매핑.

    Returns:
        부정어 처리된 토큰 리스트.

    Example:
        >>> negation_aware_pipeline("This is not sticky and non-comedogenic.")
        # 1) 도메인 치환: "This is not sticky and POSITIVE_NEG."
        # 2) Stage 1: ['this', 'is', 'not', 'sticky_NEG', 'and_NEG', 'positive_neg_NEG']
        # → and_NEG, positive_neg_NEG 는 Stage 1 의 over-marking. 후처리 필요 시 stop word 처리.
    """
    # 도메인 lexicon 먼저 (긴 phrase 가 먼저 잡혀야 함)
    if apply_domain_lexicon:
        text = apply_domain_negation_rules(text, lexicon=lexicon)
    # NLTK Stage 1 적용
    return mark_negation_simple(text)
