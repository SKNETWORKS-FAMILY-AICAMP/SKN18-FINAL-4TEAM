from typing import Optional

from chatbot.models import UserProfile
from django.db import transaction
from pydantic import BaseModel, Field
from langchain_core.tools import tool


class LoadProfileInput(BaseModel):
    user_id: str = Field(..., description="유저 ID")


class UpdateProfileInput(BaseModel):
    user_id: str = Field(..., description="유저 ID")
    role: Optional[str] = Field(None, description="직무(백엔드/프론트엔드 등)")
    skill_level: Optional[str] = Field(None, description="숙련도")
    weekly_hours: Optional[int] = Field(None, description="주당 학습/준비 시간")
    target_company: Optional[str] = Field(None, description="목표 회사")
    preferred_langs: Optional[list[str]] = Field(None, description="선호 언어 리스트")


@tool("load_profile", args_schema=LoadProfileInput, return_direct=True)
def load_profile(user_id: str) -> dict:
    """DB에서 프로필을 조회해 반환한다."""
    prof = UserProfile.objects.filter(user_id=user_id).first()
    if not prof:
        return {}
    return {
        "role": prof.role,
        "skill_level": prof.skill_level,
        "target_company": prof.target_company,
        "weekly_hours": prof.weekly_hours,
        "preferred_langs": prof.preferred_langs,
    }


@tool("upsert_profile", args_schema=UpdateProfileInput, return_direct=True)
def upsert_profile(
    user_id: str,
    role: Optional[str] = None,
    skill_level: Optional[str] = None,
    weekly_hours: Optional[int] = None,
    target_company: Optional[str] = None,
    preferred_langs: Optional[list[str]] = None,
) -> dict:
    """프로필 필드를 업데이트하거나 새로 생성한다."""
    with transaction.atomic():
        prof, _ = UserProfile.objects.get_or_create(user_id=user_id)
        if role is not None:
            prof.role = role
        if skill_level is not None:
            prof.skill_level = skill_level
        if target_company is not None:
            prof.target_company = target_company
        if weekly_hours is not None:
            prof.weekly_hours = weekly_hours
        if preferred_langs is not None:
            prof.preferred_langs = preferred_langs
        prof.save()
    return {
        "role": prof.role,
        "skill_level": prof.skill_level,
        "weekly_hours": prof.weekly_hours,
        "target_company": prof.target_company,
        "preferred_langs": prof.preferred_langs,
    }
