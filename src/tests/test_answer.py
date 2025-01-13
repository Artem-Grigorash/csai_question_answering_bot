import pytest
import asyncio

from src.database import database
from src.tests.test_data import test_data


async def test_response(question, key_words, retries=3):
    for attempt in range(1, retries + 1):
        try:
            answer = await database.answer(question)
            print(f"Attempt {attempt}: Answer: {answer}\n")
            for word in key_words:
                assert word.lower() in answer.lower()
            print("Test passed!\n\n\n")
            return answer
        except AssertionError as e:
            print(f"Attempt {attempt} failed: {e}\n")
            if attempt == retries:
                raise AssertionError
        except Exception as e:
            print(f"Error retrieving the answer on attempt {attempt}: {e}\n")
            if attempt == retries:
                raise AssertionError
        await asyncio.sleep(1)


async def test():
    errors = []
    for item in test_data:
        question = item['question']
        keywords = item['keywords']
        try:
            response = await test_response(question, keywords)
            errors.append((question, response))
        except AssertionError as e:
            errors.append((question, "test failed"))
            print(f"Errors for question '{question}':\n{e}")
    return errors


@pytest.mark.asyncio
async def test_all():
    errors = await test()
    if len(errors) > 0:
        print("Some tests failed:\n")
        for error in errors:
            print(error)
        raise AssertionError
    else:
        print("All tests passed successfully!")
