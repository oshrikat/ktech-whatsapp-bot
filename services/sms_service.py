import hmac
import hashlib
import base64
import urllib.parse
import httpx
from services.graph_service import ktech_bot_graph
from dtos.sms_dto import OutboundSmsDTO

class SmsService:
    def __init__(self):
        self.secret = "ktech_secret_2026"
        self.phone_api_url = "http://100.86.10.117:5000/sms/send"

    def verify_signature(self, timestamp: str, signature: str) -> bool:
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
        # סידור המספר לפורמט ישראלי רגיל (עובד הכי טוב עם אנדרואיד)
        local_phone = target_phone
        if local_phone.startswith("+972"):
            local_phone = "0" + local_phone[4:]
        elif local_phone.startswith("972"):
            local_phone = "0" + local_phone[3:]
            
        # שימוש ב-Query Parameters - הדרך הכי בסיסית ויציבה לשרתי IoT/Java
        params = {
            "phone_numbers": local_phone,
            "msg_content": message
        }
        
        try:
            async with httpx.AsyncClient() as client:
                # שינוי ל-GET במקום POST, עוקף בעיות קידוד גוף הבקשה
                response = await client.get(
                    self.phone_api_url, 
                    params=params,
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    print(f"✅ Command accepted by phone for {local_phone}")
                else:
                    print(f"❌ Failed to send. Status: {response.status_code}. Response: {response.text}")
        except Exception as e:
            print(f"❌ Error communicating with Phone API: {e}")

    async def process_incoming_sms(self, sender_phone: str, message_body: str):
        # 2. ניקוי הלכלוך שהאפליקציה מוסיפה להודעה הנכנסת (SIM1_ וכו')
        clean_msg = message_body.split('SIM1_')[0].strip()
        print(f"🧠 Routing SMS from {sender_phone} to AI Graph. Clean msg: '{clean_msg}'")
        
        try:
            config = {"configurable": {"thread_id": f"sms_{sender_phone}"}}
            
            # 3. הוספת הנחיה "מאחורי הקלעים" ל-AI כדי שיענה קצר וקולע ל-SMS
            ai_input = f"{clean_msg}\n\n[SYSTEM NOTE: The user is messaging via SMS. Your response MUST be extremely short, maximum 1 or 2 sentences, under 100 characters. No markdown, no long lists.]"
            
            graph_response = ktech_bot_graph.invoke({
                "current_input": ai_input, 
                "phone_number": sender_phone  
            }, config)
            
            bot_reply = graph_response["messages"][-1]["content"]
            print(f"🤖 AI SMS REPLY READY:\n{bot_reply}")
            
            await self.send_sms_reply(sender_phone, bot_reply)
        except Exception as e:
            print(f"❌ Error processing AI logic for SMS: {e}")

sms_manager = SmsService()