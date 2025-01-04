from database import database as db
# from test_data import test_data
import pytest
import asyncio

test_data = [
    {
        "question": "What is the wifi password in Pafos Gardens?",
        "keywords": ["pgardens"]
    },
    {
        "question": "How to get from the airport to Paphos?",
        "keywords": ["bus", "taxi", "rent"]
    },
    {
        "question": "What is the address of Pafos Gardens?",
        "keywords": ["Kleious", "7"]
    },
    {
        "question": "What is the phone number at the reception of the hotel Pathos Gardens?",
        "keywords": ["+357 26 882 000"]
    },
    {
        "question": "What documents are needed to extend a visa?",
        "keywords": ["Passport", "Medical Insurance", "Medical Certificate", "Bank Letter", "Bank Guarantee",
                     "House Contract", "Acceptance Letter", "Declaration for Asylum", "Sponsorship Letter",
                     "Payment Receipt"]
    }
]


async def test_response(question, key_words, retries=3):
    for attempt in range(1, retries + 1):
        try:
            answer = await db.answer(question)
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
