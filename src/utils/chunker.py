from typing import List

from dotenv import load_dotenv
import os

from openai import OpenAI

load_dotenv()

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
)
async def split_text(text: str) -> List[str]:
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": f"Your task is to split the following text in chunks. Add some article to each chunk. Don't change the text. The size of each chunk should be around 500 tokens. Between two chunks, there should be a '$$$$' separator."},
                {"role": "user", "content": text},
            ],
            max_tokens=16384
        )
        return response.choices[0].message.content.split("$$$$")

    except Exception as e:
        return ["Error during splitting: {e}"]
