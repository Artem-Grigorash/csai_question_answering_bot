import uuid
import os
from typing import List

import chromadb

from src.answer_generation.answer import preprocess_answer
from langchain_huggingface.embeddings import HuggingFaceEmbeddings
from langchain_experimental.text_splitter import SemanticChunker
from dotenv import load_dotenv

load_dotenv()

COLLECTION_NAME = os.getenv("COLLECTION_NAME")
CHROMA_HOST = os.getenv("CHROMA_HOST")
CHROMA_PORT = os.getenv("CHROMA_PORT")
THRESHOLD = 0

shared_embedder = HuggingFaceEmbeddings(model_name="deepvk/USER-base")
text_splitter = SemanticChunker(shared_embedder, breakpoint_threshold_type="percentile", breakpoint_threshold_amount=80)


class ChromaEmbeddingFunction:
    def __init__(self, embedder):
        self.embedder = embedder

    def __call__(self, input: List[str]) -> List[List[float]]:
        return self.embedder.embed_documents(input)


chroma_embedding_function = ChromaEmbeddingFunction(shared_embedder)

storage_path = os.getenv('STORAGE_PATH')
if storage_path is None:
    raise ValueError('STORAGE_PATH environment variable is not set')

client = chromadb.PersistentClient(path=storage_path)

collection = client.get_or_create_collection(name="csai", embedding_function=chroma_embedding_function)


async def upload(text):
    chunks = text_splitter.split_text(text)
    print(text)
    for chunk in chunks:
        chunk_id = uuid.uuid4()
        print(chunk_id, chunk)
        collection.add(
            documents=[chunk],
            metadatas=[{"source": "upload", "chunk_id": str(chunk_id)}],
            ids=[str(chunk_id)]
        )


async def answer(text):
    results = collection.query(
        query_texts=[
            text
        ],
        n_results=10
    )
    print(results)

    a = await preprocess_answer(text, '\n'.join(results['documents'][0]))
    return a