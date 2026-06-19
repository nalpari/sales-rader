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
