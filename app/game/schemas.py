from pydantic import BaseModel


class TelegramIDModel(BaseModel):
    telegram_id: int

    
class UserModel(TelegramIDModel):
    username: str
    first_name: str
    last_name: str
    best_score: int