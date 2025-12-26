from typing import Optional,Any, Dict, List
from chatbot.models import UserProfile,UserOutcomeLog,UserCoachingLog,MemoriesTraits,MemoriesPreferences
from api.models import LivecodingReport
from django.db import transaction
from pydantic import BaseModel, Field
from langchain_core.tools import tool


class LoadDBInput(BaseModel):
    user_id: str = Field(..., description="유저 ID")


class UpdateProfileInput(BaseModel):
    user_id: str = Field(..., description="유저 ID")
    role: Optional[str] = Field(None, description="직무(백엔드/프론트엔드 등)")
    skill_level: Optional[str] = Field(None, description="숙련도")
    weekly_hours: Optional[int] = Field(None, description="주당 학습/준비 시간")
    target_company: Optional[str] = Field(None, description="목표 회사")
    preferred_langs: Optional[list[str]] = Field(None, description="선호 언어 리스트")


@tool("load_profile", args_schema=LoadDBInput, return_direct=True)
def load_profile(user_id: str) -> Dict[str, Any]:
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

@tool("load_recent_outcome_logs", args_schema=LoadDBInput, return_direct=True)
def load_recent_outcome_logs(user_id: str, limit: int = 5) -> List[Dict[str, Any]]:
    """최근 결과 로그를 최신순으로 최대 limit개 조회한다."""
    rows = UserOutcomeLog.objects.filter(user_id=user_id).order_by("-created_at")[:limit]
    return [
        {
            "outcome_id": row.outcome_id,
            "kind": row.kind,
            "summary": row.summary,
            "link": row.link,
            "score": row.score,
            "created_at": row.created_at,
        }
        for row in rows
    ]

@tool("load_recent_coaching_logs", args_schema=LoadDBInput, return_direct=True)
def load_recent_coaching_logs(user_id: str, limit: int = 5) -> List[Dict[str, Any]]:
    """최근 코칭 로그를 최신순으로 최대 limit개 조회한다."""
    rows = UserCoachingLog.objects.filter(user_id=user_id).order_by("-created_at")[:limit]
    return [
        {
            "coaching_id": row.coaching_id,
            "artifact_id": row.artifact_id,
            "findings": row.findings,
            "recommendations": row.recommendations,
            "rubric_scores": row.rubric_scores,
            "created_at": row.created_at,
        }
        for row in rows
    ]

@tool("load_traits", args_schema=LoadDBInput, return_direct=True)
def load_traits(user_id: str) -> Dict[str, Any]:
    """사용자의 traits(강점/약점/패턴/신뢰도)를 조회한다."""
    traits = MemoriesTraits.objects.filter(user_id=user_id).first()
    if not traits:
        return None
    return {
        "strengths": traits.strengths, 
        "weaknesses": traits.weaknesses,
        "patterns": traits.patterns, 
        "confidence": traits.confidence
    }

@tool("load_preferences", args_schema=LoadDBInput,return_direct=True)
def load_preferences(user_id: str) -> Optional[dict]:
    """사용자의 피드백/톤/상세 선호도를 조회한다."""
    obj = MemoriesPreferences.objects.filter(user_id=user_id).first()
    if not obj:
        return None
    return {
        "tone_pref": obj.tone_pref,
        "detail_level": obj.detail_level,
        "feedback_style": obj.feedback_style,
    }
    
@tool("get_recent_coding_reports", args_schema=LoadDBInput,return_direct=True)
def get_recent_coding_reports(user_id: str, limit: int = 5) -> List[dict]:
    """최근 라이브코딩 리포트를 최신순으로 최대 limit개 조회한다."""
    rows = LivecodingReport.objects.filter(user_id=user_id).order_by("-created_at")[:limit]
    
    reports: List[Dict] = []
    for row in rows:
        reports.append({
            "session_id": row.session_id,

            "final_score": float(row.final_score) if row.final_score is not None else None,
            "final_grade": row.final_grade,
            "final_flags": row.final_flags or [],

            "problem_eval_score": float(row.problem_eval_score) if row.problem_eval_score is not None else None,
            "problem_eval_feedback": row.problem_eval_feedback,

            "code_collab_score": float(row.code_collab_score) if row.code_collab_score is not None else None,
            "code_collab_feedback": row.code_collab_feedback,

            "problem_evidence": row.problem_evidence,
            "code_collab_evidence": row.code_collab_evidence,

            "created_at": row.created_at.isoformat() if row.created_at else None,
        })

    return reports


@tool("search_problems", return_direct=True)
def search_problems(
    query: str,
    difficulty_band: str,
    limit: int = 6
) -> list[dict]:
    """
    문제 검색 스텁. 아직 외부 검색 연동 전이라 빈 리스트를 반환한다.
    query: "이분탐색 경계 처리"
    difficulty_band: "Lv2~Lv3" or "easy|medium"
    """
    return []

@tool("search_videos", return_direct=True)
def search_videos(
    query: str,
    max_duration_min: int = 15,
    limit: int = 2
) -> list[dict]:
    """영상 검색 스텁. 아직 연동 전이라 빈 리스트를 반환한다."""
    return []

@tool("filter_seen_materials", return_direct=True)
def filter_seen_materials(
    user_id: str,
    materials: list[dict]
) -> list[dict]:
    """사용자가 이미 본 자료를 필터링하는 스텁. 현재는 그대로 반환한다."""
    return materials
