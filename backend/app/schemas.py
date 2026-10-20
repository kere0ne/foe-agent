from pydantic import BaseModel, EmailStr, Field


class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: int
    email: str
    is_admin: bool

    class Config:
        from_attributes = True


class ProjectIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str = Field(default="", max_length=2000)


class ProjectOut(BaseModel):
    id: int
    name: str
    description: str

    class Config:
        from_attributes = True


class ProviderIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    kind: str = Field(pattern="^(ollama|openai_compat)$")
    base_url: str = Field(min_length=1, max_length=500)
    model: str = Field(min_length=1, max_length=200)
    api_key: str = Field(default="", max_length=500)
    is_default: bool = False


class ProviderOut(BaseModel):
    id: int
    name: str
    kind: str
    base_url: str
    model: str
    has_key: bool
    is_default: bool


class ConversationIn(BaseModel):
    project_id: int | None = None
    title: str = Field(default="New chat", max_length=200)


class ChatIn(BaseModel):
    conversation_id: int
    content: str = Field(min_length=1, max_length=32000)
    provider_id: int


class RunIn(BaseModel):
    goal: str = Field(min_length=1, max_length=8000)
    provider_id: int
    verify_command: str | None = Field(default=None, max_length=500)
