import pytz
from datetime import datetime

def check_business_hours() -> str:
    """
    בודק את התאריך והשעה הנוכחיים בישראל ומחזיר סטטוס פתיחה של המעבדה.
    מיועד לשימוש על ידי מודל ה-AI כדי לענות ללקוחות על שעות פעילות בזמן אמת.
    """
    # הגדרת אזור הזמן של ישראל - קריטי כדי למנוע טעויות אם השרת יושב בחו"ל
    israel_tz = pytz.timezone('Asia/Jerusalem')
    now = datetime.now(israel_tz)
    
    # חילוץ היום בשבוע (בפייתון: 0 = שני, 6 = ראשון) והשעה
    day_of_week = now.weekday()
    hour = now.hour
    
    # פורמט יפה להצגה ל-AI
    current_time_str = now.strftime("%H:%M")
    days_hebrew = ["שני", "שלישי", "רביעי", "חמישי", "שישי", "שבת", "ראשון"]
    current_day_hebrew = days_hebrew[day_of_week]

    is_open = False
    
    # --- לוגיקת שעות הפעילות של K-Tech ---

    # נניח שעות פעילות סטנדרטיות (ניתן לערוך בקלות):
    # א'-ה' (ראשון=6, שני עד חמישי=0-3): 09:00 - 17:00
    
    if day_of_week in [6, 0, 1, 2, 3]:
        if 9 <= hour < 17:
            is_open = True
            
    # ו' (שישי=4): 09:00 - 13:00
    elif day_of_week == 4:
        if 9 <= hour < 13:
            is_open = True
            
    # שבת (5) - נשאר False
    
    status_text = "פתוחה ומקבלת קהל" if is_open else "סגורה כעת"
    
    # אנחנו מחזירים ל-AI מחרוזת טקסט פשוטה ועובדתית. 
    # ה-AI יקרא אותה, וינסח בעצמו תשובה אנושית ויפה ללקוח.
    return (
        f"השעה הנוכחית בישראל: {current_time_str}, יום {current_day_hebrew}. "
        f"סטטוס המעבדה כרגע: {status_text}. "
        "שעות הפעילות הרשמיות של K-Tech: א'-ה' 09:00-17:00, ו' 09:00-13:00, שבת סגור."
    )