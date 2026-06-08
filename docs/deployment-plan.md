# 배포 파이프라인 계획서

main 브랜치 push → GitHub Actions 빌드 → Docker 이미지 → Docker Hub push → AWS EC2 배포.

> 이 문서는 `/grill-me` 인터뷰로 합의된 결정들의 기록이다. 구현 전 단계.

## 아키텍처

```
git push (main)
   │
   ▼
GitHub Actions
   ├─ paths-filter: backend/** · frontend/** 변경 감지
   ├─ [backend 변경시]  buildx → Playwright 베이스 이미지 빌드 → Docker Hub push (:latest, :<sha>)
   ├─ [frontend 변경시] buildx → standalone 빌드(--build-arg NEXT_PUBLIC_API_URL) → push (:latest, :<sha>)
   └─ deploy: SSH → EC2 → .env 생성(Secrets) → docker login → compose pull && up -d
                                   │
                                   ▼
                EC2 (Docker, ≥2GB)
                ├─ backend  컨테이너  127.0.0.1:8000
                ├─ frontend 컨테이너  127.0.0.1:3000
                └─ 호스트 Nginx(기존, TLS) ── app.domain→3000 / api.domain→8000
                          │
                          ▼
                    Supabase (외부 SaaS)
```

## 확정된 결정 12개

| # | 항목 | 결정 |
|---|------|------|
| 1 | 배포 범위 | frontend+backend 둘 다 단일 EC2, docker-compose |
| 2 | EC2 | 인스턴스+Docker+compose 준비됨 (프로비저닝 불필요) |
| 3 | 배포 방식 | SSH push → `docker compose pull && up -d` (appleboy/ssh-action) |
| 4 | 설정 관리 | compose는 repo 커밋·복사, `.env`는 배포 때 GitHub Secrets에서 생성 |
| 5 | 노출 | 서브도메인 분리(app./api.) → cross-origin → **CORS env화 필요** |
| 6 | 태깅 | `:latest`+`:<git-sha>`, compose는 sha 핀, private 레포 2개 |
| 7 | 백엔드 이미지 | `mcr.microsoft.com/playwright/python:v1.48.0` (Python ~3.12 수용) |
| 8 | 프론트 이미지 | 멀티스테이지 pnpm + Next `output: 'standalone'` + node:22-slim (sharp musl 이슈 회피로 alpine 대신 slim) |
| 9 | 빌드 범위 | 경로 필터 선택적 빌드 + GHA 빌드 캐시 |
| 10 | 메모리 | ≥2GB → 스왑 불필요, restart:unless-stopped + healthcheck |
| 11 | 스크래핑 | 수동 트리거, cron 없음 (스코프 밖) |
| 12 | 프록시 | 기존 호스트 Nginx 재사용(서브도메인+TLS 구성 완료, 사용자 관리), CI 스코프 밖 |

## 필요한 코드 변경 (repo)

1. `backend/app/config.py` — `frontend_origin` 설정 추가
2. `backend/app/main.py` — `allow_origins=["http://localhost:3000", settings.frontend_origin]` (하드코딩된 localhost 단독 제거)
3. `backend/.env.example` — `FRONTEND_ORIGIN=https://app.domain` 추가
4. `frontend/next.config.ts` — `output: 'standalone'` 추가

## 새로 만들 파일

- `backend/Dockerfile` + `backend/.dockerignore`
- `frontend/Dockerfile` + `frontend/.dockerignore`
- `docker-compose.yml` (루트)
  - 서비스: `backend`, `frontend`
  - `image: <user>/sales-rader-backend:${BACKEND_TAG}` / `...-frontend:${FRONTEND_TAG}`
  - `env_file: .env`
  - `ports: "127.0.0.1:8000:8000"` / `"127.0.0.1:3000:3000"` (직접 노출 차단, Nginx만 통하게)
  - `restart: unless-stopped`, `healthcheck`
- `.github/workflows/deploy.yml`

## GitHub Secrets / Variables

**Secrets (인프라):** `DOCKERHUB_USERNAME`, `DOCKERHUB_TOKEN`, `EC2_HOST`, `EC2_USER`, `EC2_SSH_KEY`

**Secrets (백엔드 런타임 → .env 생성용):** `SUPABASE_URL`, `SUPABASE_KEY`, `TARGET_SITE_URL`, `TARGET_SALES_URL`, `TARGET_LOGIN_ID`, `TARGET_LOGIN_PW`

**Variables (공개값):** `NEXT_PUBLIC_API_URL`(=`https://api.domain`), `FRONTEND_ORIGIN`(=`https://app.domain`)

> `NEXT_PUBLIC_API_URL`은 브라우저에 노출되는 값이라 Secret이 아닌 Variable로 둔다.

## 핵심 로직: sha 핀 + 선택적 빌드

EC2의 `.env`에 `BACKEND_TAG`·`FRONTEND_TAG` 두 줄을 유지한다. 배포 시 **이번에 빌드된 서비스의 태그만** 새 git-sha로 갱신하고, 안 바뀐 쪽은 기존 태그를 유지한 뒤 `docker compose up -d`.

- 불변 배포: 각 배포가 특정 sha에 고정
- 선택적: 한쪽만 바뀌어도 다른 쪽 컨테이너는 안 건드림
- 롤백: `.env`의 해당 태그를 이전 sha로 되돌려 재실행

## 워크플로 설계 (`.github/workflows/deploy.yml`)

- trigger: `push: branches: [main]` + `workflow_dispatch`
- job `changes`: `dorny/paths-filter` → `backend`, `frontend` 불린 출력
- job `build-backend` (if backend changed): buildx → Docker Hub login → `backend/` 빌드 → `:latest`,`:<sha>` push → GHA 캐시
- job `build-frontend` (if frontend changed): buildx → `--build-arg NEXT_PUBLIC_API_URL` → `:latest`,`:<sha>` push → GHA 캐시
- job `deploy` (needs 빌드 잡들): SSH → `/opt/sales-rader`에서 compose·.env 갱신(heredoc, Secrets) → 변경된 서비스 태그만 새 sha로 → `docker login` → `docker compose pull && up -d` → `docker image prune`

## EC2 1회성 부트스트랩 (수동)

1. Docker Hub private 레포 2개 생성 (`sales-rader-backend`, `sales-rader-frontend`)
2. GitHub Secrets/Variables 등록
3. EC2: `docker login`, `/opt/sales-rader` 디렉터리 생성
4. 기존 Nginx upstream이 `127.0.0.1:3000`/`8000`을 가리키는지 1회 확인 (통합 계약)
5. 첫 배포: 두 태그 모두 시드되도록 초기 1회 양쪽 빌드(`workflow_dispatch`)

## 알려진 리스크 (이번 스코프 밖, 기록만)

- **수 분짜리 동기 스크래핑 요청**(`/api/scrape`가 페이지네이션 끝까지 블로킹) → Nginx `proxy_read_timeout`·브라우저 fetch 타임아웃에 취약. 향후 백그라운드 작업 + 폴링/SSE로 개선 권장.
- `docker compose up -d` 재생성 시 수 초 다운타임 (단일 호스트, 수용 가능).
- Playwright chromium 메모리 스파이크 → ≥2GB로 완화.

## 단계별 실행 계획

| 단계 | 작업 | 검증 |
|------|------|------|
| 0 | 코드 변경 (CORS env, standalone) | 로컬 빌드/실행 정상 |
| 1 | Dockerfile·compose 작성 | 로컬 `docker compose up`에서 프론트↔백엔드 통신 |
| 2 | Docker Hub 레포 + Secrets 등록 | 수동 push 1회 성공 |
| 3 | 빌드 워크플로 (경로필터·태깅) | main push 시 올바른 태그로 Hub에 push 확인 |
| 4 | 배포 잡 (SSH·.env 생성·핀) | push→컨테이너 갱신, app./api. 도메인 신버전, 롤백 동작 |
| 5 | 하드닝 (healthcheck·prune·선택 lint) | 헬스체크 통과, 재시작 정책 동작 |
