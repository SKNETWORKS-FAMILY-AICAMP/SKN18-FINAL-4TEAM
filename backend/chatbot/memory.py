from deepagents.backends import StoreBackend
from deepagents.backends import CompositeBackend, StateBackend
import json
import redis
from dotenv import load_dotenv
import os
from langgraph.store.postgres import PostgresStore
from psycopg_pool import ConnectionPool
from typing import Any, Callable, Dict, List, Optional
from django.db import transaction
from django.utils import timezone
from django.conf import settings
from chatbot.models import (
    UserOutcomeLog,
    UserCoachingLog,
)
from langgraph.checkpoint.redis import RedisSaver
#######################################
# Postgre
########################################

_DB_POOL: ConnectionPool | None = None
_PG_STORE: PostgresStore | None = None

def _build_db_uri() -> str:
    """
    Django DATABASES 설정을 기반으로 DSN을 구성한다.
    """
    db = settings.DATABASES.get("default", {})
    host = db.get("HOST") 
    port = db.get("PORT")
    name = db.get("NAME")
    user = db.get("USER")
    pwd = db.get("PASSWORD")

    if not all([host, name, user, pwd]):
        missing = [k for k in ["NAME", "USER", "PASSWORD"] if not db.get(k)]
        raise RuntimeError(f"Missing DB env vars: {missing}")

    return f"postgresql://{user}:{pwd}@{host}:{port}/{name}"

def get_db_pool() -> ConnectionPool:
    global _DB_POOL
    if _DB_POOL is None:
        db_uri = _build_db_uri()
        _DB_POOL = ConnectionPool(
            conninfo=db_uri,
            min_size=2,
            max_size=10,
            kwargs={"autocommit": True},
        )
    return _DB_POOL

def get_postgres_store() -> PostgresStore:
    """
    PostgresStore는 풀을 물고 있게 하고,
    setup()은 프로세스 시작 시 1회만 호출.
    """
    global _PG_STORE
    if _PG_STORE is None:
        pool = get_db_pool()
        _PG_STORE = PostgresStore(conn=pool)  # PostgresStore가 pool을 받는 형태라면 이게 정답
        _PG_STORE.setup()
    return _PG_STORE


############################################
# Redis
########################################
load_dotenv()

REDIS_URL = os.getenv("REDIS_URL")
_SESSION_STORE = None  # lazy singleton
_CHECKPOINTER = None # 체크포인터 캐싱

def get_session_store(ttl_seconds=24 * 3600, prefix="chatsession:"):
    """SessionStore 인스턴스를 1회 생성해 재사용한다."""
    global _SESSION_STORE
    if _SESSION_STORE is None:
        _SESSION_STORE = SessionStore(ttl_seconds=ttl_seconds, prefix=prefix)
    return _SESSION_STORE

def get_checkpointer():
    """RedisSaver 기반 체크포인터를 생성/캐시. 실패하면 None."""
    global _CHECKPOINTER
    if _CHECKPOINTER is not None:
        return _CHECKPOINTER
    if not REDIS_URL:
        return None
    try:
        cp = RedisSaver(REDIS_URL)
        cp.setup()  # 연결/키스페이스 준비
        _CHECKPOINTER = cp
    except Exception:
        _CHECKPOINTER = None
    return _CHECKPOINTER

class SessionStore:
    def __init__(
        self,
        ttl_seconds=24 * 3600,
        prefix="chatsession:",
        socket_timeout=2.0,
        connect_timeout=2.0,
    ):
        # 타임아웃/재시도 옵션을 잡아 연결 장애 시 호출부가 실패를 감지하도록 한다.
        self.r = redis.Redis.from_url(
            REDIS_URL,
            socket_timeout=socket_timeout,
            socket_connect_timeout=connect_timeout,
            retry_on_timeout=True,
        )
        self.ttl = ttl_seconds
        self.p = prefix

    def _k(self, sid, *parts):
        return ":".join([self.p + sid, *parts])

    # 내부 유틸: 바이트 길이 확인
    @staticmethod
    def _too_large(payload: str | bytes, max_bytes: int) -> bool:
        size = len(payload if isinstance(payload, bytes) else payload.encode("utf-8"))
        return size > max_bytes

    # runtime
    def set_runtime(self, sid, data: dict):
        self.r.setex(self._k(sid, "runtime"), self.ttl, json.dumps(data))

    def get_runtime(self, sid):
        raw = self.r.get(self._k(sid, "runtime"))
        return json.loads(raw) if raw else None

    # recent messages
    def push_msg(
        self,
        sid,
        msg_json: str,
        maxlen: int = 10,
        max_bytes: int = 200_000,
        summarize_fn: Optional[Callable[[str, int], str]] = None,
    ) -> bool:
        """
        최근 메시지 push. max_bytes를 넘으면 summarize_fn으로 축약 후 저장 시도, 그래도 크면 저장하지 않음.
        """
        if self._too_large(msg_json, max_bytes):
            if summarize_fn:
                msg_json = summarize_fn(msg_json, max_bytes)
            if self._too_large(msg_json, max_bytes):
                return False
        key = self._k(sid, "recent_msgs")
        pipe = self.r.pipeline()
        pipe.lpush(key, msg_json)
        pipe.ltrim(key, 0, maxlen - 1)
        pipe.expire(key, self.ttl)
        pipe.execute()
        return True

    def get_msgs(self, sid):
        data = self.r.lrange(self._k(sid, "recent_msgs"), 0, -1)
        return [item.decode("utf-8") for item in data] if data else []

    # dialog summary
    def set_summary(self, sid, summary: dict):
        self.r.setex(self._k(sid, "dialog_summary"), self.ttl, json.dumps(summary))

    def get_summary(self, sid):
        raw = self.r.get(self._k(sid, "dialog_summary"))
        return json.loads(raw) if raw else None

    # working set (per item)
    def set_working_item(
        self,
        sid,
        item_id,
        data: dict,
        max_bytes: int = 500_000,
        summarize_fn: Optional[Callable[[dict, int], dict]] = None,
    ) -> bool:
        """
        작업 중 아티팩트 저장. max_bytes 초과 시 summarize_fn으로 축약 후 저장 시도, 그래도 크면 저장하지 않음.
        """
        payload = json.dumps(data)
        if self._too_large(payload, max_bytes):
            if summarize_fn:
                data = summarize_fn(data, max_bytes)
                payload = json.dumps(data)
            if self._too_large(payload, max_bytes):
                return False
        self.r.setex(self._k(sid, "working_set", item_id), self.ttl, payload)
        return True

    def get_working_item(self, sid, item_id):
        raw = self.r.get(self._k(sid, "working_set", item_id))
        return json.loads(raw) if raw else None

    def list_working_items(self, sid) -> Dict[str, Any]:
        """working_set 하위 키를 모두 반환."""
        pattern = self._k(sid, "working_set", "*")
        results = {}
        for key in self.r.scan_iter(pattern):
            raw = self.r.get(key)
            if not raw:
                continue
            # key 형식: prefix + sid : working_set : item_id
            parts = key.decode("utf-8").split(":")
            item_id = parts[-1] if parts else ""
            results[item_id] = json.loads(raw)
        return results

    def clear_session(self, sid):
        """세션 관련 키를 모두 삭제."""
        keys = [
            self._k(sid, "runtime"),
            self._k(sid, "recent_msgs"),
            self._k(sid, "dialog_summary"),
        ]
        # working_set 전체 삭제
        for key in self.r.scan_iter(self._k(sid, "working_set", "*")):
            keys.append(key)
        if keys:
            self.r.delete(*keys)

def load_session_context(session_id: str) -> dict:
    """Redis 단기 메모리 스냅샷을 반환(runtime, recent_msgs, dialog_summary)."""
    store = get_session_store()
    return {
        "runtime": store.get_runtime(session_id),
        "recent_msgs": store.get_msgs(session_id),
        "dialog_summary": store.get_summary(session_id),
    }


def save_session_context(
    session_id: str,
    runtime: Optional[dict] = None,
    summary: Optional[dict] = None,
    messages: Optional[List[str]] = None,
    working_items: Optional[Dict[str, dict]] = None,
    msg_max_bytes: int = 200_000,
    working_max_bytes: int = 500_000,
) -> None:
    """
    단기 메모리(runtime, summary, messages, working_set)를 일괄 저장.
    - messages는 리스트 순서대로 push (최신이 앞쪽으로 저장됨)
    - working_items는 {item_id: data}
    """
    store = get_session_store()
    if runtime is not None:
        store.set_runtime(session_id, runtime)
    if summary is not None:
        store.set_summary(session_id, summary)
    if messages:
        for msg in reversed(messages):  # 최신이 리스트 마지막이라면 역순 push
            store.push_msg(session_id, msg, max_bytes=msg_max_bytes)
    if working_items:
        for item_id, data in working_items.items():
            store.set_working_item(session_id, item_id, data, max_bytes=working_max_bytes)


def promote_session_to_longterm(
    session_id: str,
    user_id: str,
    delete_after: bool = True,
) -> Dict[str, Any]:
    """
    세션 단기 메모리를 장기 저장소(Django 모델)로 승격하고 Redis 세션을 정리한다.
    - dialog_summary -> UserOutcomeLog(summary)
    - working_set    -> UserCoachingLog(findings/recommendations)
    """
    store = get_session_store()
    runtime = store.get_runtime(session_id) or {}
    dialog_summary = store.get_summary(session_id)
    working = store.list_working_items(session_id)

    outcome_id = f"session:{session_id}"
    rubric_scores = runtime.get("rubric_scores")
    score = runtime.get("score")

    with transaction.atomic():
        UserOutcomeLog.objects.update_or_create(
            user_id=user_id,
            outcome_id=outcome_id,
            defaults={
                "kind": runtime.get("kind", "session"),
                "summary": json.dumps(dialog_summary) if dialog_summary else None,
                "link": runtime.get("link"),
                "score": score,
                "created_at": timezone.now(),
            },
        )

        for item_id, data in working.items():
            UserCoachingLog.objects.update_or_create(
                user_id=user_id,
                coaching_id=f"{session_id}:{item_id}",
                defaults={
                    "artifact_id": item_id,
                    "findings": data,
                    "recommendations": data.get("recommendations") if isinstance(data, dict) else None,
                    "rubric_scores": rubric_scores,
                    "created_at": timezone.now(),
                },
            )

    if delete_after:
        store.clear_session(session_id)

    return {"outcome_id": outcome_id, "coaching_saved": len(working)}


##################################################
# 사용자별 Memory 저장 방식
###################################################

class UserSpecificStoreBackend(StoreBackend):
    """사용자별 namespace를 자동으로 적용하는 StoreBackend"""

    def __init__(self, runtime, user_id: str, category: str):
        super().__init__(runtime)
        self.namespace = ("users", user_id, category)

    def _get_namespace(self):
        """항상 사용자별 namespace 반환"""
        return self.namespace


def make_user_backend(user_id: str):
    """특정 사용자를 위한 CompositeBackend 생성"""

    def backend_factory(runtime):
        return CompositeBackend(
            default=StateBackend(runtime),  # 일시적 저장소
            routes={
                # 사용자별 namespace를 가진 영구 저장소
                "/memories/": UserSpecificStoreBackend(runtime, user_id, "memories"),
                "/user/": UserSpecificStoreBackend(runtime, user_id, "user"),
            },
        )

    return backend_factory
