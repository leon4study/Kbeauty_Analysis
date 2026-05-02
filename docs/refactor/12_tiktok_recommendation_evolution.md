# TikTok 추천 알고리즘 진화

`tiktoker_recommend.ipynb` 한 노트북 안에서 **ver.1 → ver.2 → ver.3 → 회귀분석** 4단계로 추천 알고리즘이 진화한 흔적. [EXPERIMENTS_PLAYBOOK](EXPERIMENTS_PLAYBOOK.md) 패턴 A (단일 파일 + 주석 진화) 의 자연스러운 사례 — 변종이 별도 파일로 흩어지지 않고 한 노트북 안 셀로 누적되어 있어서 정리 작업 없이 이미 통폐합된 형태.

## 배경 / 의도

K-beauty 인플루언서 (틱톡커) 마케팅에서 "비슷한 인플루언서 추천" + "광고 ROI 가 높을 인플루언서 선정" 을 하기 위한 콘텐츠 기반 필터링 추천 시스템 구축. 기존 캠페인 인플루언서 (예: `krystallee2222`, `emchu_`) 와 콘텐츠 토픽이 유사한 인플루언서 top-N 을 추천하는 게 1차 목표.

## 진화 흐름

### Stage 1: 데이터 전처리

원본 `tiktoker_crawling_df_0127.csv` (인플루언서별 영상 row) 를 정제:

- **단위 변환**: `view_cnt`, `like_cnt`, `comment_cnt`, `save_cnt` 의 `k`/`m` 표기 → 숫자
- **날짜 정규화**: `1d ago`, `2w ago` 등 상대 표기 → `2025-01-21` 기준 절대 날짜
- **해시태그 추출**: `info` 컬럼에서 `#tag` 정규식 추출 → `hash_tag` 컬럼 재생성
- **자연어 처리**: NLTK tokenize + stopwords 제거

### Stage 2: 피처 엔지니어링 → `merged_mean_0207.csv`

인플루언서 단위 (mean_df) 로 집계 + 파생 피처 계산:

| 피처 | 공식/방법 | 의미 |
|---|---|---|
| `ad_cost` | `view_cnt * 20000` | 평균 조회수 × 2만 = 추정 광고 단가 (KRW) |
| `ER%` | `(like_cnt + comment_cnt) / follower_cnt * 100` | Engagement Rate — 인플루언서 콘텐츠 참여율 |
| `influencer_size` | 팔로워 수 기반 카테고리 (nano/micro/macro 등) | 광고 단가 협상 기준 |
| `avg_upload_interval` | name 별 업로드 날짜 diff 평균 | 활동 빈도 |
| `no.1, no.2, no.3` | `tiktoker_top3_modeled_topic.csv` 의 토픽 모델 top3 태그 merge | 콘텐츠 카테고리 (color/skincare/hair_body/fashion/unboxing/skin_routine/trend/asmr/eating/others) |

### Stage 3: 추천 알고리즘 ver.1 → v2 → v3 (Content-based filtering)

| 버전 | 변경점 | 의도 |
|---|---|---|
| **ver.1** | TF-IDF + cosine similarity. 콘텐츠 키워드 가중치 `no.1*3 + no.2*2 + no.3*1` | 가장 중요한 토픽 (no.1) 에 더 큰 가중치 |
| **ver.2** | ver.1 + ER% MinMax 정규화 → 키워드 반복 횟수에 곱셈 | 참여율 높은 인플루언서의 콘텐츠 키워드를 TF-IDF 에 더 강하게 반영 |
| **ver.3** | ver.2 + `max(1, ...)` 안전장치 | ER% 너무 낮을 때 키워드가 0번 반복되어 삭제되는 문제 보정 |

공통 알고리즘:
1. `content_features` 컬럼 = `no.1, no.2, no.3` 토픽을 가중치만큼 반복한 텍스트
2. `TfidfVectorizer().fit_transform(content_features)` → 인플루언서별 TF-IDF 벡터
3. 기존 캠페인 인플루언서 (selected_influencers) 의 TF-IDF 벡터와 cosine similarity
4. 평균 유사도 점수로 정렬 → top-N 추천

**왜 cosine similarity?** TF-IDF 결과는 고차원 희소 벡터 + 인플루언서별 콘텐츠 길이 차이 큼 → 벡터 방향만 비교하는 cosine 이 적합 (유클리드/jaccard/dot product 보다).

**왜 ER% 가중치를 v2 에서 추가?** ROI 관점 — ER% 높은 인플루언서가 광고 효율 높음 → 그들의 콘텐츠 토픽을 더 중요하게 다뤄야 함.

### Stage 4: 회귀분석 (가중치 자동 탐색)

ver.1~3 의 가중치 (`no.1*3 + no.2*2 + no.3*1`, ER% scaling 배수) 는 사람이 정한 heuristic. 회귀분석으로 데이터 기반 가중치를 찾는 시도:

**파생 변수 추가**:
- `like_ratio = like_cnt / view_cnt`, `comment_ratio = comment_cnt / view_cnt`, `save_ratio = save_cnt / view_cnt`
- `FSR = save_cnt / follower_cnt` (Follower-to-Save Ratio)
- `EPV = (like + comment + save) / view_cnt` (Engagement per View)
- `response_rate = (like + comment + save) / ad_cost`

**다중공선성 처리**: VIF 계산 후 `ad_cost`, `view_cnt`, `like_cnt`, `comment_cnt`, `save_cnt`, `response_rate`, `FSR`, `EPV` 제거 (서로 강한 상관).

**모델**: `LinearRegression` 으로 `ER%` 를 종속변수, `[like_ratio, comment_ratio, save_ratio, follower_cnt, avg_upload_interval]` 을 독립변수로 학습 → 회귀 계수 = 광고 ROI 가중치 후보.

**평가**: `MAE`, `R²`. 

**미완성 메모**: 노트북 끝에 `(예상 수익 - 투자 비용) / 투자 비용 * 100 = ROI%` ROI 계산 + "틱톡커 과거 ROI 가 있다면 그걸 종속변수로 회귀해서 ROI 예측 가능" 아이디어 적혀있음. 실제 ROI 데이터가 없어서 ER% 를 proxy 로 사용한 단계까지.

## 정성 검증 흔적

기존 캠페인 인플루언서 `["krystallee2222", "emchu_"]` 기준으로 ver.1, v2 의 추천 결과 출력. 노트북 셀 주석:
> krystallee2222 ER 높고 > 피부가 좋아서 신빙성 있음... emchu_ 컨셉

→ 정량 metric (cosine similarity) 외에 도메인 지식 기반 정성 검증을 같이 한 흔적.

## canonical 위치

```
notebooks/tiktok/tiktoker_recommend.ipynb     (이전: src/tiktok_recommendation/)

data/tiktok/
├── tiktoker_final_df_0127.csv               (입력: 영상 단위 원본)
├── tiktoker_top3_modeled_topic.csv          (입력: 토픽 모델링 결과)
└── merged_mean_0207.csv                     (Stage 2 출력: 인플루언서 단위 + 파생 피처)
```

## 학습 포인트

1. **변종을 별도 파일로 흩지 말고 한 노트북 안 셀로 누적** 하면 자연스럽게 통합된 진화 흔적이 남음 — `_v2.ipynb`, `_v3.ipynb` 식으로 파일 5개 만드는 것보다 미래의 본인이 한 번에 봄.
2. **v1 → v2 의 차이 (ER% 가중치 추가)** 는 도메인 통찰 (ROI 관점) 에서 나옴. 단순 metric 개선이 아니라 비즈니스 가설 검증 단계로 의미 있음.
3. **v2 → v3 의 `max(1, ...)` 안전장치** 는 실제 분포에서 발견한 edge case 보정. 가중치 시스템 만들 때 정규화 결과 0 이 되는 케이스를 항상 의심해야 함.
4. **회귀분석으로 가중치 자동 탐색** 은 heuristic → 데이터 기반 자연스러운 다음 단계. ROI 같은 진짜 종속변수가 없으면 ER% proxy 로 시작.
5. **ipynb 출력 셀 손상 위험** 때문에 50M+ 노트북의 변종 통합은 어려움. tiktoker_recommend 처럼 처음부터 한 노트북에 셀 단위로 두면 통합 비용 0.

## 위치 변경 노트

이전 위치 `src/tiktok_recommendation/` (모듈 형태) → 현재 `notebooks/tiktok/tiktoker_recommend.ipynb` + `data/tiktok/*.csv` (분석 노트북 + 데이터). 
이유: 모듈이라 부르기엔 노트북 1개 + csv 3개 형태였고, src 가 아니라 notebooks/data 가 자연스러운 자리. [11_project_code_dissolution.md](11_project_code_dissolution.md) 의 canonical 위치 그림은 이 변경 이전 (그 시점 truth) 을 반영.

## 관련 commits

- `9149705` — refactor: relocate tiktok_recommendation/ → notebooks/tiktok/
- `498d89e` (revert) — 같은 작업의 첫 시도 (untracked 사용자 파일이 같이 끌려와서 reset 후 재commit)
