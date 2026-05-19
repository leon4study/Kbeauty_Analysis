# `src/project_code/` 해체

이름부터 모호한 catch-all 디렉터리 `src/project_code/` 를 통째로 해체해서, 안 내용을 의미 단위로 분산.

## 배경 / 의도

`src/project_code/` 는 "프로젝트 코드" 라는 뜻으로 보이지만, src/ 자체가 이미 "프로젝트 코드 디렉터리" 라서 이름이 redundant + nondescript. 안에 들어있던 것:

```
src/project_code/
├── fake_data_gen/        (39 lines — fake_data_gen 모듈 일부)
├── temp/                 (9 파일, 6.3MB — 임시/실험 코드)
├── tiktok/               (TikTok 관련 일부 — test, 0130 데이터)
└── tokenize_test/        (lemmatized_test.ipynb 1개, 19MB)
```

→ 4개 카테고리가 섞여있고 의미 분리도 흐림.

## 분류 작업

### temp/ (9 파일) — 명백 분류

| 파일 | 평가 | 처분 |
|------|------|------|
| `new.py` (0줄, 빈 파일) | dead | ❌ 폐기 |
| `temp2.ipynb` (43 cells, BeautifulSoup 시도) | 임시 sketch | ❌ 폐기 |
| `csv_to_sql.py` (36줄, `from mysql1 import` — 이미 폐기된 모듈 사용) | 옛 마이그레이션 도구 학습 자료 | → `~/GitStudy/utils/legacy_crawlers/` |
| `selenium_new_proxy.py` (69줄, Selenium + 프록시) | 프록시 패턴 학습 자료 | → `legacy_crawlers/` |
| `ex_crawling.py` (61줄, tkinter + Selenium GUI 예제) | GUI 크롤러 패턴 학습 | → `legacy_crawlers/` |
| `crawling1.py` (104줄, Selenium 크롤링 시도) | 크롤링 패턴 | → `legacy_crawlers/` |
| `testMainCategory.py` (581줄, Amazon 카테고리 탐색) | 큰 파일이지만 standalone 시도 | → `legacy_crawlers/` |
| `amazon_csv_read.ipynb` (31 cells) | Amazon CSV 읽기 시도 | → `~/GitStudy/utils/legacy_notebooks/` |
| `(중간정리본)Final_Project_삼박자_0121(ver2) copy 2.ipynb` (133 cells) | 옛 정리본 변종 (이름에 `copy 2`) | → `legacy_notebooks/Final_Project_삼박자_0121_ver2.ipynb` (이름 정리) |

### tiktok/ — 데이터 + 1 노트북

| 항목 | 내용 | 처분 |
|------|------|------|
| `tiktok_test_data.ipynb` (10 cells) | TikTok 시도, "test" 이름 | → `legacy_notebooks/` |
| `0130/cleaned_info.xlsx` | 1월 30일자 cleaned 데이터 | → `data/tiktok/cleaned_info_0130.xlsx` |
| `0130/results/` (251 LDA HTML) | 틱톡커별 토픽 모델링 결과 (LDA 시각화) | → `data/tiktok/lda_per_tiktoker_0130/` |
| `tiktoker_topic_modeling/` (빈 폴더) | — | ❌ 폐기 |

### fake_data_gen/ — `src/fake_data_gen/` 와 통합
자세한 분석: [10_fake_data_gen.md](10_fake_data_gen.md)

### tokenize_test/lemmatized_test.ipynb — 의외의 발견 ⭐

이름은 "test" 인데 cells 193개. 마크다운 헤더 분석:
```
# 삼박자 - 최종 프로젝트
# PART 1: Data Preprocessing
## Import library & Load data
## Data Cleaning
### Text preprocessing
# PART 2: EDA
## Visualization
### Word Cloud
# PART 3: Data Analysis
## ◼ Amazon
### Sentiment Analysis
## ■ Skinsort
### Sentiment Analysis
```

→ "test" 이름을 가진 채로 사실상 **메인 분석 노트북**! Pre-processing → EDA → Sentiment Analysis 까지 풀 파이프라인.

처분: `notebooks/lemmatized_full_pipeline.ipynb` 로 **승격** + stale path 정리:
- `Data_4/Data/project/project5/gdrive/2.데이터/dataset/Product/` → `from util.repo_paths import AMAZON; os.chdir(AMAZON)` (canonical, gdrive 백업이 아닌 정식 위치)

## 처리 사고 — `rm -rf` 실수 후 복구

`git mv` 가 repo 외부 (`~/GitStudy/utils/`) 로는 이동 못함 → `mv` fallback 으로 보내려고 했으나 `||` chain 미스로 fallback 안 작동. 그 상태에서 `rm -rf src/project_code/` 가 **이동 안 된 파일들도 함께 삭제**.

복구 절차 (git 가 history 에 다 가지고 있어서 가능):
```bash
mkdir -p src/project_code/temp src/project_code/tiktok
git checkout HEAD -- <삭제된 파일들 명시적 나열>
# 그 다음 정상 절차로 다시 이동: cp → git rm → mv
```

**교훈**: shell `||` 와 `pipe + tail` 조합은 함정. `pipe | tail -1` 의 exit status 는 항상 0 → `||` 가 트리거 안 됨. 안전하려면 별도 변수에 status 저장하거나 처음부터 python 같은 더 명시적인 도구.

## canonical 위치

```
src/                                   (project_code 사라짐)
├── amazon_review_crawler/
├── fake_data_gen/                     (project_code 의 fake_data_gen 통합됨)
├── rag_chatbot/
├── tiktok_crawler/
├── tiktok_recommendation/
└── util/
                                       (team_folder/ 는 후속 정리에서
                                        data/archive/team_folder/ 로 이동 — archive 성격 명확화)

notebooks/lemmatized_full_pipeline.ipynb   (project_code 에서 승격)

data/tiktok/cleaned_info_0130.xlsx
data/tiktok/lda_per_tiktoker_0130/         (251 HTML)
```

## 학습 노트 보존 위치

```
~/GitStudy/utils/
├── legacy_crawlers/                   (5개 selenium 시도)
│   ├── csv_to_sql.py
│   ├── selenium_new_proxy.py
│   ├── ex_crawling.py
│   ├── crawling1.py
│   └── testMainCategory.py
└── legacy_notebooks/                  (3개 옛 노트북)
    ├── amazon_csv_read.ipynb
    ├── tiktok_test_data.ipynb
    └── Final_Project_삼박자_0121_ver2.ipynb
```

## 학습 포인트

1. **모호한 카테고리 이름은 매몰 비용**: `project_code/` 같은 nondescript 폴더는 시간이 지날수록 catch-all 로 변함. 처음부터 의미 있는 이름.
2. **이름과 실체 불일치는 큰 함정**: `lemmatized_test.ipynb` (193 cells, 메인 분석) — 이름이 `test` 라 그냥 폐기 후보로 봤다가 메타데이터 (cell 수, 마크다운 헤더) 보고 발견. **항상 내용 검증 후 결정**.
3. **변종 파일 이름의 신호**: `(중간정리본)`, `(ver2)`, `copy 2` 같은 prefix/suffix 가 붙으면 거의 100% 임시/실험본 — 정리 우선순위 높음.
4. **shell `||` 와 `pipe`**: `cmd 2>&1 | tail -1 || fallback` 은 의도와 다르게 동작 (tail 의 exit 0 때문). 안전 패턴: `if ! cmd; then fallback; fi` 또는 python.
5. **`git rm` 은 tracked 만 처리**: gitignored / untracked 는 그대로 남음. 디렉터리 통째로 청소하려면 `git rm` 후 `rm -rf` 하지만 그 사이 상태를 잘 확인해야 함.
6. **데이터-노트북-코드의 3중 분리**: 한 디렉터리 안에 .py + .ipynb + .csv + 출력물이 섞이면 정리 어려움. 각자 적절한 위치 (`src/`, `notebooks/`, `data/`, `data/.../results/`) 로 보내면 매번 정리 단순.

## 관련 commits

- `60798a2` — refactor: dissolve src/project_code; consolidate fake_data_gen with shared utils