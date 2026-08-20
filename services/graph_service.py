from langgraph.graph import StateGraph, START, END
import os
from langgraph.checkpoint.upstash_redis import UpstashRedisSaver
from dtos.chat_state import ChatState
from services.ai_service import generate_ai_response, summarize_conversation

checkpointer = UpstashRedisSaver.from_env()

# פונקציית העזר לכיווץ הזיכרון
def cut_if_needed(messages: list) -> list:
    # אם יש פחות מ-11 הודעות (10 היסטוריה + 1 חדשה), אין צורך לכווץ
    if len(messages) < 11:
        return messages   
        
    print("🔄 Memory limit reached. Summarizing past 10 messages...")
    
    # הפרדת ההודעה החדשה מההיסטוריה
    latest_user_message = messages[-1]
    messages_to_summarize = messages[:-1]
    
    # הפעלת הסיכום
    summary_text = summarize_conversation(messages_to_summarize)
    
    # יצירת הודעת מערכת המכילה את הסיכום
    summary_message = {
        "role": "model",
        "content": f"[קונטקסט משיחה קודמת]: {summary_text}"
    }
    
    # דריסת הזיכרון הישן והחזרת הרשימה המכווצת (סיכום + הודעה נוכחית)
    return [summary_message, latest_user_message]

# צומת ה-AI בגרף
def chatbot_node(state: ChatState):
    # 1. שליפת ההיסטוריה מהזיכרון (או רשימה ריקה אם זו שיחה חדשה)
    current_messages = list(state.get("messages", []))
    
    # 2. הוספת ההודעה החדשה של הלקוח באופן ידני
    new_user_msg = state.get("current_input", "")
    if new_user_msg:
        current_messages.append({"role": "user", "content": new_user_msg})

    # 3. כיווץ הזיכרון (אם הגענו ל-11 הודעות)
    optimized_messages = cut_if_needed(current_messages)

    print(f"Graph Node: Sending prompt to AI with {len(optimized_messages)} messages in memory.")
    
    # 4. קריאה ל-AI (Gemini 3.5 Flash Lite)
    ai_response_text = generate_ai_response(optimized_messages, state.get("phone_number"))
    
    # 5. הוספת תשובת הבוט לרשימה
    optimized_messages.append({"role": "model", "content": ai_response_text})
    
    # 6. החזרת הרשימה המעודכנת כדי לדרוס את הזיכרון ב-State
    return {"messages": optimized_messages}

# --- בניית הגרף ---
workflow = StateGraph(ChatState)
workflow.add_node("chatbot", chatbot_node)

workflow.add_edge(START, "chatbot")
workflow.add_edge("chatbot", END)

# קומפילציה עם מנהל הזיכרון
ktech_bot_graph = workflow.compile(checkpointer=checkpointer)

# ==========================================
# --- LOCAL MANUAL TEST ---
# ==========================================
if __name__ == "__main__":
    config = {"configurable": {"thread_id": "050_test_oshri"}}
    
    print("\n" + "="*40)
    print("🧪 TEST TURN 1: Giving the bot context")
    print("="*40)
    
    user_msg_1 = "היי, קוראים לי אושרי ואני צריך לתקן את המסך של מכונת הגילוח."
    print(f"User: {user_msg_1}")
    
    # שים לב: אנחנו משתמשים ב-current_input!
    response_1 = ktech_bot_graph.invoke(
        {"current_input": user_msg_1},
        config
    )
    print(f"\nBot Reply: {response_1['messages'][-1]['content']}")
    
    print("\n" + "="*40)
    print("🧪 TEST TURN 2: Testing memory retention")
    print("="*40)
    
    user_msg_2 = "איך קוראים לי ומה רציתי לתקן? וכמה זה אמור לעלות בערך?"
    print(f"User: {user_msg_2}")
    
    # שוב, משתמשים ב-current_input
    response_2 = ktech_bot_graph.invoke(
        {"current_input": user_msg_2},
        config
    )
    print(f"\nBot Reply: {response_2['messages'][-1]['content']}")
    print("\nTest completed.\n")    