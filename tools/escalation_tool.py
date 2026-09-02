from services.whatsapp_service import whatsapp_sender
import os

# המספר של המנהל. 
MANAGER_PHONE_NUMBER = os.getenv("MANAGER_PHONE_NUMBER")

def escalate_to_human(customer_phone: str, summary: str) -> str:
    """
    מפעיל התראת הסלמה ושולח הודעת חירום למנהל המעבדה בווטסאפ.
    יש להשתמש בכלי זה אך ורק כאשר לקוח מביע תסכול רב, מסתובב במעגלים, 
    או מבקש מפורשות לדבר עם נציג אנושי או מנהל.
    
    פרמטרים:
    customer_phone: מספר הטלפון של הלקוח כפי שהוצג למודל.
    summary: תקציר קצר (משפט או שניים) של מהות הבעיה וסיבת ההסלמה.
    """
    
    # ניסוח ההודעה שתישלח לאבא שלך
    alert_message = (
        "🚨 *התראת שירות מבוט K-Tech!* 🚨\n\n"
        "לקוח דורש מענה אנושי / הסלמה.\n"
        f"📱 *מספר הלקוח:* {customer_phone}\n"
        f"💬 *תקציר הבעיה:* {summary}\n\n"
        "אנא חזור אליו בהקדם."
    )
    
    # שימוש בשירות הוואטסאפ הקיים שלנו כדי לשלוח את ההודעה למנהל
    print(f"🛠️ TOOL TRIGGERED: Escalating call from {customer_phone} to Manager...")
    success = whatsapp_sender.send_text_message(MANAGER_PHONE_NUMBER, alert_message)
    
    # החזרת סטטוס ל-AI כדי שיידע שהפעולה הצליחה ויוכל לעדכן את הלקוח
    if success:
        return "ההודעה נשלחה בהצלחה למנהל המעבדה. עדכן את הלקוח שהפנייה הועברה ושיחזרו אליו."
    else:
        return "שגיאה: שליחת ההודעה למנהל נכשלה. בקש מהלקוח להתקשר למספר 03-6872161."