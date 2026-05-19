# examples/graphrag_input/

GraphRAG 인덱싱용 샘플 입력 데이터 (git 포함).

K-Beauty 5 브랜드 (COSRX · PURITO · Beauty of Joseon · I'm From · Dr.Jart+) 의
제품·성분·효과 정보 JSON. 신규 사용자가 챗봇을 처음 인덱싱할 때 사용.

## 파일

| 파일 | 사이즈 | 용도 |
|---|---|---|
| `5brand_graphrag_part.txt` | 100K | Ollama 변형 (`src/rag_chatbot/ollama/`) 인덱싱 input |
| `brand_50_sample.txt` | 44K | OpenAI 변형 (`src/rag_chatbot/cosmetic_rag_chat/`) 인덱싱 input |

## 사용법

### Ollama 변형 인덱싱
```bash
mkdir -p data/model/graphrag_t_2/input
cp examples/graphrag_input/5brand_graphrag_part.txt data/model/graphrag_t_2/input/
graphrag index --root ./data/model/graphrag_t_2
```

### OpenAI 변형 인덱싱
```bash
cp examples/graphrag_input/brand_50_sample.txt \
   src/rag_chatbot/cosmetic_rag_chat/indexing/input/
graphrag index --root ./src/rag_chatbot/cosmetic_rag_chat/indexing
```

## 컨텐츠 형식

```json
[
  {
    "brand": "COSRX",
    "name": "Low pH Good Morning Gel Cleanser",
    "type": "Face Cleanser",
    "ingredients": [...],
    "effects": [...]
  },
  ...
]
```

GraphRAG 가 entity (BRAND / TYPE / INGREDIENT / EFFECT) 와 관계를 자동 추출.
