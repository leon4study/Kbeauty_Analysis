# [←](../README.md) TikTok Crawler 및 지표 정의 (TikTok Crawler & Metrics)

TikTok 콘텐츠의 반응도를 정량적으로 측정하기 위한 수집 및 지표 산출 로직입니다.

### 1. 수집 메커니즘
* 해시태그(`kbeauty`, `skincareroutine` 등)를 기반으로 검색 결과 내 영상 데이터를 수집합니다.
* 영상 고유 ID, 작성자 정보, 설명(Caption), 태그 리스트, 성과 지표(조회수, 좋아요, 댓글, 공유, 저장)를 데이터베이스에 반영합니다.

### 2. 성과 지표 정의 (Core Metrics)
본 분석에서는 콘텐츠의 효율성을 측정하기 위해 두 가지 지표를 핵심적으로 활용합니다.

* **ER (Engagement Rate)**: 팔로워 수 대비 참여량의 합계($\frac{Like+Comment+Save}{Followers}$)로, 인플루언서의 팬덤 충성도를 측정합니다.
* **ERV (Engagement Rate by Views)**: 조회수 대비 참여량의 합계($\frac{Like+Comment+Save}{Views}$)로, 노출 대비 실제 반응 효율을 측정합니다. **K-Premium 산출의 핵심 지표**입니다.

### 3. 제약 사항
* TikTok의 캡차(CAPTCHA) 및 로그인 세션 차단 정책으로 인해 수집 시점에 수동 세션 인증이 필요합니다. 따라서 완전 무인 자동화보다는 분석가가 개입하는 반자동 배치(Batch) 수집 형태로 운영됩니다.