from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.llms.ollama import Ollama  # Ollama용 LLM
import gradio as gr

# Ollama LLM 설정
llm = Ollama(model="mistral")  # 사용하려는 Ollama 모델 지정

def answer(message, history):
    files = []
    for msg in history:
        if msg['role'] == "user" and isinstance(msg['content'], tuple):
            files.append(msg['content'][0])
    for file in message["files"]:
        files.append(file)

    # 파일이 없으면 오류 방지
    if not files:
        return "📂 업로드된 파일이 없습니다. 텍스트 또는 PDF 파일을 업로드하세요."

    # 파일 로드 및 RAG 인덱싱
    try:
        documents = SimpleDirectoryReader(input_files=files).load_data()
        index = VectorStoreIndex.from_documents(documents)
        query_engine = index.as_query_engine(llm=llm)
        return str(query_engine.query(message["text"]))
    except Exception as e:
        return f"⚠️ 오류 발생: {str(e)}"

demo = gr.ChatInterface(
    answer,
    type="messages",
    title="Llama Index RAG Chatbot (Ollama)",
    description="Upload any text or PDF files and ask questions about them!",
    textbox=gr.MultimodalTextbox(file_types=[".pdf", ".txt"]),
    multimodal=True
)

demo.launch()
