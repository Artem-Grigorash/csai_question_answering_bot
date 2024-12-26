import uuid
import os
from typing import List

import chromadb
from langchain_text_splitters import RecursiveCharacterTextSplitter

from answer_generation.answer import preprocess_answer
from langchain_huggingface.embeddings import HuggingFaceEmbeddings
from dotenv import load_dotenv
from googletrans import Translator

translator = Translator()

load_dotenv()

COLLECTION_NAME = os.getenv("COLLECTION_NAME")
CHROMA_HOST = os.getenv("CHROMA_HOST")
CHROMA_PORT = os.getenv("CHROMA_PORT")
THRESHOLD = 0

shared_embedder = HuggingFaceEmbeddings(model_name="deepvk/USER-base")
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=100,
    separators=["\n\n", "\n", ".", " ", ""],
)


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


async def upload(text, document_path):
    chunks = text_splitter.split_text(text)
    print(text)
    for chunk in chunks:
        chunk_id = uuid.uuid4()
        print(chunk_id, chunk)
        collection.add(
            documents=[translator.translate(chunk, dest='en').text],
            metadatas=[{"source": "upload", "chunk_id": str(chunk_id), "document_path": document_path}],
            ids=[str(chunk_id)]
        )


async def answer(text):
    results = collection.query(
        query_texts=[
            translator.translate(text, dest='en').text
        ],
        n_results=5
    )
    print(results, translator.translate(text, dest='en').text)
    documents_with_ids = [
        f"(id: {meta['chunk_id']}) document: {doc}"
        for doc, meta in zip(results['documents'][0], results['metadatas'][0])
    ]
    a = await preprocess_answer(translator.translate(text, dest='en').text, '\n'.join(documents_with_ids))
    response, ids = a.split('\n')[:-1], a.split('\n')[-1]
    print(a)
    if 'EMPTY' in ids:
        return '\n'.join(response), []
    document_paths = []
    for result in results['metadatas'][0]:
        if result['chunk_id'] in ids:
            document_paths.append(result['document_path'])
    return '\n'.join(response), document_paths
