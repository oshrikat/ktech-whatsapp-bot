import os
from google import genai
from google.genai import types
from dotenv import load_dotenv

# --- הייבוא החדש של הכלים שיצרנו ---
from tools.business_hours_tool import check_business_hours

from tools.escalation_tool import escalate_to_human

load_dotenv()

# טעינת בסיס הידע
def load_business_knowledge() -> str:
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        root_dir = os.path.dirname(current_dir)
        file_path = os.path.join(root_dir, "db", "biz_info.txt")
        
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()
            print(f"✅ Knowledge Base Loaded Successfully ({len(content)} characters).")
            return content
    except Exception as e:
        print(f"❌ ERROR: Failed to load db/biz_info.txt: {e}")
        return "אין כרגע מידע זמין על החברה."

BIZ_KNOWLEDGE = load_business_knowledge()

# הוראות למודל הראשי
SYSTEM_INSTRUCTION = f"""
אתה נציג השירות הדיגיטלי הרשמי של חברת "איי.קייטק אינטרנשיונל בע"מ" (K-Tech).
עליך לפעול אך ורק על פי הכללים ובסיס הידע המצורפים להלן.

=== בסיס הידע של החברה ===
{BIZ_KNOWLEDGE}
===========================

הנחיות קריטיות למענה:
1. היצמד אך ורק למידע המופיע בבסיס הידע. אל תמציא פרטים, שירותים, מחירים או שעות פעילות.
2. סירוב לפניות לא רלוונטיות: אם לקוח פונה לגבי סלולר, מחשבים או מוצרי חשמל ביתיים - סרב בנימוס והבהר שאנו מטפלים אך ורק במכונות גילוח/תספורת של K-Tech.
3. טיפול במידע חסר (כמו מחירים): לעולם אל תגיד מילים כמו "אין ברשותי מידע", "אני לא יודע" או "חסר נתון". אם לקוח שואל על מחיר או פרט שאינו בבסיס הידע, ענה בביטחון ובטבעיות כך: "לגבי מחירי המכונות וזמינות מלאי, אנו מספקים את כל הפרטים המדויקים בשמחה דרך טלפון המעבדה: 03-6872161. מוזמן לחייג אלינו!"
4. סגנון: עברית שירותית, קצרה ותמציתית לוואטסאפ.
"""

# הוראות מיוחדות למודל המסכם
SUMMARY_INSTRUCTION = """
תפקידך לסכם שיחת שירות לקוחות בווטסאפ ל-2-3 משפטים עובדתיים בלבד.
חובה לחלץ ולשמר בסיכום את הפרטים הבאים:
1. שם הלקוח - או כל פרט זיהוי אחר (אם הוזכר במהלך השיחה, אחרת ציין 'לא צוין').
2. מהות הבקשה, דגם המכשיר וכל פרט טכני רלוונטי שעלה.
3. התשובה או ההנחיה שניתנה על ידי הנציג (סוכם/נמסר).

פורמט נדרש:
"שם הלקוח / פרט מזהה כלשהו: [שם/ הפרט]. בקשה: [מהות הבקשה]. סוכם/נמסר: [התשובה]."
אל תוסיף ברכות, שמות של החברה או מילים מיותרות. רק עובדות יבשות.
"""

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY is missing from environment variables.")

client = genai.Client(api_key=api_key)

# 1. פונקציית המענה הראשי 
# שינינו את חתימת הפונקציה כדי שתקבל גם את מספר הטלפון
def generate_ai_response(conversation_history: list, customer_phone: str = None) -> str:
    try:
        formatted_contents = []
        for msg in conversation_history:
            role = "user" if msg["role"] == "user" else "model"
            formatted_contents.append(
                types.Content(
                    role=role,
                    parts=[types.Part.from_text(text=msg["content"])]
                )
            )

        dynamic_instruction = SYSTEM_INSTRUCTION
        if customer_phone:
            dynamic_instruction += f"\n\n[הערת מערכת נסתרת: מספר הטלפון של הלקוח בשיחה זו הוא {customer_phone}.]"

        response = client.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents=formatted_contents,
            config=types.GenerateContentConfig(
                system_instruction=dynamic_instruction, # משתמשים בהוראה הדינמית שיצרנו
                temperature=0.2,
                tools=[check_business_hours, escalate_to_human], # הכלים שלנו
            )
        )
        return response.text
        
    except Exception as e:
        print(f"Error generating AI response: {e}")
        return "שלום, נתקלתי בבעיה זמנית בעיבוד הבקשה. אנא פנה למשרדנו במספר 03-6872161."

# 2. פונקציית הסיכום המהירה
def summarize_conversation(messages_to_summarize: list) -> str:
    try:
        text_dialogue = ""
        for msg in messages_to_summarize:
            speaker = "לקוח" if msg["role"] == "user" else "נציג"
            text_dialogue += f"{speaker}: {msg['content']}\n"

        prompt = f"סכם את 10 ההודעות הבאות לפי ההנחיות:\n\n{text_dialogue}"

        response = client.models.generate_content(
            model="gemini-3.1-flash-lite",
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=SUMMARY_INSTRUCTION,
                temperature=0.0,
            )
        )
        print(f"📝 New Summary Generated: {response.text.strip()}")
        return response.text.strip()
    except Exception as e:
        print(f"Error summarizing conversation: {e}")
        return "שיחה קודמת לגבי שירות K-Tech."