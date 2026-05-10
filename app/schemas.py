from typing import List, Literal
from pydantic import BaseModel, Field


class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class Recommendation(BaseModel):
    name: str
    url: str
    test_type: str


class ChatRequest(BaseModel):
    messages: List[Message] = Field(
        ...,
        examples=[
            [
                {"role": "user", "content": "We\'re screening 500 entry-level contact centre agents. Inbound calls, customer service focus. What should we use?"},
                {"role": "assistant", "content": "I can help with that. Is English the operating language, and do you need a specific accent variant?"},
                {"role": "user", "content": "English (US)."},
            ]
        ],
    )


class ChatResponse(BaseModel):
    reply: str
    recommendations: List[Recommendation]
    end_of_conversation: bool
