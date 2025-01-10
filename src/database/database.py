async def add_document_from_file(knowledge_base, documents):
    if documents:
        knowledge_base.load_documents(documents, upsert=True)
