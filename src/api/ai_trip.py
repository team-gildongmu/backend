# src/api/ai_trip.py
import json, uuid, asyncio, time
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Header, Request, Query
from fastapi.responses import StreamingResponse

from schema.ai_trip import (
    StartSessionRequest, StartSessionResponse,
    MessageRequest, MessageResponse,
    StateResponse
)
from database.redis import get_redis, get_pubsub
from service.itinerary_engine import get_graph, set_status_emitter
from utils.jwt_utils import decode_token  # ★ 인증 디코더 사용

router = APIRouter(prefix="/ai", tags=["AI Trip"])

GRAPH = get_graph()
TTL_SECONDS = 60 * 60 * 6  # 6시간

def _conv_key(user_id: str, session_id: str) -> str:
    return f"conv:{user_id}:{session_id}"

def _status_channel(user_id: str, session_id: str) -> str:
    return f"conv:status:{user_id}:{session_id}"

def _now_ms() -> int:
    return int(time.time() * 1000)

# ---- 인증 유틸 ----
def _require_user_id_from_header(authorization: Optional[str]) -> str:
    """Authorization: Bearer <token> 에서 user_id/email 추출. 실패 시 401."""
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    token = authorization.split(" ", 1)[1].strip()
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user_id = str(payload.get("user_id") or payload.get("sub") or "")

    # user_id 없으면 email로 대체 (문자열 키로 쓰기 좋음)
    if not user_id:
        email = payload.get("email")
        if not email:
            raise HTTPException(status_code=401, detail="Token payload missing user id/email")
        user_id = email
    return user_id

def _require_user_id_for_sse(authorization: Optional[str], token_qs: Optional[str]) -> str:
    """
    SSE는 헤더를 못 싣는 경우가 많으니 ?token= 도 허용.
    1) Authorization header 우선
    2) 없으면 ?token= 으로 decode
    """
    if authorization:
        return _require_user_id_from_header(authorization)
    if token_qs:
        payload = decode_token(token_qs)
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid or expired token (query)")
        user_id = str(payload.get("user_id") or payload.get("sub") or payload.get("email") or "")
        if not user_id:
            raise HTTPException(status_code=401, detail="Token payload missing user id/email")
        return user_id
    raise HTTPException(status_code=401, detail="Auth token required (Authorization or ?token=)")

# ---- Redis 상태 emitter 등록 (모듈 전역 1회) ----
def _redis_status_emitter(payload: Dict[str, Any]):
    user_id = payload.get("user_id", "anon")
    sid     = payload.get("session_id")
    if not sid:
        return
    chan = _status_channel(user_id, sid)
    get_redis().publish(chan, json.dumps(payload, ensure_ascii=False))

# 최초 import 시 1회 등록
set_status_emitter(_redis_status_emitter)

@router.post("/session/start", response_model=StartSessionResponse)
def start_session(
    body: StartSessionRequest,
    authorization: str | None = Header(None),
):
    user_id = _require_user_id_from_header(authorization)
    sid = uuid.uuid4().hex[:12]
    key = _conv_key(user_id, sid)

    state: Dict[str, Any] = {
        "userQuery": "시작",
        "origin": (body.origin.dict() if body.origin else None),
        "days": body.days,
        "mode": body.mode,
        "tags": body.tags or [],
        "pois": [],
        "stays": [],
        "plan": {},
        "status": {"step": "INIT", "message": "세션 시작"},
        "_meta": {"createdAt": _now_ms()},
        "history": [], # 멀티턴 대화 히스토리
        "_user_id": user_id,
        "_session_id": sid,
    }
    r = get_redis()
    r.setex(key, TTL_SECONDS, json.dumps(state, ensure_ascii=False))
    return StartSessionResponse(session_id=sid)

@router.post("/session/{sid}/message", response_model=MessageResponse)
def send_message(
    sid: str,
    body: MessageRequest,
    authorization: str | None = Header(None),
):
    user_id = _require_user_id_from_header(authorization)
    key = _conv_key(user_id, sid)
    r = get_redis()

    raw = r.get(key)
    if not raw:
        raise HTTPException(status_code=404, detail="세션이 만료되었거나 존재하지 않습니다.")
    state = json.loads(raw)

    hist = state.get("history", [])
    hist.append({"role": "user", "text": body.message, "ts": _now_ms()})

    state["userQuery"] = body.message
    if body.origin is not None:
        state["origin"] = body.origin.dict()
    if body.days is not None:
        state["days"] = body.days
    if body.mode is not None:
        state["mode"] = body.mode
    if body.tags is not None:
        state["tags"] = body.tags

    state["_user_id"] = user_id
    state["_session_id"] = sid
    state["history"] = hist

    out = GRAPH.invoke(state)
    plan   = out.get("plan", {})
    status = out.get("status", {"step": "DONE", "message": "완료되었습니다."})

    hist.append({"role": "assistant", "plan": plan, "ts": _now_ms()})

    chan = _status_channel(user_id, sid)
    r.publish(chan, json.dumps({
        "user_id": user_id, "session_id": sid,
        "step": "RESULT", "plan": plan, "ts": _now_ms()
    }, ensure_ascii=False))
    r.publish(chan, json.dumps({
        "user_id": user_id, "session_id": sid,
        "step": "DONE", "message": "완료되었습니다.", "ts": _now_ms()
    }, ensure_ascii=False))

    out["history"] = hist
    r.setex(key, TTL_SECONDS, json.dumps(out, ensure_ascii=False))

    return MessageResponse(plan=plan, status=status)

@router.get("/session/{sid}/state", response_model=StateResponse)
def get_state(
    sid: str,
    authorization: str | None = Header(None),
):
    user_id = _require_user_id_from_header(authorization)
    key = _conv_key(user_id, sid)
    r = get_redis()
    raw = r.get(key)
    if not raw:
        raise HTTPException(status_code=404, detail="세션이 만료되었거나 존재하지 않습니다.")
    return StateResponse(state=json.loads(raw))

@router.get("/session/{sid}/events")
async def stream_events(
    sid: str,
    request: Request,
    authorization: str | None = Header(None),
    token: str | None = Query(default=None, description="SSE용 토큰(헤더 대체)")
):
    """
    Server-Sent Events (SSE)
    - 헤더에 Authorization: Bearer <token> 또는
    - 쿼리스트링 ?token=<token> 둘 중 하나로 인증
    """
    user_id = _require_user_id_for_sse(authorization, token)
    chan = _status_channel(user_id, sid)

    def format_sse(data: str) -> str:
        return f"data: {data}\n\n"

    async def event_gen():
        pubsub = get_pubsub()
        pubsub.subscribe(chan)
        try:
            while True:
                if await request.is_disconnected():
                    break
                msg = pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if msg and isinstance(msg.get("data"), str):
                    yield format_sse(msg["data"])
                await asyncio.sleep(0.2)
        finally:
            try:
                pubsub.unsubscribe(chan)
                pubsub.close()
            except Exception:
                pass

    return StreamingResponse(event_gen(), media_type="text/event-stream")
