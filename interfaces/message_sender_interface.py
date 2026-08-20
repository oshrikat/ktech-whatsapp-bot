from abc import ABC, abstractmethod

class IMessageSender(ABC):
    """
    An interface (contract) for sending messages.
    Any platform (WhatsApp, SMS, Telegram) must implement this method.
    """
    
    @abstractmethod
    def send_text_message(self, recipient_id: str, text: str) -> bool:
        """
        Sends a simple text message to the recipient.
        
        Args:
            recipient_id (str): The phone number or ID of the user.
            text (str): The text content to send.
            
        Returns:
            bool: True if the message was sent successfully, False otherwise.
        """
        pass