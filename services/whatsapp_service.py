import os
import requests
from dotenv import load_dotenv
from interfaces.message_sender_interface import IMessageSender

load_dotenv()

class WhatsAppService(IMessageSender):
    """
    A concrete implementation of the IMessageSender interface for Meta's WhatsApp API.
    """
    
    def __init__(self):
        # We will need to set these in the .env file later
        self.access_token = os.getenv("WHATSAPP_ACCESS_TOKEN")
        self.phone_number_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
        self.version = "v26.0"
        
    def send_text_message(self, recipient_id: str, text: str) -> bool:
        """
        Sends a text message via the WhatsApp Cloud API.
        """
        if not self.access_token or not self.phone_number_id:
            print("ERROR: Missing WhatsApp credentials in .env file.")
            return False
            
        url = f"https://graph.facebook.com/{self.version}/{self.phone_number_id}/messages"
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        # This is the exact JSON structure Meta demands
        payload = {
            "messaging_product": "whatsapp",
            "to": recipient_id,
            "type": "text",
            "text": {
                "body": text
            }
        }
        
        try:
            print(f"WhatsApp Service: Attempting to send message to {recipient_id}...")
            response = requests.post(url, headers=headers, json=payload)
            
            if response.status_code == 200:
                print("WhatsApp Service: Message sent successfully!")
                return True
            else:
                print(f"WhatsApp Service: Failed to send. Status: {response.status_code}")
                print(f"Error Details: {response.text}")
                return False
                
        except Exception as e:
            print(f"WhatsApp Service: Exception occurred while sending message: {e}")
            return False

# Initialize a singleton instance to be used by the controllers
whatsapp_sender = WhatsAppService()

# ==========================================
# --- LOCAL MANUAL TEST (Outbound Message) ---
# ==========================================
if __name__ == "__main__":
    # Insert your actual phone number here with country code (e.g., "972501234567")
    TEST_PHONE_NUMBER = "972535204447" 
    
    print("\n" + "="*40)
    print("🧪 TEST: Sending Outbound WhatsApp Message")
    print("="*40)
    
    test_message = "Hello! This is a test message directly from the K-Tech Server API."
    
    # Call the service directly
    success = whatsapp_sender.send_text_message(TEST_PHONE_NUMBER, test_message)
    
    if success:
        print("\n✅ Test passed! Check your phone.")
    else:
        print("\n❌ Test failed. Check the error logs above.")
    print("="*40 + "\n")