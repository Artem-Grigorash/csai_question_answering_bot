from googletrans import Translator

translator = Translator()


async def add_document_from_file(knowledge_base, documents):
    if documents:
        knowledge_base.load_documents(documents, upsert=True)


def query_assistant(assistant, question: str) -> str:
    return "".join([delta for delta in assistant.run(translator.translate(question, dest='en').text)])
