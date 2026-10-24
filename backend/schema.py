from typing import Literal
from pydantic import BaseModel, Field as PydanticField


class Option(BaseModel):
    value: str
    label: str


class FieldEvidence(BaseModel):
    selector: str
    label: str
    instructions: str


class FormField(BaseModel):
    id: str
    label: str
    type: str
    section: str
    required: bool
    instructions: str
    options: list[Option] = []
    constraints: dict[str, str] = {}
    required_when: str | None = None
    evidence: FieldEvidence


class Requirement(BaseModel):
    id: str
    text: str
    selector: str


class Form(BaseModel):
    id: str
    title: str
    instructions: str
    source_hash: str
    fields: list[FormField]
    requirements: list[Requirement]
    ambiguities: list[str]


class Explanation(BaseModel):
    field_id: str
    plain_label: str = PydanticField(min_length=2, max_length=100)
    explanation: str = PydanticField(min_length=5, max_length=400)


class ModelExplanation(BaseModel):
    fields: list[Explanation]


class CreateSession(BaseModel):
    form_id: Literal['scholarship', 'community', 'benefit']


class UserAnswer(BaseModel):
    answers: dict[str, str | bool] = PydanticField(default_factory=dict, max_length=30)
    checklist: list[str] = PydanticField(default_factory=list, max_length=10)
    step: int = PydanticField(default=0, ge=0, le=30)


class ProposedAction(BaseModel):
    confirmation: bool
    action_token: str = PydanticField(min_length=20, max_length=150)


class AuditEvent(BaseModel):
    event: str
    created_at: str
    detail: str
