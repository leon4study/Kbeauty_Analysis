# Amazon × TikTok 결합 분석 노트북

Amazon 리뷰 데이터 + TikTok 영상/인플루언서 데이터를 결합한 분석 모음. 변종이 6개 누적되어 있어 별도 큐레이션 필요.

## 변종 카탈로그 (파일명 기반 임시 분류)

| 노트북 | 사이즈 | 추정 가설/차이 | 검증 상태 |
|---|---:|---|---|
| `amazon_tiktok_analysis.ipynb` | 48M | 기본 분석 (EDA + 결합) | 미검증 |
| `amazon_tiktok_analysis_ngram_added.ipynb` | 51M | n-gram 피처 추가 실험 | 미검증 |
| `amazon_tiktok_statistic_analysis.ipynb` | 57M | 통계 분석 본 | 미검증 |
| `amazon_tiktok_statistic_analysis_1228.ipynb` | 56M | 12월 28일 시점 스냅샷 | 미검증 |
| `amazon_tiktok_statistic_analysis_without_wonyoung.ipynb` | 57M | 장원영(이상치 후보?) 데이터 제외 가설 | 미검증 |
| `amazon_tiktok_statistic_analysis_without_wonyoung copy.ipynb` | 15M | 위 또 다른 사본 (사이즈 작음 → 결과 셀 다름) | 미검증 |

> ⚠️ **각 변종의 정확한 가설/차이는 아직 검증 안 됨**. 50M+ 노트북 6개 — 별도 큐레이션 세션에서 markdown header diff + 핵심 셀 비교 후 [EXPERIMENTS_PLAYBOOK](../../docs/refactor/EXPERIMENTS_PLAYBOOK.md) 패턴 C (README 카탈로그) 또는 통폐합 결정 예정.

## 변종 비교 명령어 (큐레이션 시 사용)

```bash
# markdown 헤더 + 변수 할당만 추출해서 diff (50M 노트북도 30초)
for f in *.ipynb; do
  jupyter nbconvert --to script --stdout "$f" 2>/dev/null \
    | grep -E "^# ###|^# ##|^[a-z_]+ =" > "/tmp/${f%.ipynb}.summary"
done
diff /tmp/amazon_tiktok_analysis.summary /tmp/amazon_tiktok_analysis_ngram_added.summary
```

## 관련 docs

- [../../docs/refactor/EXPERIMENTS_PLAYBOOK.md](../../docs/refactor/EXPERIMENTS_PLAYBOOK.md) — 변종 정리 표준 + 통폐합 패턴
