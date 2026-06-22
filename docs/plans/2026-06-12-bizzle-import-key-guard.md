# Bizzle 매출 가져오기 변조방지 가드 — sales-rader 구현 작업서 (key 주체)

- 작성일: 2026-06-19
- 상태: 구현 대기
- **SSOT(전체 설계)**: `whale-erp-front/docs/plans/sales/2026-06-12-bizzle-import-tamper-guard.md`
- 관련 작업서: `whale-erp-api/docs/plans/sales/2026-06-12-bizzle-import-tamper-guard-relay.md`

> 이 문서는 SSOT 중 **sales-rader(FastAPI)** 가 할 일만 추린 구현 체크리스트다.
> sales-rader 는 이 가드에서 **key 의 생성·저장·검증·소멸을 모두 담당하는 주체**다.

---

## 0. 역할 (요약)

3계층 `front → whale-erp-api(:8080) → sales-rader(:7000)` 에서 sales-rader 는:
1. `POST /api/import-key` 로 **1회용 key 생성·인메모리 저장**(TTL 60s) 후 `{ key }` 반환
2. `POST /api/scrape-aggregate` 진입부에서 `X-Sales-Import-Key` 헤더 **검증 → 소멸**, 실패 시 **Bizzle 호출 전에 419 반환**

- sales-rader 는 `127.0.0.1:7000` 로 localhost 바인딩(외부 직접 접근 불가) → 호출은 항상 api 경유.
- **단일 인스턴스 전제**(SSOT §7-2 확정) → 인메모리 저장으로 충분. 다중화 시 Redis 등으로 교체 필요.

---

## 1. 변경 파일 목록

| 파일 | 변경 |
|------|------|
| `backend/app/services/import_key_store.py` | **신규** — 인메모리 key store (TTL 60s, 1회용) |
| `backend/app/routers/scraper.py` | `POST /api/import-key` 신규, `scrape-aggregate` 진입부 key 검증·소멸 |
| `backend/app/models.py` | `ImportKeyRequest`(`{year, month}`), `ImportKeyResponse`(`{key}`) 추가 |

---

## 2. 인메모리 key store (`import_key_store.py` 신규)

```python
import secrets
import threading
import time

_TTL_SECONDS = 60

class _Entry:
    __slots__ = ("year", "month", "expires_at")
    def __init__(self, year: int, month: int, expires_at: float):
        self.year = year
        self.month = month
        self.expires_at = expires_at

class ImportKeyStore:
    """1회용 import key 저장소. 단일 인스턴스 전제(인메모리).

    - issue(): 추측 불가 난수 key 생성 → (year, month, expires_at=now+60s) 저장
    - consume(): key 존재·미만료·(year, month) 일치 시 즉시 삭제하고 True. 아니면 False(소멸 안 함).
    """
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._store: dict[str, _Entry] = {}

    def issue(self, year: int, month: int) -> str:
        key = secrets.token_urlsafe(32)
        with self._lock:
            self._purge_expired_locked()
            self._store[key] = _Entry(year, month, time.monotonic() + _TTL_SECONDS)
        return key

    def consume(self, key: str, year: int, month: int) -> bool:
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return False
            # 검증 통과 여부와 무관하게, 매칭된 key 는 1회용이므로 삭제 후 판정
            del self._store[key]
            if entry.expires_at < time.monotonic():
                return False
            return entry.year == year and entry.month == month

    def _purge_expired_locked(self) -> None:
        now = time.monotonic()
        expired = [k for k, e in self._store.items() if e.expires_at < now]
        for k in expired:
            del self._store[k]

import_key_store = ImportKeyStore()
```
- `time.monotonic()` 사용(시스템 시계 변경에 영향받지 않음).
- `threading.Lock`: FastAPI 가 sync 라우터를 스레드풀에서 실행할 수 있으므로 방어. async-only 로 운영하면 생략 가능.
- 만료 청소는 issue 시 lazy 수행(버려진 key 가 무한 적재되지 않게). 별도 백그라운드 태스크 불필요.

---

## 3. 모델 (`models.py`)

```python
class ImportKeyRequest(BaseModel):
    year: int
    month: int

class ImportKeyResponse(BaseModel):
    key: str
```

---

## 4. 라우터 (`routers/scraper.py`)

### 4.1 신규: key 발급
```python
from fastapi import Header
from fastapi.responses import JSONResponse
from app.models import ImportKeyRequest, ImportKeyResponse
from app.services.import_key_store import import_key_store

@router.post("/import-key", response_model=ImportKeyResponse)
async def issue_import_key(request: ImportKeyRequest):
    """1회용 import key 발급 (TTL 60s). whale-erp-api 경유로만 호출됨."""
    key = import_key_store.issue(request.year, request.month)
    return ImportKeyResponse(key=key)
```
> 응답은 raw `{ "key": "..." }`. front 가 보는 `{ data: { key } }` envelope 는 whale-erp-api 가 씌운다.

### 4.2 변경: scrape-aggregate 진입부 검증 → 소멸 → 실패 419
```python
@router.post("/scrape-aggregate")
async def trigger_scrape_aggregate(
    request: ScrapeRequest,
    x_sales_import_key: str | None = Header(default=None, alias="X-Sales-Import-Key"),
):
    # key 바인딩은 (year, month). start_date 가 항상 해당 월 1일이므로 거기서 도출해 대조한다(SSOT §4.2).
    year, month = request.start_date.year, request.start_date.month
    if not x_sales_import_key or not import_key_store.consume(x_sales_import_key, year, month):
        # Bizzle 을 건드리기 전에 거부
        return JSONResponse(
            status_code=419,
            content={"code": "INVALID_IMPORT_KEY", "message": "잘못된 데이터 가져오기 방식입니다."},
        )
    return await scrape_sale_dep(
        request.start_date, request.end_date, request.login_id, request.login_pw
    )
```
- **검증 순서 주의**: key 검증·소멸을 `scrape_sale_dep`(Bizzle 로그인·스크래핑) **이전**에 둔다. 실패 시 외부 사이트를 건드리지 않는다.
- `consume()` 은 매칭된 key 를 검증 통과 여부와 무관하게 삭제(1회용). 정상 흐름에선 60s 안에 도착하므로 항상 통과.
- 419 응답 body 의 `code: "INVALID_IMPORT_KEY"` 는 whale-erp-api 와의 약속. api 는 status 419 로 분기한다(api 작업서 §4.3).

---

## 5. 주의 / 결정 사항
- **419 비표준 상태코드**: FastAPI `JSONResponse(status_code=419)` 로 그대로 내려보낼 수 있다(프레임워크 제약 없음).
  whale-erp-api 쪽은 enum 제약이 있어 별도 처리가 필요하다(api 작업서 §5). 419→400 으로 단순화하기로 하면 양쪽을 함께 바꾼다.
- **key 바인딩 (year, month)**: `scrape-aggregate` 가 받는 `start_date`/`end_date` 와 무관하게 `start_date` 의 연·월만으로 대조.
  정밀 비교(start/end 전체)는 월 경계 계산 불일치로 멀쩡한 key 가 거부될 위험이 있어 채택하지 않는다(SSOT §4.2).
- **기존 `scrape-aggregate` 동작 불변**: 헤더 검증만 앞단에 추가하고, 스크래핑·응답(resobj 패스스루)은 그대로 둔다.
- `.env`/CORS/`frontend_origin` 등 기존 설정 변경 없음.

---

## 6. 검증 체크리스트
- [ ] `POST /api/import-key {year, month}` → `{ key }` 반환, 60s 후 만료
- [ ] 올바른 key 로 `scrape-aggregate` 호출 → 정상 스크래핑, key 1회용 소멸(재사용 시 419)
- [ ] 헤더 없음 / 틀린 key / 만료 key / (year,month) 불일치 → **419 `INVALID_IMPORT_KEY`**, Bizzle 미호출
- [ ] 419 케이스에서 `scrape_sale_dep` 가 호출되지 않음(로그로 확인)
