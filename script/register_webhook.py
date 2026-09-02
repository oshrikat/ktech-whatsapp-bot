import requests
from requests.auth import HTTPBasicAuth

# 1. הזן את הנתונים המדויקים שהופיעו לך במסך הבית של הטלפון:
PHONE_LOCAL_URL = "http://10.0.0.8:8080/api/v1/webhooks"
USERNAME = "K-Tech bot"
PASSWORD = "ktech123"

# 2. היעד באורקל שאליו הטלפון צריך לירות את ה-SMS:
payload = {
    "url": "http://158.178.129.94:8000/webhook/sms/inbound",
    "event": "sms:received"
}

try:
    print(f"Connecting to phone at: {PHONE_LOCAL_URL}...")
    response = requests.post(
        PHONE_LOCAL_URL, 
        json=payload, 
        auth=HTTPBasicAuth(USERNAME, PASSWORD),
        timeout=10 # כדי שלא ייתקע לנצח אם אין חיבור
    )
    
    print(f"Status Code: {response.status_code}")
    
    # מנסים לקרוא JSON, ואם זה נופל - נדפיס טקסט גולמי
    try:
        print(f"JSON Response: {response.json()}")
    except ValueError:
        print(f"Raw Text Response (Not JSON): {response.text}")
        
except requests.exceptions.RequestException as e:
    print(f"Connection Failed: {e}")
    print("\n---> בעיית רשת: ודא שהמחשב והטלפון מחוברים לאותו ה-Wi-Fi, ושהשרת באפליקציה דלוק!")