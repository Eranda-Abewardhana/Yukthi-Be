from pydantic import BaseModel, Field
from typing import Literal, Optional, List
from datetime import datetime


# Response model for chat endpoint
class ChatResponse(BaseModel):
    message: str
    links: List[dict]
    timestamp: datetime
    status: Literal["success", "pending", "error", "started","over limit"]

class RequestBody(BaseModel):
    query: str

# General error response model
class ErrorResponse(BaseModel):
    detail: str = Field(..., description="Error message explaining what went wrong")
    status: Literal["error", "blocked"] = Field(..., description="Status of the response")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Time the error occurred")
    links: Optional[List[str]] = None
