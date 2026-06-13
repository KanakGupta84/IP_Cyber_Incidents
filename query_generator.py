from config import STATE, FRAUD_CATEGORIES

def generate_queries():
    queries = []

    for category, keywords in FRAUD_CATEGORIES.items():

        for keyword in keywords:

            query = f"{keyword} {STATE}"

            queries.append({
                "query": query,
                "search_intent": category
            })

    print(queries)
    return queries

if __name__ == "__main__":

    queries = generate_queries()

    print(f"Generated {len(queries)} queries\\n")

    for q in queries:
        print(
            f"{q['search_intent']:20} -> {q['query']}"
        )