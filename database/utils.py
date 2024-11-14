def search_in_db(query_text, collection, num):
    try:
        results = collection.query(query_texts=[query_text], n_results=num)
        return results
    except Exception as e:
        raise e
