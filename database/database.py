from tg_bot.main import collection

async def upload(text):
    print(text)
    collection.add(
        documents=[text],
        metadatas=[{'source': 'example'}],
        ids=['id1'],
    )


async def answer(text):
    results = collection.query(
        query_texts=[
            text
        ],
        n_results=1
    )
    print(results['documents'])
    return results['documents']
