import gradio as gr
import lancedb
from llama_index.vector_stores.lancedb import LanceDBVectorStore
from llama_index.llms.ollama import Ollama
from llama_index.core import VectorStoreIndex, StorageContext, SimpleDirectoryReader
import os
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core import Settings
import pandas as pd
from llama_index.core import ServiceContext


# Settings를 사용하여 임베딩 및 LLM 설정
Settings.embed_model = HuggingFaceEmbedding(model_name="sentence-transformers/all-mpnet-base-v2")
#Settings.embed_model = HuggingFaceEmbedding(model_name="bert-base-uncased")  # 768 차원의 벡터를 생성하는 모델
#Settings.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")
#Settings.embed_model = HuggingFaceEmbedding(model_name="gemma2")

# 📌 Ollama 모델 설정 (로컬 모델 사용)
#llm = OllamaLLM(model_name="gemma2")  # Ollama 모델 설정
#Settings.llm = llm


llm = Ollama(model="gemma2",base_url="http://localhost:11434/v1")
Settings.llm = llm

# 📌 GraphRAG에서 생성한 LanceDB 불러오기
db_path = "/Users/jun/GitStudy/Data_4/Data/project5/model/graphrag_t_2/output/lancedb"
db = lancedb.connect(db_path)  # GraphRAG에서 사용한 DB 경로 

# ✅ 테이블 존재 여부 확인 후 불러오기
table_names = db.table_names()
# ✅ 모든 테이블을 불러와서 VectorStoreIndex 생성
vector_stores = {name: LanceDBVectorStore(table=db.open_table(name)) for name in table_names}
storage_contexts = {name: StorageContext.from_defaults(vector_store=store) for name, store in vector_stores.items()}
indexes = {name: VectorStoreIndex.from_vector_store(store, storage_context=storage_contexts[name]) for name, store in vector_stores.items()}


# ✅ 여러 테이블을 사용할 수 있도록 Query 엔진을 딕셔너리 형태로 저장
query_engines = {name: index.as_query_engine() for name, index in indexes.items()}

# 📌 파일 업로드 후 문서 처리
def process_uploaded_files(files):
    """사용자가 업로드한 파일을 처리하여 LlamaIndex에 추가"""
    if not files:
        return None  # 파일이 없으면 무시

    # 파일 저장 경로
    upload_dir = "uploaded_files"
    os.makedirs(upload_dir, exist_ok=True)

    # 업로드된 파일 저장
    file_paths = []
    for file in files:
        file_path = os.path.join(upload_dir, file.name)
        file_paths.append(file_path)

        # Parquet 파일 처리
        if file.name.endswith(".parquet"):
            try:
                df = pd.read_parquet(file)  # ✅ Parquet 파일을 DataFrame으로 변환
                text_data = df.to_string(index=False)  # ✅ DataFrame을 문자열로 변환
                text_file_path = file_path.replace(".parquet", ".txt")  # 변환된 파일명
                with open(text_file_path, "w", encoding="utf-8") as text_file:
                    text_file.write(text_data)  # ✅ TXT 파일로 저장하여 LlamaIndex가 읽을 수 있도록 변환
                file_paths.append(text_file_path)  # 변환된 파일을 추가
            except Exception as e:
                print(f"❌ Parquet 파일 변환 실패: {e}")
                return None  # 변환 실패 시 무시

        else:
            # 기존 방식대로 파일 저장
            with open(file_path, "wb") as f:
                f.write(file.read())

    # 📌 새 문서 인덱싱
    documents = SimpleDirectoryReader(input_files=file_paths).load_data()
    new_index = VectorStoreIndex.from_documents(documents)
    return new_index.as_query_engine()

# 📌 사용자 메시지 처리
def answer(message, history, files):
    
    global query_engines
    """사용자의 질문을 받고, 기존 GraphRAG 데이터 + 업로드된 문서 데이터로 답변"""
    
    # 기존 GraphRAG 데이터 (여러 테이블에서 처리)
    query_engine_list = list(query_engines.values())  
    
    # 업로드된 파일이 있을 경우 새롭게 인덱싱하여 추가
    new_query_engine = process_uploaded_files(files)
    if new_query_engine:
        query_engine_list.append(new_query_engine)
        query_engines["uploaded_files"] = new_query_engine # ✅ 업로드한 문서도 추가
    
    # 모든 쿼리 엔진에서 질의 수행
    responses = []
    for qe in query_engine_list:
        if hasattr(qe, 'query'):  # query 엔진이 query 메서드를 가지고 있는지 확인
            responses.append(qe.query(message["text"]))
        else:
            print(f"❌ {qe}는 query 메서드를 가지고 있지 않습니다.")
    
    # 📌 응답을 종합하여 반환
    return "\n\n---\n\n".join([str(resp) for resp in responses])

# 📌 Gradio 인터페이스 설정
demo = gr.ChatInterface(
    answer,
    type="messages",
    title="GraphRAG + Ollama RAG Chatbot",
    description="GraphRAG에서 생성한 LanceDB 데이터와 사용자가 업로드한 문서를 활용한 Ollama 기반 RAG Chatbot!",
    textbox=gr.MultimodalTextbox(file_types=[".pdf", ".txt"]),
    multimodal=True  # 파일 업로드 허용
)

# 📌 실행
demo.launch()