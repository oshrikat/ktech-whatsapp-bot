import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def subscribe_app_to_waba():
    access_token = os.getenv("WHATSAPP_ACCESS_TOKEN")
    waba_id = os.getenv("WHATSAPP_WABA_ID")
    
    if not access_token or not waba_id:
        print("ERROR: Missing WHATSAPP_ACCESS_TOKEN or WHATSAPP_WABA_ID in .env file.")
        return
        
    url = f"https://graph.facebook.com/v26.0/{waba_id}/subscribed_apps"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    print(f"Attempting to subscribe App to WABA: {waba_id}...")
    response = requests.post(url, headers=headers)
    
    if response.status_code == 200:
        print(f"Success! Meta API Response: {response.json()}")
    else:
        print(f"Failed to subscribe. Status Code: {response.status_code}")
        print(f"Error Details: {response.text}")

if __name__ == "__main__":
    subscribe_app_to_waba()