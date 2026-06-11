"""내부 호출자(whale-erp-api) ↔ sales-rader 간 1회용 HMAC 요청 서명 검증.

sales-rader 의 스크래핑 엔드포인트는 인증이 없고 Bizzle 자격증명을 본문으로 받는다.
포트가 실수로 노출돼도 임의 호출자가 자격증명을 던지지 못하도록, 공유 시크릿으로
서명된 요청만 받아들이며 각 요청은 1회만 유효하다(재사용 불가).

서명 규약(양쪽 서비스가 동일하게 구현):
- 헤더
  - X-Timestamp: 요청 생성 시각(epoch 초)
  - X-Nonce: 요청마다 새로 생성하는 1회용 토큰(UUID 권장)
  - X-Signature: hex(HMAC-SHA256(secret, message))
- message = f"{timestamp}.{nonce}.".encode() + 원본 요청 본문 바이트
  (timestamp/nonce 로 재생 차단 + 본문을 포함해 변조 차단)

검증 규칙:
1. timestamp 가 허용 시간창 밖이면 거부(만료/미래) → 가로챈 요청의 무한 재생 차단
2. 서명 불일치(시크릿 불일치 또는 본문 변조) 거부
3. 이미 사용된 nonce 거부 후 기록 → 시간창 안에서의 재생도 차단(1회용 강제)

운영 주의:
- nonce 저장소는 프로세스 메모리다. Dockerfile 이 uvicorn 을 단일 워커로 띄우므로 유효하다.
  멀티 워커/멀티 인스턴스로 확장하면 공유 저장소(Redis 등)로 교체해야 한다.
- SCRAPE_API_SECRET 미설정 시 검증을 건너뛴다(개발/점진 배포). 운영에서는 반드시 설정한다.
"""

import hashlib
import hmac
import time

from fastapi import HTTPException, Request, status

from app.config import settings

# 사용된 nonce -> 만료 epoch(이 시각 이후 메모리에서 정리). 시간창 밖이면 어차피 timestamp 검증에서 거부된다.
_used_nonces: dict[str, float] = {}


def _purge_expired(now: float) -> None:
    for nonce in [n for n, exp in _used_nonces.items() if exp <= now]:
        _used_nonces.pop(nonce, None)


async def verify_scrape_signature(request: Request) -> None:
    """1회용 HMAC 서명을 검증하는 FastAPI 의존성. 실패 시 401."""
    secret = settings.scrape_api_secret
    if not secret:
        # fail-open: 시크릿 미설정 환경(로컬/초기 배포)에서는 통과. 운영은 반드시 설정.
        return

    timestamp = request.headers.get("X-Timestamp")
    nonce = request.headers.get("X-Nonce")
    signature = request.headers.get("X-Signature")
    if not timestamp or not nonce or not signature:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "missing signature headers")

    try:
        ts = int(timestamp)
    except ValueError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid timestamp")

    now = time.time()
    window = settings.scrape_sig_window_seconds
    if abs(now - ts) > window:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "stale or future timestamp")

    # 본문을 읽어 두면 Starlette 가 캐시하므로 이후 Pydantic 모델 바인딩도 동일 본문을 재사용한다.
    body = await request.body()
    message = f"{timestamp}.{nonce}.".encode() + body
    expected = hmac.new(secret.encode(), message, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "signature mismatch")

    _purge_expired(now)
    if nonce in _used_nonces:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "nonce already used")
    _used_nonces[nonce] = ts + window
