---
globs:
  - "supabase/**"
---

# Database Rules (Supabase)

## 테이블: card_sales
Supabase 프로젝트 ID: `pgwvcabukadiyraushcj` (리전: ap-northeast-2)

### 스키마 (20개 컬럼)
- `id` UUID PK (auto-generated)
- `transaction_date` TIMESTAMPTZ — 거래일시 (KST → UTC 변환 저장)
- `card_number` VARCHAR(20) — 마스킹된 카드번호
- `approval_number` VARCHAR(20) — 승인번호
- `approval_amount` BIGINT — 승인금액
- `acquirer` / `issuer` VARCHAR(20) — 매입사 / 발급사
- `transaction_type` VARCHAR(10) — 승인 또는 취소
- 기타: vat_amount, tip_amount, status, installment_months, is_check_card, simple_pay, deposit_date, deposit_amount, fee, store_name, terminal_id, created_at

### 제약조건
- **Unique**: `(approval_number, acquirer, transaction_date)` — upsert 시 중복 방지 기준
- **Index**: `transaction_date DESC`, `acquirer`

### 마이그레이션
- `001_create_tables.sql` — 테이블 + 인덱스 생성
- DDL 변경 시 Supabase MCP `apply_migration` 또는 대시보드 SQL Editor 사용
