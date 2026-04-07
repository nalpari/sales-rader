---
globs:
  - "frontend/**"
---

# Frontend Rules (Next.js)

## 실행
```bash
cd frontend
npm run dev      # 개발 서버 (port 3000)
npm run build    # 프로덕션 빌드
npm run lint     # ESLint
```

## 스택
- Next.js 16 (App Router) + React 19 + TypeScript 5
- Tailwind CSS 4 + PostCSS

## 페이지 구조
- `/` — 대시보드: 매출 요약 (매입사별 카드 그리드 + 총 매출 히어로)
- `/sales` — 매출 상세: 페이지네이션 테이블 + 날짜 필터

## API 클라이언트
`src/lib/api.ts`에 타입 정의와 fetch 함수가 있다.
- `fetchSales()` → `{ data: CardSale[], total_count: number }` 반환
- `fetchSummary()` → `SalesSummary[]` 반환
- `triggerScrape()` → `ScrapeResponse` 반환
- API base URL: `NEXT_PUBLIC_API_URL` 환경변수 또는 기본 `http://localhost:8000`

## 디자인 시스템
`globals.css`에 시맨틱 CSS 변수 기반 디자인 토큰 정의:
- 컬러: navy, blue, orange, success, danger, surface, border, muted
- 폰트: Calistoga (디스플레이, `.font-display`), Pretendard (본문)
- 유틸리티: `.animate-in` (스태거 입장), `.shimmer` (로딩 스켈레톤)

## 컴포넌트
- `SalesTable` — 페이지네이션 포함 (PageNumbers + PageJumpInput)
- `SalesSummaryCard` — 매입사별 카드 그리드 + 비율 바
- `ScrapeButton` — 날짜 범위 선택 + 수집 실행
- `DateRangeFilter` — 날짜 범위 필터 (헤더에 인라인 배치)
