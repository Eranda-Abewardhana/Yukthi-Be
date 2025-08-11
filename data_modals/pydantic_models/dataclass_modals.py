from pydantic import BaseModel
from dataclasses import dataclass



class UserContext(BaseModel):
    user_input_query:str
    index:str

