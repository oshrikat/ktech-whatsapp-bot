import hmac
import hashlib
import base64
import urllib.parse
import httpx
from services.graph_service import ktech_bot_graph

class SmsService:
    def __init__(self):
        self.secret = "ktech_secret_2026"
        # ה ip מתוך האפליקציה tail של הטלפון קייטק
        self.phone_api_url = "http://100.86.10.117:5000/sms/send" 

    def verify_signature(self, timestamp: str, signature: str) -> bool:
        """אימות מאובטח של החתימה (המיקרוסקופ הוסר, נשאר רק הקוד שעובד חלק)"""
        try:
            clean_signature = urllib.parse.unquote(signature)
            message = f"{timestamp}\n{self.secret}".encode('utf-8')
            secret_bytes = self.secret.encode('utf-8')
            signature_mac = hmac.new(secret_bytes, message, digestmod=hashlib.sha256).digest()
            expected_signature = base64.b64encode(signature_mac).decode('utf-8')
            return hmac.compare_digest(expected_signature, clean_signature)
        except Exception as e:
            print(f"Error verifying SMS signature: {e}")
            return False

    async def send_sms_reply(self, target_phone: str, message: str):
        """שולח בקשת HTTP לשרת הפנימי של טלפון קייטק כדי שישגר SMS"""
        # משתמשים בפורמט שהאפליקציה דורשת, תוך וידוא שסוג הנתונים מוגדר היטב
        payload = {
            "sim_slot": 1,
            "phone_numbers": target_phone,
            "msg_content": message
        }
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        try:
            async with httpx.AsyncClient() as client:
                # לפעמים האפליקציה מצפה ל-Data ולא ל-Json, נתחיל עם Json תקני עם Headers
                response = await client.post(
                    self.phone_api_url, 
                    json=payload, 
                    headers=headers,
                    timeout=10.0
                )
                if response.status_code == 200:
                    print(f"✅ Outbound SMS sent successfully to {target_phone} via K-Tech Phone")
                else:
                    print(f"❌ Failed to send SMS. Phone returned status: {response.status_code}")
                    print(f"Response details: {response.text}")
        except Exception as e:
            print(f"❌ Error communicating with K-Tech Phone API: {e}")

    async def process_incoming_sms(self, sender_phone: str, message_body: str):
        """העברת ההודעה ל-LangGraph ושליחת התשובה חזרה"""
        print(f"🧠 Routing SMS from {sender_phone} to AI Graph...")
        try:
            config = {"configurable": {"thread_id": f"sms_{sender_phone}"}}
            graph_response = ktech_bot_graph.invoke({
                "current_input": message_body, 
                "phone_number": sender_phone  
            }, config)
            
            bot_reply = graph_response["messages"][-1]["content"]
            print(f"🤖 AI SMS REPLY READY:\n{bot_reply}")
            
            print("📤 Sending reply back to the user via SMS...")
            await self.send_sms_reply(sender_phone, bot_reply)
        except Exception as e:
            print(f"❌ Error processing AI logic for SMS: {e}")

# מופע יחיד שישמש את הראוטר
sms_manager = SmsService()