"""Local Ollama 기반 RAG 챗봇 — GraphRAG 인덱싱 + 사용자 업로드 문서 둘 다 활용.

같은 RAG 챗봇을 ch1 → ch4 → ch5 → ch6 → ch7 로 점진 진화시킨 결과의 .py 마지막
버전. ch7.ipynb 와 코드는 95%+ 동일 — 노트북은 출력 보면서 개발하던 흔적이고,
이 .py 가 실행 친화적인 정리본. ch8.ipynb 가 그 다음 단계로 LanceDB graph 데이터를
더 깊이 활용 (별도 보존).

스택:
- LLM: Ollama (`gemma2`, 로컬 ``http://localhost:11434``)
- 임베딩: HuggingFace ``sentence-transformers/all-mpnet-base-v2``
- 벡터 store: LanceDB (GraphRAG 인덱싱 결과 재사용)
- UI: Gradio ChatInterface (multimodal — pdf/txt 업로드 지원)

설계 가정:
- Ollama 데몬이 로컬에 ``11434`` 포트로 떠있음 (없으면 LLM 호출 시 fail)
- GraphRAG 인덱싱이 미리 돌아서 ``data/model/graphrag_t_2/output/lancedb`` 에 결과 저장돼있음
- HuggingFace 모델은 첫 실행 시 다운로드 (~수 GB)

확장 힌트:
- 다른 임베딩 시도: 주석 처리된 모델들 (bert-base, BAAI/bge-small) 참고
- Ollama 모델 변경: ``Ollama(model="...")`` 부분 수정 (mistral, llama3 등)
- chat 후처리: ``answer()`` 의 ``responses`` join 로직에서 추가 가공 가능
"""
from __future__ import annotations

import os

import gradio as gr
import lancedb
import pandas as pd
from llama_index.core import (
    Settings,
    SimpleDirectoryReader,
    StorageContext,
    VectorStoreIndex,
)
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.ollama import Ollama
from llama_index.vector_stores.lancedb import LanceDBVectorStore

from util.repo_paths import DATA


# ---- LlamaIndex 글로벌 Settings ---------------------------------------------
# 모든 인덱스가 공통 임베딩/LLM 사용하도록 ``Settings`` 에 한 번 등록.
# 임베딩: 차원/품질 trade-off 고려해서 mpnet 채택 (다른 모델 시도는 주석 참고).
Settings.embed_model = HuggingFaceEmbedding(
    model_name="sentence-transformers/all-mpnet-base-v2"
)
# 다른 임베딩 모델 후보 (필요시 위 줄 대체):
#   HuggingFaceEmbedding(model_name="bert-base-uncased")  # 768 차원
#   HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")
#   HuggingFaceEmbedding(model_name="gemma2")

# LLM: 로컬 Ollama (gemma2 모델). base_url 의 /v1 은 OpenAI-호환 endpoint.
Settings.llm = Ollama(
    model="gemma2",
    base_url="http://localhost:11434/v1",
)


# ---- GraphRAG LanceDB 로드 --------------------------------------------------
# GraphRAG 인덱싱 결과를 LanceDB에서 읽어 LlamaIndex VectorStoreIndex 로 래핑.
# 테이블이 여러 개 (community / entity / text_unit) 라 각각을 별도 query 엔진으로 운영.
DB_PATH = str(DATA / "model" / "graphrag_t_2" / "output" / "lancedb")
db = lancedb.connect(DB_PATH)

table_names = db.table_names()
vector_stores = {
    name: LanceDBVectorStore(table=db.open_table(name)) for name in table_names
}
storage_contexts = {
    name: StorageContext.from_defaults(vector_store=store)
    for name, store in vector_stores.items()
}
indexes = {
    name: VectorStoreIndex.from_vector_store(
        store, storage_context=storage_contexts[name]
    )
    for name, store in vector_stores.items()
}
# 각 테이블별 query 엔진. ``answer()`` 가 모든 엔진에 같은 질문을 던져 응답을 종합.
query_engines = {name: index.as_query_engine() for name, index in indexes.items()}


def process_uploaded_files(files):
    """사용자가 업로드한 파일을 LlamaIndex 인덱스로 변환해 반환.

    pdf/txt 는 SimpleDirectoryReader 로 직접 읽고, parquet 은 DataFrame → 문자열
    변환 후 ``.txt`` 로 저장하여 같은 reader 가 처리할 수 있게 한다.

    Args:
        files: Gradio MultimodalTextbox 가 넘기는 file 객체 리스트.

    Returns:
        새 ``QueryEngine`` 인스턴스. 파일이 없으면 ``None``.
    """
    if not files:
        return None

    upload_dir = "uploaded_files"
    os.makedirs(upload_dir, exist_ok=True)

    file_paths = []
    for file in files:
        file_path = os.path.join(upload_dir, file.name)
        file_paths.append(file_path)

        # parquet 은 텍스트로 변환해야 LlamaIndex Reader 가 인덱싱 가능.
        if file.name.endswith(".parquet"):
            try:
                df = pd.read_parquet(file)
                text_data = df.to_string(index=False)
                text_file_path = file_path.replace(".parquet", ".txt")
                with open(text_file_path, "w", encoding="utf-8") as text_file:
                    text_file.write(text_data)
                file_paths.append(text_file_path)
            except Exception as e:
                print(f"❌ Parquet 파일 변환 실패: {e}")
                return None
        else:
            with open(file_path, "wb") as f:
                f.write(file.read())

    documents = SimpleDirectoryReader(input_files=file_paths).load_data()
    new_index = VectorStoreIndex.from_documents(documents)
    return new_index.as_query_engine()


def answer(message, history, files):
    """ChatInterface 핸들러 — GraphRAG 데이터 + 업로드 문서 둘 다에 질의 후 응답 종합.

    각 query 엔진이 같은 질문에 대해 답을 내고, 결과들을 ``---`` 로 구분하여 이어붙여
    반환. 사용자는 여러 데이터 소스의 답을 한 번에 비교 가능.

    Args:
        message: Gradio 가 넘기는 입력 dict — ``"text"`` 키에 사용자 질문.
        history: 대화 이력 (이 함수에선 미사용).
        files: 업로드된 파일 리스트 (있으면 새 엔진으로 인덱싱 후 추가).
    """
    global query_engines

    # 기존 GraphRAG 데이터 (테이블별 엔진들)
    query_engine_list = list(query_engines.values())

    # 업로드된 파일이 있으면 새 엔진 추가
    new_query_engine = process_uploaded_files(files)
    if new_query_engine:
        query_engine_list.append(new_query_engine)
        query_engines["uploaded_files"] = new_query_engine  # 다음 turn에도 사용

    # 모든 엔진에 같은 질문 던지고 응답 모으기
    responses = []
    for qe in query_engine_list:
        if hasattr(qe, "query"):
            responses.append(qe.query(message["text"]))
        else:
            print(f"❌ {qe} 는 query 메서드를 가지고 있지 않습니다.")

    return "\n\n---\n\n".join([str(resp) for resp in responses])


# Gradio UI — multimodal=True 로 텍스트 + 파일 업로드 같이 받음.
demo = gr.ChatInterface(
    answer,
    type="messages",
    title="GraphRAG + Ollama RAG Chatbot",
    description=(
        "GraphRAG에서 생성한 LanceDB 데이터와 사용자가 업로드한 문서를 활용한 "
        "Ollama 기반 RAG Chatbot!"
    ),
    textbox=gr.MultimodalTextbox(file_types=[".pdf", ".txt"]),
    multimodal=True,
)


if __name__ == "__main__":
    demo.launch()