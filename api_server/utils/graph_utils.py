from fuzzywuzzy import fuzz # type: ignore

def check_preference_negative(restaurant_name, pref):
    # Normalize and prepare text
    restaurant_name = restaurant_name.lower()
    pref = pref.lower()

    # Check for negative phrases
    negative_keywords = ["no", "not", "never", "don't like", "dont like", "hate", "dislike", "avoid"]
    if not any(neg_word in pref for neg_word in negative_keywords):
        return "none"

    # Fuzzy matching: check if restaurant name appears in the sentence
    if fuzz.ratio(pref, restaurant_name) > 49:  # Allow some flexibility for spelling
        return "pop"

    return "none"


def check_preference_score(restaurant_list: list, user_id:str, user_preferences: list, db):
    
    for restaurant in restaurant_list:
        with db.get_store() as store:
            store.put(namespace=("rank_restaurants", user_id), 
                      key=restaurant["name"], 
                      value={
                       "reviews": restaurant["reviews"],
                      },
                      index=["reviews"])
    
    boosted_names = []
    for pref in user_preferences:

        with db.get_store() as store:
            score_items_per_pref = store.search(("rank_restaurants", user_id), query=pref.value["preference"], limit=9)
            
        
        for item in score_items_per_pref:
            if item.score >= 0.4:
                boosted_names.append(item.key)

    for restaurant in restaurant_list:
        if restaurant["name"] in boosted_names:
            restaurant["pref_note"] = 'boost'
        else:
            restaurant["pref_note"] = 'none'

    return restaurant_list
    
    
def remove_duplicates(lst: list[dict]):
    seen = set()
    unique_lst = []
    
    for d in lst:
        name = d.get('name')
        if name not in seen:
            seen.add(name)
            unique_lst.append(d)
    
    return unique_lst