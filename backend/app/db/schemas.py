from pydantic import BaseModel, EmailStr, Field
from enum import Enum
from pydantic import BaseModel
from enum import Enum



class UserRole(str, Enum):
    admin = "admin"
    qa = "qa"
    dev = "dev"

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    role: UserRole = UserRole.qa

class UserOut(BaseModel):
    id: int
    email: EmailStr
    role: UserRole
    class Config:
        from_attributes = True  # pydantic v2: enable orm mode

class LoginIn(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

from pydantic import BaseModel

class ProjectCreate(BaseModel):
    name: str

class ProjectOut(BaseModel):
    id: int
    name: str
    created_by: int
    class Config:
        from_attributes = True

class SuiteCreate(BaseModel):
    project_id: int
    name: str

class SuiteOut(BaseModel):
    id: int
    project_id: int
    name: str
    class Config:
        from_attributes = True

class CaseCreate(BaseModel):
    suite_id: int
    title: str
    steps: str | None = None
    expected: str | None = None

class CaseOut(BaseModel):
    id: int
    suite_id: int
    title: str
    steps: str | None
    expected: str | None
    class Config:
        from_attributes = True

class ResultStatus(str, Enum):
    PASS_ = "PASS"
    FAIL = "FAIL"
    SKIP = "SKIP"

class RunCreate(BaseModel):
    project_id: int
    triggered_by_ci: bool = False

class RunOut(BaseModel):
    id: int
    project_id: int
    created_by: int
    triggered_by_ci: bool
    class Config: from_attributes = True

class ResultCreate(BaseModel):
    case_id: int
    status: ResultStatus
    duration_ms: int | None = None
    evidence_url: str | None = None

class ResultOut(BaseModel):
    id: int
    run_id: int
    case_id: int
    status: ResultStatus
    duration_ms: int | None
    evidence_url: str | None
    class Config: from_attributes = True

class RunSummary(BaseModel):
    run_id: int
    total: int
    passed: int
    failed: int
    skipped: int