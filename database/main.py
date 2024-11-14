import logging
import os
from typing import List

import chromadb
from chromadb.config import Settings
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from langchain_experimental.text_splitter import SemanticChunker
from langchain_huggingface.embeddings import HuggingFaceEmbeddings
from rerankers import Reranker

from utils import search_in_db

load_dotenv()

app = FastAPI()

COLLECTION_NAME = os.getenv("COLLECTION_NAME")
CHROMA_HOST = os.getenv("CHROMA_HOST")
CHROMA_PORT = os.getenv("CHROMA_PORT")
THRESHOLD = 0

logging.basicConfig(level=logging.INFO)

client = chromadb.HttpClient(
    host=CHROMA_HOST,
    port=int(CHROMA_PORT),
    settings=Settings()
)

shared_embedder = HuggingFaceEmbeddings(model_name="deepvk/USER-base")

text_splitter = SemanticChunker(shared_embedder, breakpoint_threshold_type="percentile", breakpoint_threshold_amount=65)

ranker = Reranker('DiTy/cross-encoder-russian-msmarco', model_type='cross-encoder')


class ChromaEmbeddingFunction:
    def __init__(self, embedder):
        self.embedder = embedder

    def __call__(self, input: List[str]) -> List[List[float]]:
        return self.embedder.embed_documents(input)


chroma_embedding_function = ChromaEmbeddingFunction(shared_embedder)

collection = client.get_or_create_collection(
    name=COLLECTION_NAME,
    embedding_function=chroma_embedding_function,
)


@app.get("/search")
async def search_document(query: str, num: int = 5, reranker: bool = True):
    try:
        docs = search_in_db(query, collection, num)['documents'][0]
        if reranker:
            docs = ranker.rank(query=query, docs=docs)
            docs = [i.document.text for i in docs.results if i.score > THRESHOLD]
        return {"docs": docs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
