---
globs:
  - "backend/app/services/**"
---

# Scraper Rules (Bizzle 스크래핑)

## 핵심 로직
HTML 파싱이 아닌, Playwright로 로그인 후 세션 쿠키를 활용한 **API 직접 호출** 방식이다.

1. Playwright headless Chromium으로 `#USER_ID`, `#USER_P` 입력 후 `#btnLogin` 클릭
2. `main.do`로 리다이렉트 확인 후 매출 페이지 접근
3. `page.evaluate()`로 `POST /svc/sales/selectSaleDetail.do` 직접 호출
4. 응답 파싱 → Supabase upsert

## 페이지네이션 (치명적 주의)
- Bizzle API의 `TOTPAGE`는 **마지막 페이지 인덱스**(0-based)이다.
- 반드시 `current_page > tot_page`로 비교해야 한다. `>=`를 쓰면 마지막 페이지를 건너뛴다.
- 한 페이지당 50건.

## 타임존 (치명적 주의)
- Bizzle API의 거래시간(TSDATE + TSTIME)은 **KST**이다.
- 저장 시 반드시 `+09:00` 타임존을 명시해야 한다. 생략 시 UTC로 저장되어 프론트에서 +9시간 이중 적용된다.

## 카드번호 마스킹
- `mask_card_number()`: 앞 6자리 + `****` + 뒤 4자리

## Bizzle API 필드 매핑
상세 필드 매핑은 `docs/api-analysis.md` 참조. 주요 필드:
- `TSDATE`/`TSTIME` → transaction_date, `CDNO` → card_number
- `AUTHNO` → approval_number, `AMT1` → approval_amount
- `ACQHID` → acquirer, `HID` → issuer, `GBN` → transaction_type (0=승인, 1=취소)

## Playwright 설치
최초 1회 `playwright install chromium` 실행 필요.
