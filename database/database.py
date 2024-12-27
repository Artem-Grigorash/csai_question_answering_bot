from answer_generation.answer import preprocess_answer
from tg_bot.main import collection

async def upload(text):
    print(text, 'id' + str(collection.count()))
    collection.add(
        documents=[text],
        metadatas=[{'source': 'example'}],
        ids=['id' + str(collection.count())],
    )


async def answer(text):
    print(text)
    results = collection.query(
        query_texts=[
            text
        ],
        n_results=10
    )
    print(results)

    a = await preprocess_answer(text, '\n'.join(results['documents'][0]))
    return a
