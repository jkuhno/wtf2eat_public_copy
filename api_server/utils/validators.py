import requests # type: ignore
import os


CF_TURNSTILE_SECRET = os.environ['CF_TURNSTILE_SECRET']


def validate_api_key(gmaps_api_key: str):
    # Validate Google Maps API key
    url = "https://places.googleapis.com/v1/places:searchText"

    # Using field mask to restrict to only free Place IDs
    headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": gmaps_api_key,
            "X-Goog-FieldMask": "places.id,"
        }
    # Needs a better way to handle location bias, this is not restrictive enough
    # PageSize could be larger
    data = {
            "textQuery": "restaurant",
            "pageSize": "1",
            
    }
    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 200:
        return True
    else:
        return False
    
    
def validate_captcha(captcha: str):
    # Validate CAPTCHA
    captcha_response = requests.post(
        "https://challenges.cloudflare.com/turnstile/v0/siteverify",
        data={"secret": CF_TURNSTILE_SECRET, "response": captcha}
    ).json()

    if captcha_response.get("success"):
        return True
    else:
        return False