from config_keywords_reject_terms.config import FRAUD_CATEGORIES
from config_keywords_reject_terms.states_term import INDIAN_STATES

def generate_queries():
    queries = []
    for state in INDIAN_STATES:                         
        for category, keywords in FRAUD_CATEGORIES.items():
            for keyword in keywords:                     
                query = f"{keyword} {state}"           
                queries.append({                        
                    "query": query,
                    "search_intent": category
                })
    
    return queries

if __name__ == "__main__":

    queries = generate_queries()

    print(f"Generated {len(queries)} queries\\n")

    for q in queries:
        print(
            f"{q['search_intent']:20} -> {q['query']}"
        )