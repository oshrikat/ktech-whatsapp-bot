import hmac
import hashlib
import base64
import urllib.parse
import time
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
        # 1. סידור מספר הטלפון לפורמט מקומי
        local_phone = target_phone
        if local_phone.startswith("+972"):
            local_phone = "0" + local_phone[4:]
        elif local_phone.startswith("972"):
            local_phone = "0" + local_phone[3:]

        # 2. שימוש ב-DTO הארכיטקטוני שלנו למידע הפנימי
        sms_data = OutboundSmsDTO(
            sim_slot=1,
            phone_numbers=local_phone,
            msg_content=message
        )

        # 3. עטיפת ה-DTO בתבנית ה"זהב" שהרגע פיצחנו
        payload = {
            "data": sms_data.model_dump(),
            "timestamp": int(time.time() * 1000),
            "sign": ""
        }

        headers = {
            "Content-Type": "application/json; charset=utf-8"
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.phone_api_url, 
                    json=payload,
                    headers=headers,
                    timeout=10.0
                )
                
                # האפליקציה מחזירה code: 200 כשהכל תקין
                if response.status_code == 200 and "success" in response.text.lower():
                    print(f"✅ Outbound SMS sent successfully to {local_phone}")
                else:
                    print(f"❌ Failed to send SMS. Status: {response.status_code}, Response: {response.text}")
        except Exception as e:
            print(f"❌ Error communicating with Phone API: {e}")

    async def process_incoming_sms(self, sender_phone: str, message_body: str):
        clean_msg = message_body.split('SIM1_')[0].strip()
        print(f"🧠 Routing SMS from {sender_phone} to AI Graph. Clean msg: '{clean_msg}'")
        
        try:
            config = {"configurable": {"thread_id": f"sms_{sender_phone}"}}
            
            # הנחיה ל-AI לענות קצר וקולע ב-SMS
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