# team_folder — 팀 작업 흔적

3 명 공동 팀원 (이니셜 S/H/M) 의 작업 노트북 + 발표 자료 + 데이터 모음. 1/15 ~ 1/28 사이의 시점별 분석 진화 흔적. 각 폴더는 해당 팀원의 담당 파트별 산출물.

## 팀원별 담당 파트 (노트북 markdown 헤더 + 사용 라이브러리로 추론)

| 팀원 | 담당 파트 | 핵심 분석 |
|---|---|---|
| **M** | Amazon 리뷰 분석 + 제품/브랜드 분석 | Sentiment Analysis (TF-IDF), Topic Modeling (LDA), **K-beauty 브랜드 클러스터링**, **성분 기반 제품 속성 분석 (Transformer)** — 0121 노트북 PART 3 ~ PART 4 |
| **H** | 텍스트 전처리 정교화 + EDA + Skinsort 가격 분석 | Data Overview / Handling Missing Values / Column-wise transformation 체계화, LDA + K-beauty 불용어, 명사 필터링, **Word Cloud**, Skinsort `pay_amount` (가격) 분석 — 0128 노트북 |
| **S** | TikTok 인플루언서 `info_tag` 수동 정제 | `cleaned_info.xlsx` (1679 rows × name + info_tag) — TikTok 영상 설명 텍스트 정제 결과. 후속 분석의 input |

## 진화 흐름 (시점 + 팀원별)

```
0115  M  3beaty_최종프로젝트_v1_0115.pptx          ← 발표 시작점
0116  M  Final_Project_삼박자_0116.ipynb           ← 첫 분석 노트북
0121  M  (클러스터링추가)Final_Project_삼박자_0121  ← M 의 마지막 분석 단계
        + 데이터 파일 일반화 (items_0116.csv → items.csv)
        + import 정리 (ast, datetime, re, string, nltk 추가)
        + 클러스터링 분석 추가
0121  H  (중간정리본)..._0121vvvTest                ← H 가 받아 실험 분기
0121  H  삼박자(중간제출용)                         ← 제출용 1차 정리
0121  H  (중간정리본)..._0121(ver5)                 ← ver5 누적 정리
0128  H  3조_분석스크립트_v5_0128(h)               ← 🎯 H 최종 (가장 최신, 494 lines)
        + product_data_path 분리
        + Data Overview / Handling Missing Values / Column-wise transformation 체계화
        + WordNetLemmatizer + ngrams + gensim Phrases
        + preprocess_skinsort_col 함수
       (별개) Test용 코드 v1 copy 2.ipynb         ← test 분기
```

## 폴더 카탈로그

### `M/` — 팀원 M (5 파일, 249MB)

| 파일 | 사이즈 | 역할 |
|---|---|---|
| `Final_Project_삼박자_0116.ipynb` | 6.7M | **시작점**. 1/16. 기본 분석 + sentiment count (po/ne/mi) + items_0116.csv/reviews_0116.csv 로드 |
| `(클러스터링추가)Final_Project_삼박자_0121.ipynb` | 7.3M | **M 의 마지막**. 1/21. 데이터 파일 일반화 + 클러스터링 분석 추가 |
| `3beaty_최종프로젝트_v1_0115.pptx` | 161M | 1/15 발표 자료 (가장 무거움 — 이미지 다수) |
| `기획흐름참고용.pptx` | 76M | 기획 자료 (참고용) |
| `amazon_koreaOnly_translated.csv` | 10M | Amazon 리뷰 한글 번역본 데이터 |

### `H/` — 팀원 H (5 ipynb, 60MB)

| 파일 | 사이즈 | lines (.py) | 역할 |
|---|---|---:|---|
| `(중간정리본)Final_Project_삼박자_0121vvvTest (1).ipynb` | 5.8M | 194 | **0121 실험 분기** (vvvTest = 실험명) |
| `삼박자(중간제출용).ipynb` | 12M | 293 | **0121 제출용** 정리 |
| `(중간정리본)Final_Project_삼박자_0121(ver5).ipynb` | 14M | 303 | **0121 ver5** — 정리 누적 (`Test용` 보다 풍부) |
| `3조_분석스크립트_v5_0128(h).ipynb` | 20M | 494 | **🎯 H 최종 (1/28)** — 가장 최신·풍부. WordNetLemmatizer + ngrams + Phrases. Data Overview / Handling Missing Values / Column-wise transformation 섹션 체계화 |
| `Test용 코드 v1 copy 2.ipynb` | 11M | 171 | **별개 test 분기** (이름이 Test 라 위 진화 흐름과 별도 가지) |

### `S/` — 팀원 S (1 파일, 172KB)

| 파일 | 사이즈 | 역할 |
|---|---|---|
| `cleaned_info.xlsx` | 172K | **TikTok 인플루언서 영상 설명 (`info_tag`) 정제본**. 1679 rows × {name, info_tag}. 영상 설명에서 hashtag (`#kbeauty #koreanskincare #wonyoungism` 등) 추출 가능한 형태. 다른 팀원의 후속 분석 (M 의 토픽 모델링, H 의 텍스트 전처리) input 으로 사용됨 |

## 추천 main

- **분석 final**: `H/3조_분석스크립트_v5_0128(h).ipynb` (가장 최신 + 가장 풍부)
- **발표 자료**: `M/3beaty_최종프로젝트_v1_0115.pptx`
- 나머지는 진화 흔적 (보존)

## 위치 / 정리 메모

이 폴더는 현재 `src/team_folder/` 위치이지만 실제 내용은 **분석 노트북 + 발표 자료** 라 위치가 약간 어색함. 후보 이동 위치:
- `notebooks/team/` (분석 노트북 성격이라 가장 자연스러움)
- `data/archive/team/` (제출용 산출물 모음 성격이면)
- 그대로 `src/team_folder/` 유지 (현재 — 손대지 않음, 별도 결정 시 이동)

PPTX 2 개 (M/, 합계 237MB) 가 폴더 사이즈의 76% 차지. 발표 자료라면 `data/archive/` 가 더 자연스러운 위치 — 별도 정리 시 검토.

## 변종 비교 명령어

```bash
cd src/team_folder
for f in H/*.ipynb M/*.ipynb; do
  out="/tmp/team_$(basename "$f" .ipynb | tr ' ()' '___').summary"
  jupyter nbconvert --to script --stdout "$f" 2>/dev/null \
    | grep -E "^# ###|^# ##|^[a-z_]+ =|^def |^from |^import " > "$out"
done
diff /tmp/team_Final_Project_삼박자_0116.summary /tmp/team__클러스터링추가_Final_Project_삼박자_0121.summary
```

## 관련 docs

- [../../docs/refactor/EXPERIMENTS_PLAYBOOK.md](../../docs/refactor/EXPERIMENTS_PLAYBOOK.md) — 변종 정리 표준 (이 README 가 패턴 C 사례)
- [../../README.md](../../README.md) — 프로젝트 전체
