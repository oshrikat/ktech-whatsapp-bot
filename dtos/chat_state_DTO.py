from typing import TypedDict

class ChatState(TypedDict):
    # מזהה הלקוח
    phone_number: str
    
    # ההודעה החדשה שנכנסה הרגע מוואטסאפ
    current_input: str  
    
    # היסטוריית השיחה (תידרס רק על ידי צומת ה-AI שלנו)
    messages: list[dict]