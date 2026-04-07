# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Sales Rader는 Bizzle(스마트로) 가맹점 관리 시스템에서 카드매출 데이터를 스크래핑하여 Supabase에 저장하고, Next.js 대시보드로 조회하는 시스템이다.

## Architecture

```
sales-rader/
├── backend/     # FastAPI + Playwright (Python 3.13, venv)
├── frontend/    # Next.js 16 + React 19 + Tailwind CSS 4
├── supabase/    # 마이그레이션 SQL
└── docs/        # Bizzle API 분석 문서
```

**데이터 흐름**: Playwright로 Bizzle 로그인 → 세션 쿠키로 `selectSaleDetail.do` API 직접 호출 → Supabase upsert → FastAPI REST API → Next.js 프론트엔드

## Context Rules

역할별 상세 규칙은 `.claude/rules/`에 분리되어 있다. 작업 중인 파일 경로에 따라 자동으로 해당 규칙만 로드된다.

| 규칙 파일 | 적용 대상 | 내용 |
|-----------|-----------|------|
| `backend.md` | `backend/**` | FastAPI 서버 실행, API 엔드포인트, 환경변수 |
| `scraper.md` | `backend/app/services/**` | Bizzle 스크래핑 로직, 페이지네이션, 타임존 |
| `frontend.md` | `frontend/**` | Next.js 실행, 디자인 토큰, 컴포넌트 구조 |
| `database.md` | `supabase/**` | 테이블 스키마, 제약조건, 마이그레이션 |
