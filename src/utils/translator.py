from dotenv import load_dotenv
import os

from openai import OpenAI

load_dotenv()

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
)
async def translate_text_with_openai(text: str, target_language="english") -> str:
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": f"Translate the following text to {target_language}"},
                {"role": "user", "content": text},
            ]
        )
        return response.choices[0].message.content

    except Exception as e:
        return f"Error during translation: {e}"
