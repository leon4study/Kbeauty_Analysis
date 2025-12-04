# Amazon Review & Item Crawler

Amazon 크롤러는 Selenium을 사용하여 다음 데이터를 수집합니다.

## 📌 수집 항목

- 제품명
- ASIN
- 가격
- 브랜드
- 카테고리
- 총 리뷰수
- 별점
- 성분(Ingredients)
- Best Seller Rank
- Description
- Detail SPEC
- 리뷰 데이터(최대 2만 건)

## 👨‍💻 코드 구조

main.py  
│  
├── amazon_login()  
├── select_best_sellers()  
├── get_description()  
├── crawl_amazon() ← 전체 크롤링 파이프라인  
│  
├── load_items()  
└── load_reviews()

## 🧪 특징

- Sponsored 필터링 가능
- 중복 ASIN 체크
- 브랜드 필터링
- 스크롤 스텝을 셀레니움 액션으로 구현
- 리뷰 페이지 무한 페이징 처리
