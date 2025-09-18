# src/service/itinerary_engine.py
import os, json, re, time, requests
from typing import Dict, Any, List, Optional, TypedDict, Callable
from urllib.parse import unquote
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from concurrent.futures import ThreadPoolExecutor, as_completed

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langchain_core.tools import tool

# ---------------------------------------------------------------------
# 환경설정
# ---------------------------------------------------------------------
load_dotenv()
OPENAI_API_KEY         = os.getenv("OPENAI_API_KEY")
TOURAPI_KEY            = os.getenv("TOURAPI_KEY")
GOOGLE_PLACES_API_KEY  = os.getenv("GOOGLE_PLACES_API_KEY")  # Places API(New, v1)
MOBILE_OS              = os.getenv("MOBILE_OS", "WEB")
MOBILE_APP             = os.getenv("MOBILE_APP", "Gildongmu")
BASE_URL_HTTPS         = "https://apis.data.go.kr/B551011/KorService2"
BASE_URL_HTTP          = "http://apis.data.go.kr/B551011/KorService2"
GEOCODE_TIMEOUT        = 10

# LLM
llm      = ChatOpenAI(model="gpt-4o",      temperature=0, openai_api_key=OPENAI_API_KEY)      # 최종 플랜
llm_fast = ChatOpenAI(model="gpt-4o-mini", temperature=0, openai_api_key=OPENAI_API_KEY)      # 파싱용

# ---------------------------------------------------------------------
# 로깅 & 상태 emitter
# ---------------------------------------------------------------------
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

def _log(level: str, msg: str):
    order = {"DEBUG": 10, "INFO": 20, "WARN": 30, "ERROR": 40}
    if order[level] >= order.get(LOG_LEVEL, 20):
        print(f"[{level}] {msg}")

# 외부에서 주입되는 상태 스트림 emitter (Redis 등)
_STATUS_EMITTER: Optional[Callable[[Dict[str, Any]], None]] = None

def set_status_emitter(fn: Callable[[Dict[str, Any]], None]):
    """상태가 바뀔 때마다 호출되는 콜백을 주입"""
    global _STATUS_EMITTER
    _STATUS_EMITTER = fn

def _set_status(state: dict, step: str, message: str):
    state["status"] = {"step": step, "message": message}
    _log("INFO", f"STATUS[{step}] {message}")
    if _STATUS_EMITTER:
        try:
            _STATUS_EMITTER({
                "user_id": state.get("_user_id", "anon"),
                "session_id": state.get("_session_id"),
                "step": step,
                "message": message,
                "ts": int(time.time() * 1000)
            })
        except Exception as e:
            _log("WARN", f"status emitter error: {e}")

# ---------------------------------------------------------------------
# HTTP 세션 & TourAPI 공통
# ---------------------------------------------------------------------
def _normalize_service_key(raw: str) -> str:
    if "%" in raw:
        try:
            return unquote(raw)
        except Exception:
            return raw
    return raw

SERVICE_KEY = _normalize_service_key(TOURAPI_KEY)

def _mk_session() -> requests.Session:
    s = requests.Session()
    retries = Retry(total=3, backoff_factor=0.4,
                    status_forcelist=[429, 500, 502, 503, 504],
                    allowed_methods=["GET", "POST"])
    s.mount("https://", HTTPAdapter(max_retries=retries))
    s.mount("http://",  HTTPAdapter(max_retries=retries))
    return s

SESSION = _mk_session()

def tourapi_params(**kwargs):
    base = dict(serviceKey=SERVICE_KEY, MobileOS=MOBILE_OS, MobileApp=MOBILE_APP, _type="json")
    base.update({k: v for k, v in kwargs.items() if v not in [None, "", [], {}]})
    return base

def _request_with_fallback(path: str, params: dict, timeout: int = 20):
    try:
        _log("DEBUG", f"HTTPS 요청: {path} params={params}")
        return SESSION.get(f"{BASE_URL_HTTPS}/{path}", params=params, timeout=timeout)
    except requests.exceptions.SSLError:
        _log("WARN", "HTTPS 실패 → HTTP 폴백")
        return SESSION.get(f"{BASE_URL_HTTP}/{path}", params=params, timeout=timeout)

def tour_get(path: str, **params):
    r = _request_with_fallback(path, tourapi_params(**params))
    r.raise_for_status()
    js = r.json()
    items = js.get("response", {}).get("body", {}).get("items", {}).get("item", []) or []
    _log("INFO", f"{path} 결과 건수={len(items)}")
    return items

# ---------------------------------------------------------------------
# Tool
# ---------------------------------------------------------------------
@tool("tour_location_based", description="위치기반 관광정보 조회(locationBasedList2).")
def tour_location_based(mapX: float, mapY: float, radius: int = 3000,
                        contentTypeId: Optional[int] = None,
                        arrange: str = "E",
                        numOfRows: int = 30, pageNo: int = 1) -> List[Dict[str, Any]]:
    radius = min(max(100, int(radius)), 20000)
    return tour_get("locationBasedList2", mapX=mapX, mapY=mapY, radius=radius,
                    arrange=arrange, contentTypeId=contentTypeId,
                    numOfRows=numOfRows, pageNo=pageNo)

# ---------------------------------------------------------------------
# 상태 및 파싱 프롬프트
# ---------------------------------------------------------------------
class TripState(TypedDict, total=False):
    userQuery: str
    origin: Dict[str, float]   # {"mapX": lng, "mapY": lat}
    days: int
    mode: str
    area: Optional[str]
    tags: List[str]
    pois: List[Dict[str, Any]]
    stays: List[Dict[str, Any]]
    plan: Dict[str, Any]
    status: Dict[str, str]
    _user_id: str
    _session_id: str

SYSTEM_PARSE_PROMPT = """\
다음 문장에서 여행 일수(기본 1), 이동수단(walk/drive/transit),
성향 태그(자연/도심/야경/역사/맛집/힐링/신나게 등 1~3개), (있다면) 지역명(시/군/구/동/랜드마크)을 추출해 JSON으로.
문장: "{query}"
출력 예시: {{"days":2,"mode":"walk","tags":["맛집"],"area":"홍대"}}"""

def robust_json(s: str, fallback: dict) -> dict:
    try:
        m = re.search(r"\{.*\}", s, re.S)
        return json.loads(m.group(0)) if m else fallback
    except Exception:
        return fallback

# ---------------------------------------------------------------------
# Google Places v1 + OSM(Nominatim)
# ---------------------------------------------------------------------
AGGRO_TITLE_PATTERNS = ["리스트", "베스트", "BEST", "Top", "TOP", "추천", "근처", "예약", "할인", "|", ":"]

def _is_aggregator_title(t: str) -> bool:
    t = t or ""
    return any(tok in t for tok in AGGRO_TITLE_PATTERNS)

def _places_ready() -> bool:
    ok = bool(GOOGLE_PLACES_API_KEY and GOOGLE_PLACES_API_KEY.strip())
    if not ok:
        _log("WARN", "GOOGLE_PLACES_API_KEY 미설정 또는 비어 있음")
    return ok

def _places_v1_headers() -> Dict[str, str]:
    return {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": GOOGLE_PLACES_API_KEY,
        "X-Goog-FieldMask": "places.displayName,places.id,places.location,places.photos,places.types,places.rating,places.googleMapsUri"
    }

def _places_v1_photo_url(photo_name: str, max_px=800) -> str:
    if not (_places_ready() and photo_name):
        return ""
    return f"https://places.googleapis.com/v1/{photo_name}/media?key={GOOGLE_PLACES_API_KEY}&maxWidthPx={max_px}"

def _places_v1_search_text(
    text_query: str,
    included_type: Optional[str] = None,
    origin: Optional[Dict[str, float]] = None,
    radius_m: float = 7000.0,
    max_count: int = 12,
    language: str = "ko",
    region: str = "KR",
) -> List[Dict[str, Any]]:
    if not _places_ready() or not text_query:
        return []
    url = "https://places.googleapis.com/v1/places:searchText"
    body: Dict[str, Any] = {
        "textQuery": text_query,
        "maxResultCount": max_count,
        "languageCode": language,
        "regionCode": region,
    }
    if included_type:
        body["includedType"] = included_type
    if origin and origin.get("mapX") is not None and origin.get("mapY") is not None:
        body["locationBias"] = {
            "circle": {
                "center": {"latitude": float(origin["mapY"]), "longitude": float(origin["mapX"])},
                "radius": float(radius_m),
            }
        }
    try:
        resp = SESSION.post(url, headers=_places_v1_headers(), json=body, timeout=GEOCODE_TIMEOUT)
        js = resp.json()
        places = js.get("places", []) or []
        out = []
        for p in places:
            name = (p.get("displayName", {}) or {}).get("text") or ""
            if not name or _is_aggregator_title(name):  # 리스트/광고 컷
                continue
            loc = p.get("location") or {}
            lat = loc.get("latitude"); lng = loc.get("longitude")
            if lat is None or lng is None:
                continue
            photos = (p.get("photos") or [])[:2]
            images = []
            for ph in photos:
                photo_name = ph.get("name")
                url_photo = _places_v1_photo_url(photo_name)
                if url_photo:
                    images.append(url_photo)
            out.append({
                "title": name,
                "coords": {"mapx": float(lng), "mapy": float(lat)},
                "images": images,
                "provider": "google",
                "place_id": p.get("id"),
                "source": p.get("googleMapsUri") or "",
                "rating": p.get("rating"),
            })
        return out
    except Exception as e:
        _log("WARN", f"Places v1 search 예외: {e}")
        return []

def _geocode_text(query: str, region: str = "KR") -> Optional[Dict[str, float]]:
    res = _places_v1_search_text(query, included_type=None, origin=None, max_count=1, language="ko", region=region)
    if res:
        c = res[0]["coords"]
        return {"mapx": c["mapx"], "mapy": c["mapy"]}
    try:
        headers = {"User-Agent": "Gildongmu/1.0 (contact: dev@example.com)"}
        params = {"q": query, "format": "json", "limit": 1}
        r = SESSION.get("https://nominatim.openstreetmap.org/search", params=params, headers=headers, timeout=GEOCODE_TIMEOUT)
        arr = r.json()
        if arr:
            return {"mapx": float(arr[0]["lon"]), "mapy": float(arr[0]["lat"])}
    except Exception as e:
        _log("WARN", f"Nominatim 지오코딩 예외: {e}")
    return None

def google_places_search(area_kw: str, query: str, type_hint: Optional[str], origin: Optional[Dict[str,float]]) -> List[Dict[str, Any]]:
    q = f"{area_kw} {query}".strip()
    return _places_v1_search_text(q, included_type=type_hint, origin=origin, radius_m=7000.0, max_count=12, language="ko", region="KR")

# ---------------------------------------------------------------------
# Theme 표준화
# ---------------------------------------------------------------------
ALLOWED_THEMES = [
    "자연", "도심", "야경", "역사", "맛집", "힐링", "신나게", "쇼핑", "문화/예술", "휴양/휴식"
]

# 키워드에 해당하면 ALLOWED_THEMES 중 어떤 것인지 매핑
THEME_SYNONYMS = {
    "자연": ["자연", "숲", "공원", "산", "바다", "호수", "해변", "트레킹", "산책"],
    "도심": ["도심", "도시", "시내", "핫플", "카페거리", "번화가", "다운타운"],
    "야경": ["야경", "야간", "밤", "루프탑", "나이트"],
    "역사": ["역사", "유적", "궁", "성곽", "사적지", "한옥", "박물관(역사)"],
    "맛집": ["맛집", "먹방", "미식", "카페", "디저트", "식도락", "맛있는"],
    "힐링": ["힐링", "명상", "휴식", "차분", "잔잔"],
    "신나게": ["신나게", "액티비티", "레저", "놀이공원", "익스트림", "체험"],
    "쇼핑": ["쇼핑", "아울렛", "백화점", "시장", "플리마켓", "쇼핑몰"],
    "문화/예술": ["문화", "예술", "전시", "공연", "뮤지컬", "갤러리", "아트", "콘서트"],
    "휴양/휴식": ["휴양", "휴식", "스파", "온천", "리조트", "호캉스"]
}

def _map_theme_from_text(value: str) -> Optional[str]:
    s = (value or "").lower()
    # 1) 정확일치(허용셋)
    for t in ALLOWED_THEMES:
        if s == t.lower():
            return t
    # 2) 시소러스 포함 매칭
    for allowed, kws in THEME_SYNONYMS.items():
        for kw in kws:
            if kw.lower() in s:
                return allowed
    return None

def _pick_theme(existing_theme: Any, tags: List[str]) -> str:
    """
    - plan에 theme가 문자열로 있으면 그대로 사용(허용 셋이면), 아니면 근사치 매핑
    - plan.theme가 배열이거나, 없으면 tags에서 근사치 매핑
    - 결국 하나의 문자열 반환, 못 정하면 '도심' 기본값
    """
    # plan.theme 우선
    if isinstance(existing_theme, str):
        m = _map_theme_from_text(existing_theme)
        if m: return m
        # 허용 셋이 아니면 근사치가 없더라도 일단 가장 비슷한 것 시도 후 실패 시 tags로
    elif isinstance(existing_theme, list):
        for v in existing_theme:
            m = _map_theme_from_text(str(v))
            if m: return m

    # tags에서 선택
    for t in tags or []:
        m = _map_theme_from_text(str(t))
        if m: return m

    # 그래도 없으면 기본값
    return "도심"

def _synthesize_desc_reason(name: str, seg_type: str) -> Dict[str, str]:
    if seg_type == "POI":
        desc   = f"{name}은(는) 산책과 사진 촬영에 좋은 명소로, 주변 볼거리와 접근성이 좋아요."
        reason = f"{name}의 인지도와 접근성, 동선을 고려해 추천합니다."
    elif seg_type == "MEAL":
        desc   = f"{name}은(는) 현지인과 여행객에게 인기 있는 식당으로 식사 시간 방문에 적합해요."
        reason = f"이 일대 대표 맛집으로 동선상 이동이 편리해 추천합니다."
    else:
        desc   = f"{name}은(는) 이동이 편리한 숙소로 일정 전후 휴식에 적합합니다."
        reason = f"위치와 편의시설, 이동 동선을 고려해 추천합니다."
    return {"desc": desc, "reason": reason}

# ---------------------------------------------------------------------
# 표준화/검증
# ---------------------------------------------------------------------
def attach_images_if_missing(items: List[Dict[str, Any]]):
    for it in items:
        imgs = []
        for k in ("firstimage", "firstimage2", "image"):
            if it.get(k):
                imgs.append(it[k])
        it["images"] = imgs[:3]

def _extract_coords_from_item(it: Dict[str, Any]) -> Optional[Dict[str, float]]:
    try:
        x = it.get("mapx") or it.get("mapX")
        y = it.get("mapy") or it.get("mapY")
        if x is None or y is None:
            return None
        return {"mapx": float(x), "mapy": float(y)}
    except Exception:
        return None

def _std_provider_source(it: Dict[str, Any]):
    it["provider"] = "tourapi"
    cid = it.get("contentid")
    if cid:
        it["source"] = f"https://korean.visitkorea.or.kr/detail/ms_detail.do?cotid={cid}"

def _valid(o: Dict[str, Any]) -> bool:
    if not o.get("title"): return False
    if not isinstance(o.get("coords"), dict): return False
    if o["coords"].get("mapx") is None or o["coords"].get("mapy") is None: return False
    if not o.get("provider"): return False
    if not o.get("source"): return False
    return True

def _norm_title(t: str) -> str:
    t = (t or "").lower()
    return re.sub(r"[^a-z0-9가-힣]", "", t)

def _dedup_by_title(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen = set()
    out = []
    for it in items:
        k = _norm_title(it.get("title"))
        if not k or k in seen:
            continue
        seen.add(k)
        out.append(it)
    return out

# ---------------------------------------------------------------------
# LangGraph 노드
# ---------------------------------------------------------------------
def node_parse_query(state: TripState):
    _set_status(state, "ANALYZE", "사용자의 질문을 분석하고 있어요.")
    _log("INFO", f"node_parse_query: {state['userQuery']}")
    out = llm_fast.invoke(SYSTEM_PARSE_PROMPT.format(query=state["userQuery"]))
    text = getattr(out, "content", out)
    parsed = robust_json(text, {"days": state.get("days", 1), "mode": state.get("mode", "walk"), "tags": [], "area": None})

    q = state["userQuery"]
    if any(tok in q for tok in ["내 주변", "내주변", "근처", "가까운", "주변"]):
        parsed["area"] = None

    days = int(parsed.get("days", state.get("days", 1)) or 1)
    mode = parsed.get("mode", state.get("mode", "walk")) or "walk"
    tags = parsed.get("tags", [])
    area = parsed.get("area")
    return {**state, "days": days, "mode": mode, "tags": tags, "area": area}

def node_resolve_area(state: TripState):
    area_name = (state.get("area") or "").strip()
    if not area_name:
        if state.get("origin"):
            _log("INFO", "지역명 없음 → 기존 origin 사용")
            return state
        _log("WARN", "지역명/기존 origin 모두 없음 → 이후 Places-only 보강")
        return state

    geo = _geocode_text(area_name)
    if geo:
        state["origin"] = {"mapX": geo["mapx"], "mapY": geo["mapy"]}
        _log("INFO", f"지오코딩 좌표 반영: ({geo['mapx']},{geo['mapy']})")
    else:
        _log("WARN", "지오코딩 실패 → 기존 origin 유지(없으면 Places-only)")
    return state

def _build_google_only_candidates(state: TripState) -> (List[Dict[str, Any]], List[Dict[str, Any]]):
    area_kw = state.get("area") or "내 주변"
    origin  = state.get("origin")
    poi_raw  = google_places_search(area_kw, "관광지", "tourist_attraction", origin)
    meal_raw = google_places_search(area_kw, "맛집",    "restaurant",        origin)
    stay_raw = google_places_search(area_kw, "호텔",    "lodging",           origin)

    def to_item(r: Dict[str, Any], seg_type: str) -> Optional[Dict[str, Any]]:
        if not r.get("coords"):
            return None
        syn = _synthesize_desc_reason(r["title"], seg_type)
        return {
            "type": seg_type,
            "title": r["title"],
            "desc": syn["desc"],
            "reason": syn["reason"],
            "images": r.get("images", [])[:3],
            "coords": r["coords"],
            "provider": "google",
            "source": r.get("source"),
            "place_id": r.get("place_id")
        }

    pois_meals, stays = [], []
    for r in poi_raw[:10]:
        it = to_item(r, "POI");  it and pois_meals.append(it)
    for r in meal_raw[:10]:
        it = to_item(r, "MEAL"); it and pois_meals.append(it)
    for r in stay_raw[:8]:
        it = to_item(r, "STAY"); it and stays.append(it)

    return _dedup_by_title(pois_meals), _dedup_by_title(stays)

def node_fetch_pois(state: TripState):
    if state.get("origin"):
        _set_status(state, "TOURAPI", "한국관광공사에서 여행지를 추천하고 있어요.")
        x, y = state["origin"]["mapX"], state["origin"]["mapY"]
        try:
            with ThreadPoolExecutor(max_workers=3) as ex:
                futs = {
                    ex.submit(tour_location_based.invoke, {"mapX": x, "mapY": y, "radius": 7000, "contentTypeId": cid, "arrange": "E", "numOfRows": n})
                    : cid for cid, n in [(12, 20), (39, 20), (32, 10)]
                }
                spots, eats, stays = [], [], []
                for f in as_completed(futs):
                    cid = futs[f]
                    res = f.result() or []
                    if cid == 12: spots = res
                    elif cid == 39: eats = res
                    else: stays = res
        except Exception as e:
            _log("WARN", f"TourAPI 호출 실패 → Places-only 대체: {e}")
            _set_status(state, "GOOGLE", "여행에 도움이 될 만한 최신 자료를 확인하고 있어요.")
            pois, stays2 = _build_google_only_candidates(state)
            pois = [p for p in pois if _valid(p)]
            stays2 = [s for s in stays2 if _valid(s)]
            return {**state, "pois": pois, "stays": stays2}

        attach_images_if_missing(spots); attach_images_if_missing(eats); attach_images_if_missing(stays)
        for it in spots + eats + stays:
            _std_provider_source(it)
            c = _extract_coords_from_item(it)
            it["coords"] = c if c else {"mapx": None, "mapy": None}
            it["images"] = it.get("images", [])[:3]

        MIN_POI, MIN_MEAL, MIN_STAY = 6, 4, 3
        need_poi  = len(spots) < MIN_POI
        need_meal = len(eats)  < MIN_MEAL
        need_stay = len(stays) < MIN_STAY

        g_pois, g_stays = [], []
        if need_poi or need_meal or need_stay:
            _set_status(state, "GOOGLE", "여행에 도움이 될 만한 최신 자료를 확인하고 있어요.")
            gp_pois, gp_stays = _build_google_only_candidates(state)
            if need_poi:
                g_pois += [x for x in gp_pois if x["type"] == "POI"]
            if need_meal:
                g_pois += [x for x in gp_pois if x["type"] == "MEAL"]
            if need_stay:
                g_stays += gp_stays

        pois = []
        for it in spots:
            pois.append({
                "type": "POI", "title": it.get("title"), "desc": it.get("desc") or "",
                "reason": it.get("reason") or "일정 동선에 맞춰 추천합니다.",
                "images": it.get("images", []), "coords": it["coords"],
                "provider": it.get("provider"), "source": it.get("source")
            })
        for it in eats:
            pois.append({
                "type": "MEAL", "title": it.get("title"), "desc": it.get("desc") or "",
                "reason": it.get("reason") or "이 일대 대표 맛집으로 추천합니다.",
                "images": it.get("images", []), "coords": it["coords"],
                "provider": it.get("provider"), "source": it.get("source")
            })
        for it in g_pois:
            pois.append(it)

        stays_std = []
        for it in stays:
            stays_std.append({
                "type": "STAY", "title": it.get("title"), "desc": it.get("desc") or "주변 숙박 후보",
                "reason": it.get("reason") or "동선과 접근성을 고려해 추천합니다.",
                "images": it.get("images", []), "coords": it["coords"],
                "provider": it.get("provider"), "source": it.get("source")
            })
        for it in g_stays:
            stays_std.append(it)

        pois      = _dedup_by_title([p for p in pois if _valid(p)])
        stays_std = _dedup_by_title([s for s in stays_std if _valid(s)])
        _log("INFO", f"최종 후보: 관광지+음식점 {len(pois)}개, 숙박 {len(stays_std)}개")
        return {**state, "pois": pois, "stays": stays_std}

    _set_status(state, "GOOGLE", "여행에 도움이 될 만한 최신 자료를 확인하고 있어요.")
    pois, stays = _build_google_only_candidates(state)
    pois  = _dedup_by_title([p for p in pois  if _valid(p)])
    stays = _dedup_by_title([s for s in stays if _valid(s)])
    _log("INFO", f"최종 후보(Places-only): POI/MEAL {len(pois)}개, STAY {len(stays)}개")
    return {**state, "pois": pois, "stays": stays}

def node_build_itinerary(state: TripState):
    _set_status(state, "PLAN", "조금만 기다려주세요, 여행 계획을 완성하고 있어요!")
    _log("INFO", f"node_build_itinerary: days={state.get('days')}, tags={state.get('tags')}, pois={len(state.get('pois', []))}, stays={len(state.get('stays', []))}")
    if not state.get("pois"):
        _set_status(state, "DONE", "완료되었습니다.")
        return {**state, "plan": {"title":"", "subtitle":"", "days": [], "theme": state.get("tags", [])}}

    pois_text  = json.dumps(state["pois"][:50], ensure_ascii=False)
    stays_text = json.dumps(state["stays"][:8],  ensure_ascii=False)

    prompt = f"""
    사용자의 여행 질의(가장 최근): {state['userQuery']}
    성향 태그: {state.get('tags', [])}
    총 {state['days']}일 일정입니다.

    - 후보(관광지/음식점) JSON:
    {pois_text}
    - 숙박 후보 JSON:
    {stays_text}

    코스 구성 규칙:
    - 1일 코스: 숙박은 포함하지 않아도 됨.
    - 2일 이상: 숙박은 하루 일정에 넣지 말고, 별도로 stays 리스트로만 제공.
    - 매일 관광지(POI) 2~3곳 + 음식점(MEAL) 1~2곳. 가까운 동선으로 묶기.
    - 각 항목은 title, desc, reason, images(배열), coords(필수), provider("tourapi"|"google"), source(필수).
    - 최종 JSON 키: title(<=15자), subtitle(<=40자), keywords(5~10개), days(segments 배열), stays, summary(3~4문장)
    - days.segment.type은 "POI" 또는 "MEAL".
    - 한국어로.
    """
    out  = llm.invoke(prompt)
    plan = robust_json(getattr(out, "content", out),
                       {"title":"", "subtitle":"", "keywords": [], "days": [], "stays": [], "summary": ""})

    catalog_index: Dict[str, Dict[str, Any]] = {}
    for it in (state.get("pois", []) + state.get("stays", [])):
        k = _norm_title(it.get("title"))
        if not k:
            continue
        catalog_index[k] = {
            "provider": it.get("provider"),
            "source":   it.get("source"),
            "coords":   it.get("coords"),
            "images":   (it.get("images") or [])[:3],
        }

    def _clean_segments_strict(segs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        cleaned = []
        for s in segs:
            imgs = s.get("images") or []
            if isinstance(imgs, str): imgs = [imgs]
            s["images"] = imgs[:3]

            if not isinstance(s.get("coords"), dict):
                s["coords"] = {"mapx": None, "mapy": None}

            k = _norm_title(s.get("title"))
            meta = catalog_index.get(k, {})
            if not s.get("provider"):
                s["provider"] = meta.get("provider")
            if not s.get("source"):
                s["source"] = meta.get("source")
            if s["coords"].get("mapx") is None or s["coords"].get("mapy") is None:
                if meta.get("coords"):
                    s["coords"] = meta["coords"]
            if not s.get("images"):
                s["images"] = (meta.get("images") or [])[:3]

            if _valid(s):
                cleaned.append(s)
        return cleaned

    for day in plan.get("days", []):
        segs = day.get("segments", [])
        day["segments"] = _clean_segments_strict(segs)

    plan["stays"] = _clean_segments_strict(plan.get("stays", []))

    # theme 주입 (tags 그대로)
    plan["theme"] = _pick_theme(plan.get("theme"), state.get("tags", []))

    _set_status(state, "DONE", "완료되었습니다.")
    return {**state, "plan": plan}

# ---------------------------------------------------------------------
# LangGraph 구성 + 외부에서 쓸 수 있게 export
# ---------------------------------------------------------------------
graph = StateGraph(TripState)
graph.add_node("ParseQuery",    node_parse_query)
graph.add_node("ResolveArea",   node_resolve_area)
graph.add_node("FetchPOIs",     node_fetch_pois)
graph.add_node("BuildItinerary",node_build_itinerary)
graph.set_entry_point("ParseQuery")
graph.add_edge("ParseQuery", "ResolveArea")
graph.add_edge("ResolveArea", "FetchPOIs")
graph.add_edge("FetchPOIs", "BuildItinerary")
graph.add_edge("BuildItinerary", END)
_app = graph.compile()

def get_graph():
    """FastAPI 라우터에서 호출할 컴파일된 LangGraph"""
    return _app
