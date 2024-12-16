import logging
import os
import src.answer_generation.prompts as prompts
import openai
from dotenv import load_dotenv
from openai import OpenAI

logging.basicConfig(level=logging.INFO)
load_dotenv()
key = os.getenv("OPENAI_API_KEY")
openai.api_key = key


async def preprocess_answer(question, information):
    client = OpenAI()
    request = prompts.ASKING_PROMT + "Question: " + question + "Information: " + information
    stream = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": request}],
        stream=True,
    )
    answer = ""
    for chunk in stream:
        if chunk.choices[0].delta.content is not None:
            answer += chunk.choices[0].delta.content
    return answer
