from fastapi import APIRouter, Request, HTTPException, Response, BackgroundTasks , status
from services.graph_service import ktech_bot_graph
from services.whatsapp_service import whatsapp_sender
import os
import urllib.parse
import hmac
import hashlib
import base64

router = APIRouter(prefix="/webhook", tags=["WhatsApp Webhook"])

VERIFY_TOKEN = os.getenv("WEBHOOK_VERIFY_TOKEN", "ktech_secure_token_123")

SMS_SECRET = "ktech_secret_2026"

# --- פונקציית הרקע שתרוץ מאחורי הקלעים ---
def process_ai_and_reply(sender_phone: str, message_body: str):
    """
    פונקציה זו מבצעת את העבודה ה"כבדה" מול Gemini ושולחת את התשובה לוואטסאפ.
    היא רצה ברקע כדי לא לעכב את התשובה למטא.
    """
    try:
        # מעבירים למוח (LangGraph)
        config = {"configurable": {"thread_id": sender_phone}}
        
        graph_response = ktech_bot_graph.invoke({
            "current_input": message_body, 
            "phone_number": sender_phone  
        }, config)
        
        bot_reply = graph_response["messages"][-1]["content"]
        
        print(f"🤖 AI REPLY READY (With Context):\n{bot_reply}")
        print("-" * 40)
        
        # שולחים את התשובה ללקוח בוואטסאפ
        print("📤 Sending reply back to the user via WhatsApp...")
        whatsapp_sender.send_text_message(sender_phone, bot_reply)
        print("=" * 40 + "\n")
        
    except Exception as e:
        print(f"❌ Error in background processing: {e}")

# --- הראוטרים שלנו ---
@router.get("/")
@router.get("")
async def verify_webhook(request: Request):
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if not mode or not token:
        raise HTTPException(status_code=400, detail="Missing parameters")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        print("Meta Webhook verified successfully!")
        return Response(content=challenge, media_type="text/plain")

    raise HTTPException(status_code=403, detail="Invalid verification token")

@router.post("/")
@router.post("")
async def receive_message(request: Request, background_tasks: BackgroundTasks):
    try:
        body = await request.json()
        
        entry = body.get("entry", [])
        if entry:
            changes = entry[0].get("changes", [])
            if changes:
                value = changes[0].get("value", {})
                messages = value.get("messages", [])
                
                if messages:
                    message_data = messages[0]
                    sender_phone = message_data.get("from")
                    
                    if message_data.get("type") == "text":
                        message_body = message_data.get("text", {}).get("body")
                        
                        print("\n" + "=" * 40)
                        print(f"📩 INCOMING WHATSAPP MESSAGE")
                        print(f"From: {sender_phone}")
                        print(f"Text: {message_body}")
                        print("-" * 40)
                        
                        # הוספת עיבוד ה-AI למשימות הרקע במקום לחכות לו!
                        background_tasks.add_task(process_ai_and_reply, sender_phone, message_body)

        # החזרת סטטוס 200 למטא באופן מיידי כדי למנוע את לופ החזרות!
        return {"status": "success"}

    except Exception as e:
        print(f"Error parsing incoming webhook: {e}")
        return {"status": "error"}

def verify_sms_signature(timestamp: str, signature: str, secret: str) -> bool:
    """פונקציה לאימות חתימת HMAC של SmsForwarder"""
    try:
        # יצירת המחרוזת לחתימה לפי התקן של האפליקציה
        message = f"{timestamp}\n{secret}".encode('utf-8')
        secret_bytes = secret.encode('utf-8')
        
        # חישוב החתימה הדיגיטלית
        signature_mac = hmac.new(secret_bytes, message, digestmod=hashlib.sha256).digest()
        expected_signature = base64.b64encode(signature_mac).decode('utf-8')
        
        # השוואה בטוחה של החתימות
        return hmac.compare_digest(expected_signature, signature)
    except Exception as e:
        print(f"Error verifying signature: {e}")
        return False

@router.post("/sms/inbound")
async def receive_sms(request: Request):
    """נקודת קצה לקליטת הודעות SMS ממכשיר ה-Gateway"""
    raw_body = await request.body()
    raw_str = raw_body.decode('utf-8')
    
    # פירוק המידע המקודד
    parsed_data = urllib.parse.parse_qs(raw_str)
    
    sender = parsed_data.get('from', ['Unknown'])[0]
    content = parsed_data.get('content', ['No content'])[0]
    timestamp = parsed_data.get('timestamp', [''])[0]
    signature = parsed_data.get('sign', [''])[0]
    
    # 1. שכבת ההגנה: אימות החתימה
    if not verify_sms_signature(timestamp, signature, SMS_SECRET):
        print(f"⚠️ BLOCKED: Invalid SMS signature from {sender}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Invalid security signature"
        )
        
    print(f"✅ SECURE SMS RECEIVED from {sender}: {content}")
    
    # 2. העברה לשכבת הלוגיקה וה-AI
    # כאן נקרא ל-Service הקיים שלך כדי לעבד את ההודעה מול LangGraph. לדוגמה:
    # await graph_service.process_incoming_message(sender, content, channel="sms")
    
    return {"status": "ok"}