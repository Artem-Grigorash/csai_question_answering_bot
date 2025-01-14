async def add_documents(knowledge_base, documents):
    if documents:
        knowledge_base.load_documents(documents, upsert=True)
