import gradio as gr
from langchain.chat_models import ChatOpenAI
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain.document_loaders import TextLoader
import os

# Step 1: 문서 로딩
def load_documents(file_path):
    loader = TextLoader(file_path)
    documents = loader.load()
    return documents

# Step 2: 벡터화 및 검색을 위한 설정
def create_vector_store(documents):
    embeddings = OpenAIEmbeddings()  # OpenAI 임베딩 모델 사용
    vector_store = FAISS.from_documents(documents, embeddings)
    return vector_store

# Step 3: LangChain을 사용한 질문 응답
def generate_answer_with_documents(query, documents):
    # 문서 검색
    vector_store = create_vector_store(documents)
    retriever = vector_store.as_retriever()

    # QA 체인 생성
    qa_chain = RetrievalQA.from_chain_type(
        llm=ChatOpenAI(model="gpt-3.5"), retriever=retriever
    )
    
    response = qa_chain.run(query)
    return response

# Gradio 인터페이스 설정
def answer(message, history, files):
    documents = []
    # 업로드된 파일 처리
    if files:
        for file in files:
            file_path = os.path.join("uploaded_files", file.name)
            documents.extend(load_documents(file_path))  # 새로 로드한 문서 추가

    # RAG 응답 생성
    response = generate_answer_with_documents(message, documents)
    return response

# Gradio 인터페이스 실행
demo = gr.ChatInterface(
    answer,
    type="messages",
    title="LangChain 기반 RAG Chatbot",
    description="LangChain을 사용한 문서 검색과 Ollama 모델을 활용한 응답 생성!",
    textbox=gr.MultimodalTextbox(file_types=[".pdf", ".txt"]),
    multimodal=True  # 파일 업로드 허용
)

demo.launch()
