import requests # type: ignore
import os

GMAPS_API_KEY = os.getenv("GMAPS_API_KEY")

def get_restaurants(query: str, db, location) -> list[dict]:
    """
    Queries the Places API (new).
    First gets place IDs with Text Search, then details with Place Details.
    Save the results of details query, and first match ids agains the saved ones.
    Because IDs are free to query, this saves API credits by only querying details of the not saved ones.

    Args:
        input (str): LLM generated query string

    Returns:
        list[dict]: Dict keys "name", "reviews", "rating", "maps_uri", "delivery", "photo"
    """

    max_height = 400
    max_width = 400
    
    url = "https://places.googleapis.com/v1/places:searchText"

    # Using field mask to restrict to only free Place IDs
    headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": GMAPS_API_KEY,
            "X-Goog-FieldMask": "places.id,"
        }
    # Needs a better way to handle location bias, this is not restrictive enough
    # PageSize could be larger
    data = {
            "textQuery": query,
            "pageSize": "9",
            "openNow": "false",
            "locationBias": {
              "circle": {
                "center": {"latitude": location['lat'], "longitude": location['lon']},
                "radius": 1000.0
              }
            }
    }
    response = requests.post(url, headers=headers, json=data)

    if not response.json():
        raise ValueError("Could not query for restaurants with this input. If you only meant to indicate a preference, try being more specific")

    place = {}
    place_list = []

    # Check if resulted IDs are stored, and get the details if IDs found
    # Otherwise perform a Place Details query to API
    for id in response.json()["places"]:
        with db.get_store() as store:
            # id["id"] is the place id found with query
            saved_item = store.get(namespace=("restaurants",), key=id['id'])
        if saved_item:
            place["name"] = saved_item.value["name"]
            place["reviews"] = saved_item.value["reviews"]
            place["rating"] = saved_item.value["rating"]
            place["delivery"] = saved_item.value["delivery"]
            place["maps_uri"] = saved_item.value["maps_uri"]
            place["photo"] = saved_item.value["photo"]
            place_list.append(place.copy())
    
        else:
            # When the place is not found locally, query the name and reviews from API
            # These are expensive queries, careful
            
            # Place Details (Basic) SKU: displayName | 0.0170 USD per each
            # Place Details (Preferred) SKU: reviews | 0.025 USD per each

            # Full set of totally new places: (0.017 + 0.025) * pageSize
            # with 5 places, total 0,21 USD (2/24/2025)

            url = f"https://places.googleapis.com/v1/places/{id['id']}"
            headers = {
                "Content-Type": "application/json",
                "X-Goog-Api-Key": GMAPS_API_KEY,
                "X-Goog-FieldMask": "reviews.text.text,displayName,delivery,photos,rating,googleMapsUri",
            }
        
            response = requests.get(url, headers=headers)
            data = response.json()

            if "reviews" not in data.keys():
                data["reviews"] = 'None'
            
            # Only get two reviews
            # TODO: scheck sorting, is it better to get first or last indices
            reviews = data["reviews"][:5]

            # Formatting in case LLM needs to operate on these
            formatted_list = []
            i = 1
            for rev in reviews:
                if "text" not in rev.keys():
                    formatted_list.append(f'Review not found')
                    continue
                formatted_list.append(f'Review {i}: {rev["text"]["text"]}')
                i += 1
            
            # Get a photo of the place
            selected_photo = data["photos"][0]["name"]
            for photo in data["photos"]:
                if data["displayName"]["text"] == photo["authorAttributions"][0]["displayName"]:
                    selected_photo = photo["name"]
                    break
        
            url = f"https://places.googleapis.com/v1/{selected_photo}/media?maxHeightPx={max_height}&maxWidthPx={max_width}&skipHttpRedirect=true"
            headers = {
                "Content-Type": "application/json",
                "X-Goog-Api-Key": GMAPS_API_KEY,
            }
            response = requests.get(url, headers=headers)
            photo_uri = response.json()["photoUri"]

            if "delivery" not in data.keys():
                data["delivery"] = "Unknown"
            elif data["delivery"]:
                data["delivery"] = "Available"
            else:
                data["delivery"] = "Not Available"

            # Store the newly found place details, and append them to the output
            with db.get_store() as store:
                store.put(("restaurants",), 
                           id['id'], 
                           {
                            "name": data["displayName"]["text"], 
                            "reviews": formatted_list,
                            "rating": data["rating"],
                            "delivery": data["delivery"],
                            "maps_uri": data["googleMapsUri"],
                            "photo": photo_uri
                           },
                           index=["reviews"])
            
            place["name"] = data["displayName"]["text"]
            place["reviews"] = formatted_list
            place["rating"] = data["rating"]
            place["delivery"] = data["delivery"]
            place["maps_uri"] = data["googleMapsUri"]
            place["photo"] = photo_uri
            place_list.append(place.copy())
            
    return place_list