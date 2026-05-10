from pydantic import BaseModel

class RegisterRequest(BaseModel):
    username: str
    password: str
    role: str

class LoginRequest(BaseModel):
    username: str
    password: str
    

from pydantic import BaseModel, Field

class RegisterRequest(BaseModel):
    username: str
    password: str = Field(min_length=8, max_length=72)

class LoginRequest(BaseModel):
    username: str
    password: str = Field(max_length=72) 