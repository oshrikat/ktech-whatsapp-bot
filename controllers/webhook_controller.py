from fastapi import APIRouter, Request, HTTPException, Response, BackgroundTasks
from services.graph_service import ktech_bot_graph
from services.whatsapp_service import whatsapp_sender

router = APIRouter(prefix="/webhook", tags=["WhatsApp Webhook"])

VERIFY_TOKEN = "ktech_secure_token_123"

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