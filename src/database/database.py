from io import BytesIO

from dotenv import load_dotenv

import os
from googletrans import Translator

translator = Translator()
load_dotenv()

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
DB_URL = os.getenv('DB_URL')


async def add_document_from_file(knowledge_base, documents):
    if documents:
        knowledge_base.load_documents(documents, upsert=True)


def query_assistant(assistant, question: str) -> str:
    return "".join([delta for delta in assistant.run(translator.translate(question, dest='en').text)])



