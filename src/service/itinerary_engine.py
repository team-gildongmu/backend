# src/service/itinerary_engine.py
import os, json, re, time, requests
from typing import Dict, Any, List, Optional, TypedDict, Callable, Tuple
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

_STATUS_EMITTER: Optional[Callable[[Dict[str, Any]], None]] = None
def set_status_emitter(fn: Callable[[Dict[str, Any]], None]):
    global _STATUS_EMITTER
    _STATUS_EMITTER = fn

# ---------------------------------------------------------------------
# 언어(i18n) - 상태/문구/엔드포인트
# ---------------------------------------------------------------------
LANG_CFG = {
    "ko": {
        "tour_service": "KorService2",
        "places_language": "ko",
        "region": "KR",
        "i18n": {
            "STATUS_ANALYZE": "사용자의 질문을 분석하고 있어요.",
            "STATUS_TOURAPI": "한국관광공사에서 여행지를 추천하고 있어요.",
            "STATUS_GOOGLE": "여행에 도움이 될 만한 최신 자료를 확인하고 있어요.",
            "STATUS_PLAN": "조금만 기다려주세요, 여행 계획을 완성하고 있어요!",
            "STATUS_DONE": "완료되었습니다.",
            "REASON_POI":  "{name}의 인지도와 접근성, 동선을 고려해 추천합니다.",
            "DESC_POI":    "{name}은(는) 산책과 사진 촬영에 좋은 명소로, 주변 볼거리와 접근성이 좋아요.",
            "REASON_MEAL": "이 일대 대표 맛집으로 동선상 이동이 편리해 추천합니다.",
            "DESC_MEAL":   "{name}은(는) 현지인과 여행객에게 인기 있는 식당으로 식사 시간 방문에 적합해요.",
            "REASON_STAY": "위치와 편의시설, 이동 동선을 고려해 추천합니다.",
            "DESC_STAY":   "{name}은(는) 이동이 편리한 숙소로 일정 전후 휴식에 적합합니다.",
            "DEFAULT_REASON_POI":  "일정 동선에 맞춰 추천합니다.",
            "DEFAULT_REASON_MEAL": "이 일대 대표 맛집으로 추천합니다.",
            "DEFAULT_DESC_STAY":   "주변 숙박 후보"
        }
    },
    "en": {
        "tour_service": "EngService2",
        "places_language": "en",
        "region": "KR",
        "i18n": {
            "STATUS_ANALYZE": "Analyzing your request…",
            "STATUS_TOURAPI": "Fetching recommendations from the Korea Tourism Organization…",
            "STATUS_GOOGLE":  "Checking the latest helpful sources…",
            "STATUS_PLAN":    "One moment—finalizing your itinerary!",
            "STATUS_DONE":    "All set.",
            "REASON_POI":  "Recommended based on popularity, accessibility, and route fit for {name}.",
            "DESC_POI":    "{name} is a pleasant spot for strolling and photos, with easy access to nearby sights.",
            "REASON_MEAL": "A popular local restaurant with convenient access.",
            "DESC_MEAL":   "{name} is popular among locals and travelers; great for mealtimes.",
            "REASON_STAY": "Recommended for its location, amenities, and travel route.",
            "DESC_STAY":   "{name} offers convenient access and comfort for rest before/after your itinerary.",
            "DEFAULT_REASON_POI":  "Recommended to fit today’s route.",
            "DEFAULT_REASON_MEAL": "A representative restaurant in the area.",
            "DEFAULT_DESC_STAY":   "Nearby stay candidates"
        }
    },
    "ja": {
        "tour_service": "JpnService2",
        "places_language": "ja",
        "region": "KR",
        "i18n": {
            "STATUS_ANALYZE": "ご要望を分析しています…",
            "STATUS_TOURAPI": "韓国観光公社からおすすめ情報を取得しています…",
            "STATUS_GOOGLE":  "最新の参考情報を確認しています…",
            "STATUS_PLAN":    "少々お待ちください。旅程を仕上げています！",
            "STATUS_DONE":    "完了しました。",
            "REASON_POI":  "{name}の知名度やアクセス、動線を考慮しておすすめします。",
            "DESC_POI":    "{name}は散策や写真撮影にぴったりの名所で、周辺観光にも便利です。",
            "REASON_MEAL": "エリアの代表的な人気店で、移動の動線にも適しています。",
            "DESC_MEAL":   "{name}は地元の人にも旅行者にも人気の飲食店です。",
            "REASON_STAY": "立地・設備・移動動線を考慮しておすすめします。",
            "DESC_STAY":   "{name}は移動に便利で、旅程の前後の休憩にも最適です。",
            "DEFAULT_REASON_POI":  "本日の動線に合わせておすすめします。",
            "DEFAULT_REASON_MEAL": "このエリアの代表的な飲食店です。",
            "DEFAULT_DESC_STAY":   "周辺の宿泊候補"
        }
    }
}

def _cfg(lang: str) -> dict:
    return LANG_CFG.get((lang or "ko").lower(), LANG_CFG["ko"])

def _set_status(state: dict, step: str):
    # step: ANALYZE | TOURAPI | GOOGLE | PLAN | DONE
    lang = (state.get("lang") or "ko").lower()
    msg = _cfg(lang)["i18n"].get(f"STATUS_{step.upper()}", "")
    state["status"] = {"step": step, "message": msg}
    _log("INFO", f"STATUS[{step}] {msg}")
    if _STATUS_EMITTER:
        try:
            _STATUS_EMITTER({
                "user_id": state.get("_user_id", "anon"),
                "session_id": state.get("_session_id"),
                "step": step,
                "message": msg,
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

def _base_urls(lang: str) -> Tuple[str, str]:
    svc = _cfg(lang)["tour_service"]
    return (f"https://apis.data.go.kr/B551011/{svc}", f"http://apis.data.go.kr/B551011/{svc}")

def _request_with_fallback(path: str, params: dict, timeout: int = 20, lang: str = "ko"):
    https_base, http_base = _base_urls(lang)
    try:
        _log("DEBUG", f"HTTPS 요청: {path} params={params} lang={lang}")
        return SESSION.get(f"{https_base}/{path}", params=params, timeout=timeout)
    except requests.exceptions.SSLError:
        _log("WARN", "HTTPS 실패 → HTTP 폴백")
        return SESSION.get(f"{http_base}/{path}", params=params, timeout=timeout)

def tour_get(path: str, lang: str = "ko", **params):
    r = _request_with_fallback(path, tourapi_params(**params), lang=lang)
    r.raise_for_status()
    js = r.json()
    items = js.get("response", {}).get("body", {}).get("items", {}).get("item", []) or []
    _log("INFO", f"{path} 결과 건수={len(items)} (lang={lang})")
    return items

def _first_image_str(imgs) -> str:
    if not imgs: return ""
    if isinstance(imgs, str): return imgs
    if isinstance(imgs, list) and imgs: return imgs[0]
    return ""

# ---------------------------------------------------------------------
# Tool
# ---------------------------------------------------------------------
@tool("tour_location_based", description="위치기반 관광정보 조회(locationBasedList2).")
def tour_location_based(mapX: float, mapY: float, radius: int = 3000,
                        contentTypeId: Optional[int] = None,
                        arrange: str = "E",
                        numOfRows: int = 30, pageNo: int = 1,
                        lang: str = "ko") -> List[Dict[str, Any]]:
    radius = min(max(100, int(radius)), 20000)
    return tour_get("locationBasedList2", lang=lang, mapX=mapX, mapY=mapY, radius=radius,
                    arrange=arrange, contentTypeId=contentTypeId,
                    numOfRows=numOfRows, pageNo=pageNo)

# ---------------------------------------------------------------------
# 상태 타입 & 파싱 프롬프트
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
    history: List[Dict[str, Any]]
    lang: str  # "ko" | "en" | "ja"
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
AGGRO_TITLE_PATTERNS = ["리스트", "ベスト", "BEST", "Top", "TOP", "추천", "近く", "예약", "할인", "|", ":"]

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
            if not name or _is_aggregator_title(name):
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

def google_places_search(area_kw: str, query: str, type_hint: Optional[str],
                         origin: Optional[Dict[str,float]],
                         lang: str) -> List[Dict[str, Any]]:
    cfg = _cfg(lang)
    q = f"{area_kw} {query}".strip()
    return _places_v1_search_text(q, included_type=type_hint, origin=origin,
                                  radius_m=7000.0, max_count=12,
                                  language=cfg["places_language"], region=cfg["region"])

def _synthesize_desc_reason(name: str, seg_type: str, lang: str = "ko") -> Dict[str, str]:
    i18n = _cfg(lang)["i18n"]
    if seg_type == "POI":
        return {"desc": i18n["DESC_POI"].format(name=name), "reason": i18n["REASON_POI"].format(name=name)}
    if seg_type == "MEAL":
        return {"desc": i18n["DESC_MEAL"].format(name=name), "reason": i18n["REASON_MEAL"]}
    return {"desc": i18n["DESC_STAY"].format(name=name), "reason": i18n["REASON_STAY"]}

# ---------------------------------------------------------------------
# Theme 표준화
# ---------------------------------------------------------------------
CANONICAL_THEMES = [
    "자연", "도심", "야경", "역사", "맛집", "힐링", "신나게", "쇼핑", "문화/예술", "휴양/휴식"
]

THEME_SYNONYMS = {
    "자연": ["자연","숲","공원","산","바다","호수","해변","트레킹","산책","nature","forest","park","mountain","sea","lake","beach","trail","walk","自然","森","公園","山","海","湖","ビーチ","散歩","トレッキング"],
    "도심": ["도심","도시","시내","핫플","카페거리","번화가","다운타운","city","urban","downtown","街","市内","繁華街","ホットプレイス","カフェ通り"],
    "야경": ["야경","야간","밤","루프탑","나이트","nightview","night view","nightscape","rooftop","夜景","夜","ナイト","ルーフトップ"],
    "역사": ["역사","유적","궁","성곽","사적지","한옥","박물관","history","heritage","palace","fortress","hanok","museum","歴史","遺跡","宮","城郭","韓屋","博物館"],
    "맛집": ["맛집","먹방","미식","카페","디저트","식도락","맛있는","food","restaurant","cafe","dessert","gourmet","グルメ","食べ歩き","カフェ","デザート","美食"],
    "힐링": ["힐링","명상","휴식","차분","잔잔","healing","relax","calm","slow","リラックス","ヒーリング","休息","静か","癒し"],
    "신나게": ["신나게","액티비티","레저","놀이공원","익스트림","체험","active","activity","leisure","theme park","amusement","extreme","experience","アクティブ","レジャー","体験","遊園地","エクストリーム"],
    "쇼핑": ["쇼핑","아울렛","백화점","시장","플리마켓","쇼핑몰","shopping","outlet","mall","department","market","フリマ","アウトレット","デパート","マーケット","モール"],
    "문화/예술": ["문화","예술","전시","공연","뮤지컬","갤러리","아트","콘서트","culture","art","exhibition","performance","musical","gallery","concert","文化","芸術","展示","公演","ギャラリー","アート","コンサート"],
    "휴양/휴식": ["휴양","휴식","스파","온천","리조트","호캉스","resort","relaxation","spa","hot spring","onsen","hotelcation","休養","温泉","スパ","リゾート","ホカンス"]
}

THEME_I18N = {
    "자연": {"ko":"자연","en":"Nature","ja":"自然"},
    "도심": {"ko":"도심","en":"City/Urban","ja":"街・市内"},
    "야경": {"ko":"야경","en":"Night View","ja":"夜景"},
    "역사": {"ko":"역사","en":"History/Heritage","ja":"歴史・遺跡"},
    "맛집": {"ko":"맛집","en":"Foodie","ja":"グルメ"},
    "힐링": {"ko":"힐링","en":"Healing/Relax","ja":"ヒーリング"},
    "신나게": {"ko":"신나게","en":"Active/Leisure","ja":"アクティブ"},
    "쇼핑": {"ko":"쇼핑","en":"Shopping","ja":"ショッピング"},
    "문화/예술": {"ko":"문화/예술","en":"Culture/Arts","ja":"文化・芸術"},
    "휴양/휴식": {"ko":"휴양/휴식","en":"Resort/Relax","ja":"休養・休息"},
}

def _map_theme_from_text(value: str) -> Optional[str]:
    s = (value or "").lower()
    for t in CANONICAL_THEMES:
        if s == t.lower():
            return t
    for allowed, kws in THEME_SYNONYMS.items():
        for kw in kws:
            if kw.lower() in s:
                return allowed
    return None

def _pick_theme(existing_theme: Any, tags: List[str]) -> str:
    if isinstance(existing_theme, str):
        m = _map_theme_from_text(existing_theme)
        if m: return m
    elif isinstance(existing_theme, list):
        for v in existing_theme:
            m = _map_theme_from_text(str(v))
            if m: return m
    for t in tags or []:
        m = _map_theme_from_text(str(t))
        if m: return m
    return "도심"

def _localize_theme(canonical: str, lang: str) -> str:
    return THEME_I18N.get(canonical, {"ko": canonical, "en": canonical, "ja": canonical}).get(lang, canonical)

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
    return re.sub(r"[^a-z0-9가-힣ぁ-んァ-ンー一-龥]", "", t)

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

def _backfill_images_with_google(items: List[Dict[str, Any]], state: "TripState"):
    lang = (state.get("lang") or "ko").lower()
    origin = state.get("origin")
    for it in items:
        if it.get("provider") == "tourapi" and not it.get("image"):
            title = it.get("title") or ""
            if not title: continue
            try:
                found = google_places_search("", title, None, origin, lang)
                if found and found[0].get("images"):
                    it["image"] = found[0]["images"][0]
            except Exception as e:
                _log("WARN", f"image backfill failed for '{title}': {e}")

# ---------------------------------------------------------------------
# LangGraph 노드
# ---------------------------------------------------------------------
def node_parse_query(state: "TripState"):
    _set_status(state, "ANALYZE")
    _log("INFO", f"node_parse_query: {state['userQuery']}")
    out = llm_fast.invoke(SYSTEM_PARSE_PROMPT.format(query=state["userQuery"]))
    text = getattr(out, "content", out)
    parsed = robust_json(text, {"days": state.get("days", 1), "mode": state.get("mode", "walk"), "tags": [], "area": None})

    q = state["userQuery"]
    if any(tok in q for tok in ["내 주변", "내주변", "근처", "가까운", "주변", "near me", "nearby", "近く"]):
        parsed["area"] = None

    days = int(parsed.get("days", state.get("days", 1)) or 1)
    mode = parsed.get("mode", state.get("mode", "walk")) or "walk"
    tags = parsed.get("tags", [])
    area = parsed.get("area")
    return {**state, "days": days, "mode": mode, "tags": tags, "area": area}

def node_resolve_area(state: "TripState"):
    area_name = (state.get("area") or "").strip()
    if not area_name:
        if state.get("origin"):
            _log("INFO", "지역명 없음 → 기존 origin 사용")
            return state
        _log("WARN", "지역명/기존 origin 모두 없음 → 이후 Places-only 보강")
        return state

    geo = _geocode_text(area_name, region="KR")
    if geo:
        state["origin"] = {"mapX": geo["mapx"], "mapY": geo["mapy"]}
        _log("INFO", f"지오코딩 좌표 반영: ({geo['mapx']},{geo['mapy']})")
    else:
        _log("WARN", "지오코딩 실패 → 기존 origin 유지(없으면 Places-only)")
    return state

def _build_google_only_candidates(state: "TripState") -> (List[Dict[str, Any]], List[Dict[str, Any]]):
    lang = (state.get("lang") or "ko").lower()
    area_kw = state.get("area") or {"ko":"내 주변","en":"near me","ja":"近く"}.get(lang, "내 주변")
    origin  = state.get("origin")

    poi_raw  = google_places_search(area_kw, {"ko":"관광지","en":"tourist spots","ja":"観光地"}.get(lang, "관광지"),
                                    "tourist_attraction", origin, lang)
    meal_raw = google_places_search(area_kw, {"ko":"맛집","en":"restaurants","ja":"グルメ"}.get(lang, "맛집"),
                                    "restaurant", origin, lang)
    stay_raw = google_places_search(area_kw, {"ko":"호텔","en":"hotels","ja":"ホテル"}.get(lang, "호텔"),
                                    "lodging", origin, lang)

    def to_item(r: Dict[str, Any], seg_type: str) -> Optional[Dict[str, Any]]:
        if not r.get("coords"): return None
        syn = _synthesize_desc_reason(r["title"], seg_type, lang)
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

def node_fetch_pois(state: "TripState"):
    lang = (state.get("lang") or "ko").lower()
    i18n_defaults = _cfg(lang)["i18n"]

    if state.get("origin"):
        _set_status(state, "TOURAPI")
        x, y = state["origin"]["mapX"], state["origin"]["mapY"]
        try:
            with ThreadPoolExecutor(max_workers=3) as ex:
                futs = {
                    ex.submit(tour_location_based.invoke, {"mapX": x, "mapY": y, "radius": 7000,
                                                           "contentTypeId": cid, "arrange": "E", "numOfRows": n,
                                                           "lang": lang})
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
            _set_status(state, "GOOGLE")
            pois, stays2 = _build_google_only_candidates(state)
            pois  = [p for p in pois  if _valid(p)]
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
            _set_status(state, "GOOGLE")
            gp_pois, gp_stays = _build_google_only_candidates(state)
            if need_poi:  g_pois += [x for x in gp_pois if x["type"] == "POI"]
            if need_meal: g_pois += [x for x in gp_pois if x["type"] == "MEAL"]
            if need_stay: g_stays += gp_stays

        pois = []
        for it in spots:
            item = {
                "type": "POI", "title": it.get("title"), "desc": it.get("desc") or "",
                "reason": it.get("reason") or i18n_defaults["DEFAULT_REASON_POI"],
                "coords": it["coords"], "provider": it.get("provider"), "source": it.get("source")
            }
            imgs = (it.get("images") or [])[:3]
            item["image"] = _first_image_str(imgs)
            pois.append(item)

        for it in eats:
            item = {
                "type": "MEAL", "title": it.get("title"), "desc": it.get("desc") or "",
                "reason": it.get("reason") or i18n_defaults["DEFAULT_REASON_MEAL"],
                "coords": it["coords"], "provider": it.get("provider"), "source": it.get("source")
            }
            imgs = (it.get("images") or [])[:3]
            item["image"] = _first_image_str(imgs)
            pois.append(item)

        for it in g_pois:
            imgs = (it.get("images") or [])[:3]
            it["image"] = _first_image_str(imgs)
            it.pop("images", None)
            pois.append(it)

        stays_std = []
        for it in stays:
            item = {
                "type": "STAY", "title": it.get("title"),
                "desc": it.get("desc") or i18n_defaults["DEFAULT_DESC_STAY"],
                "reason": it.get("reason") or i18n_defaults["REASON_STAY"],
                "coords": it["coords"], "provider": it.get("provider"), "source": it.get("source")
            }
            imgs = (it.get("images") or [])[:3]
            item["image"] = _first_image_str(imgs)
            stays_std.append(item)

        for it in g_stays:
            imgs = (it.get("images") or [])[:3]
            it["image"] = _first_image_str(imgs)
            it.pop("images", None)
            stays_std.append(it)

        _backfill_images_with_google(pois, state)
        _backfill_images_with_google(stays_std, state)

        pois      = _dedup_by_title([p for p in pois if _valid(p)])
        stays_std = _dedup_by_title([s for s in stays_std if _valid(s)])
        _log("INFO", f"최종 후보: 관광지+음식점 {len(pois)}개, 숙박 {len(stays_std)}개")
        return {**state, "pois": pois, "stays": stays_std}

    _set_status(state, "GOOGLE")
    pois, stays = _build_google_only_candidates(state)
    pois  = _dedup_by_title([p for p in pois  if _valid(p)])
    stays = _dedup_by_title([s for s in stays if _valid(s)])
    _log("INFO", f"최종 후보(Places-only): POI/MEAL {len(pois)}개, STAY {len(stays)}개")
    return {**state, "pois": pois, "stays": stays}

def node_build_itinerary(state: "TripState"):
    _set_status(state, "PLAN")
    _log("INFO", f"node_build_itinerary: days={state.get('days')}, tags={state.get('tags')}, pois={len(state.get('pois', []))}, stays={len(state.get('stays', []))}")
    lang = (state.get("lang") or "ko").lower()

    if not state.get("pois"):
        themes_from_tags = list(dict.fromkeys(state.get("tags", [])))
        canonical = _pick_theme(None, themes_from_tags)
        plan = {
            "title":"", "subtitle":"", "keywords": [], "days": [], "stays": [], "summary": "",
            "themes": themes_from_tags,
            "theme_canonical": canonical,
            "theme": _localize_theme(canonical, lang)
        }
        _set_status(state, "DONE")
        return {**state, "plan": plan}

    pois_text  = json.dumps(state["pois"][:50], ensure_ascii=False)
    stays_text = json.dumps(state["stays"][:8],  ensure_ascii=False)

    if lang == "en":
        head_user  = "User query (latest):"
        head_tags  = "Preference tags:"
        head_total = f"Total {state['days']} day(s) itinerary."
        head_pois  = "- Candidates (POI/MEAL) JSON:"
        head_stays = "- Stay candidates JSON:"
        head_rules = "Rules:"
        rule1 = "- 1-day: stay is optional."
        rule2 = '- 2+ days: put stays only in the "stays" list, not inside daily segments.'
        rule3 = "- Per day: 2–3 POIs + 1–2 MEALs. Group by proximity."
        rule4 = '- Each item: title, desc, reason, images(array), coords(required), provider("tourapi"|"google"), source(required).'
        rule5 = "- Final JSON keys: title(<=15 chars), subtitle(<=40), keywords(5–10), days(segments[]), stays, summary(3–4 sentences)"
        rule6 = '- days.segment.type is "POI" or "MEAL".'
        lang_clause = "Write the entire output in English only."
    elif lang == "ja":
        head_user  = "直近のユーザー要望:"
        head_tags  = "嗜好タグ:"
        head_total = f"合計 {state['days']}日 の行程です。"
        head_pois  = "- 候補(観光/グルメ) JSON:"
        head_stays = "- 宿泊候補 JSON:"
        head_rules = "作成ルール:"
        rule1 = "- 1日コース：宿泊は含まなくても良い。"
        rule2 = '- 2日以上：宿泊は日別セグメントに入れず、“stays”のみに記載。'
        rule3 = "- 各日：POI 2～3か所 + 食事 1～2件。近い動線でまとめる。"
        rule4 = '- 各項目：title, desc, reason, images(配列), coords(必須), provider("tourapi"|"google"), source(必須)。'
        rule5 = "- 最終JSONキー：title(15文字以内), subtitle(40文字以内), keywords(5～10), days(segments配列), stays, summary(3～4文)"
        rule6 = '- days.segment.typeは"POI"または"MEAL"。'
        lang_clause = "出力のすべての文字列は日本語のみで記載してください。"
    else:
        head_user  = "사용자의 여행 질의(가장 최근):"
        head_tags  = "성향 태그:"
        head_total = f"총 {state['days']}일 일정입니다."
        head_pois  = "- 후보(관광지/음식점) JSON:"
        head_stays = "- 숙박 후보 JSON:"
        head_rules = "코스 구성 규칙:"
        rule1 = "- 1일 코스: 숙박은 포함하지 않아도 됨."
        rule2 = '- 2일 이상: 숙박은 하루 일정에 넣지 말고, 별도로 stays 리스트로만 제공.'
        rule3 = "- 매일 관광지(POI) 2~3곳 + 음식점(MEAL) 1~2곳. 가까운 동선으로 묶기."
        rule4 = '- 각 항목은 title, desc, reason, images(배열), coords(필수), provider("tourapi"|"google"), source(필수).'
        rule5 = "- 최종 JSON 키: title(<=15자), subtitle(<=40자), keywords(5~10개), days(segments 배열), stays, summary(3~4문장)"
        rule6 = '- days.segment.type은 "POI" 또는 "MEAL".'
        lang_clause = "출력은 전부 한국어로 작성해 주세요."

    prompt = f"""
{head_user} {state['userQuery']}
{head_tags} {state.get('tags', [])}
{head_total}

{head_pois}
{pois_text}
{head_stays}
{stays_text}

{head_rules}
{rule1}
{rule2}
{rule3}
{rule4}
{rule5}
{rule6}
{lang_clause}
"""
    out  = llm.invoke(prompt)
    plan = robust_json(getattr(out, "content", out),
                       {"title":"", "subtitle":"", "keywords": [], "days": [], "stays": [], "summary": ""})

    catalog_index: Dict[str, Dict[str, Any]] = {}
    for it in (state.get("pois", []) + state.get("stays", [])):
        k = _norm_title(it.get("title"))
        if not k: continue
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
            imgs = imgs[:3]
            s["images"] = imgs

            if not isinstance(s.get("coords"), dict):
                s["coords"] = {"mapx": None, "mapy": None}

            k = _norm_title(s.get("title"))
            meta = catalog_index.get(k, {})
            if not s.get("provider"): s["provider"] = meta.get("provider")
            if not s.get("source"):   s["source"]   = meta.get("source")
            if s["coords"].get("mapx") is None or s["coords"].get("mapy") is None:
                if meta.get("coords"): s["coords"] = meta["coords"]
            if not s.get("images"): s["images"] = (meta.get("images") or [])[:3]

            s["image"] = _first_image_str(s.get("images"))
            s.pop("images", None)

            if _valid({"title": s.get("title"), "coords": s.get("coords"),
                       "provider": s.get("provider"), "source": s.get("source")}):
                cleaned.append(s)
        return cleaned

    for day in plan.get("days", []):
        segs = day.get("segments", [])
        day["segments"] = _clean_segments_strict(segs)

    plan["stays"] = _clean_segments_strict(plan.get("stays", []))

    canonical = _pick_theme(plan.get("theme"), state.get("tags", []))
    plan["theme_canonical"] = canonical
    plan["theme"] = _localize_theme(canonical, lang)

    _set_status(state, "DONE")
    return {**state, "plan": plan}

# ---------------------------------------------------------------------
# LangGraph 구성 + export
# ---------------------------------------------------------------------
graph = StateGraph(TripState)
graph.add_node("ParseQuery",     node_parse_query)
graph.add_node("ResolveArea",    node_resolve_area)
graph.add_node("FetchPOIs",      node_fetch_pois)
graph.add_node("BuildItinerary", node_build_itinerary)
graph.set_entry_point("ParseQuery")
graph.add_edge("ParseQuery",  "ResolveArea")
graph.add_edge("ResolveArea", "FetchPOIs")
graph.add_edge("FetchPOIs",   "BuildItinerary")
graph.add_edge("BuildItinerary", END)

_app = graph.compile()

def get_graph():
    return _app

app = _app
