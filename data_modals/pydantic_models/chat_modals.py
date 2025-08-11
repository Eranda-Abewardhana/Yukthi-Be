
from pydantic import BaseModel
class UserMessageModal(BaseModel):
    message: str

class TaskResponse(BaseModel):
    task_id: str