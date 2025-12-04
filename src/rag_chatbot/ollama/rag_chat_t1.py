import os
import pandas as pd
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core import Settings
from llama_index.core import Document
from OllamaLLM import OllamaLLM


llm = OllamaLLM(model_name="gemma2")  # Ollama 모델 설정


data_path = 
hotel_review_df = hotel_review_d.to_pandas()

documents = [Document(text=row['review'], metadata={'hotel': row['hotel_name']}) for index, row in hotel_review_df.iterrows()]




Settings.embed_model = HuggingFaceEmbedding(
    model_name="BAAI/bge-small-en-v1.5"
)

