# [←](../README.md) ETL 및 데이터 정규화 (ETL Pipeline)

수집된 데이터의 일관성을 확보하고 분석 정확도를 높이기 위한 가공 프로세스입니다.

### 1. 텍스트 정제 프로세스
`src/amazon_review_crawler/reviews.py`에 정의된 정제 로직을 따릅니다.
* **Cleaning**: HTML 태그, 특수문자, 이모티콘을 제거하고 소문자로 변환합니다.
* **Tokenization & Lemmatization**: NLTK/SpaCy를 활용하여 텍스트를 토큰화하고 단어의 원형을 복원합니다.
* **Stopwords Removal**: 분석에 유의미하지 않은 불용어를 제거하고, 'Glass Skin'과 같은 주요 도메인 용어를 보존하기 위해 N-gram을 생성합니다.

### 2. 분석용 특성 생성 (Feature Engineering)
* **Log Transformation**: 조회수와 팔로워 수의 분포 비대칭성(Skewness)을 해결하기 위해 로그 변환을 수행합니다($\log\_view$, $\log\_follower$).
* **K-keyword Flagging**: 해시태그 및 텍스트 내 특정 키워드 포함 여부에 따라 Binary 변수를 생성합니다.

### 3. 적재 로직
* **MySQL Upsert**: `ON DUPLICATE KEY UPDATE` 구문을 활용하여, 기존 데이터가 존재할 경우 최신 성과 데이터로 업데이트하고 존재하지 않을 경우 새로 삽입합니다.