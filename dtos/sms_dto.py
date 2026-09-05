from pydantic import BaseModel, Field

class OutboundSmsDTO(BaseModel):
    """
    אובייקט המייצג בקשה לשליחת SMS יוצא.
    מבודד את המבנה שהאפליקציה דורשת מהלוגיקה של השרת.
    """
    sim_slot: int = Field(default=1, description="The SIM slot to use (1 or 2)")

    phone_numbers: str = Field(..., description="The target phone number")

    msg_content: str = Field(..., description="The content of the SMS message")