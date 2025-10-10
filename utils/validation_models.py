from pydantic import BaseModel

class add_contact_validation(BaseModel):
    username:str
    
class message_validation(BaseModel):
    chat_id:str
    message:str