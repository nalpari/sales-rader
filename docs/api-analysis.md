# Bizzle (스마트로) 카드매출 API 분석

## 대상 사이트

- **사이트**: Bizzle (스마트로 가맹점 관리 시스템)
- **로그인 URL**: `https://bizzle.smartro.co.kr/login/login.do`
- **메인 URL**: `https://bizzle.smartro.co.kr/main.do`
- **매출 상세 URL**: `https://bizzle.smartro.co.kr/svc/sales/saleDetail.do`

## 인증

| 항목 | 값 |
|------|-----|
| 로그인 방식 | ID/PW 폼 로그인 |
| ID 필드 | `#USER_ID` |
| PW 필드 | `#USER_P` |
| 로그인 버튼 | `#btnLogin` (a 태그, JS 이벤트 바인딩) |
| 인증 API | `POST /login/loginVerify.do` |
| 세션 유지 | 쿠키 기반 |

## 매출 데이터 API

### 엔드포인트

```
POST https://bizzle.smartro.co.kr/svc/sales/selectSaleDetail.do
```

### 요청 파라미터

| 파라미터 | 설명 | 예시 |
|----------|------|------|
| `SDATE` | 조회 시작일 (YYYYMMDD) | `20260401` |
| `EDATE` | 조회 종료일 (YYYYMMDD) | `20260407` |
| `STIME` | 조회 시작시간 | `000000` |
| `ETIME` | 조회 종료시간 | `235959` |
| `GBN` | 거래구분 (-1: 전체) | `-1` |
| `HID_GBN` | 카드사 구분 (1: 전체) | `1` |
| `CURRPAGE` | 페이지 번호 (0부터) | `0` |
| `NRSPC_TYPE` | 응답 유형 | `0` |
| `REJEC_TYPE` | 거절 유형 | `2` |
| `CDNO` | 카드번호 필터 | (빈값) |
| `AUTHNO` | 승인번호 필터 | (빈값) |
| `CATID` | 카테고리 | (빈값) |
| `COMP_NO` | 가맹점번호 | (빈값=전체) |
| `COMP_IDX` | 가맹점 IDX | (빈값=전체) |
| `ORGCOD` | 원거래 코드 | (빈값) |

### 응답 구조

```json
{
  "resobj": {
    "MSG": null,
    "MSG2": null,
    "OBJ": [ ... ]  // 거래 레코드 배열
  }
}
```

### 페이지네이션

- 한 페이지당 **50건**
- `TOT_CNT`: 전체 건수
- `TOTPAGE`: 전체 페이지 수
- `CURRPAGE`: 현재 페이지 (0부터 시작)

### 거래 레코드 필드

| 필드 | 설명 | 예시 | DB 저장 |
|------|------|------|---------|
| `TSDATE` | 거래일자 (YYYYMMDD) | `20260407` | O |
| `TSTIME` | 거래시간 (HHmmss) | `174413` | O |
| `CDNO` | 카드번호 (전체) | `4689140002980401` | O |
| `AUTHNO` | 승인번호 | `00969892` | O |
| `AMT1` | 승인금액 | `6900` | O |
| `ACQHID` | 매입사 | `현대` | O |
| `HID` | 발급사 | `현대` | O |
| `NRSPC_NM` | 거래상태 | `승인` | O |
| `GBN` | 거래구분 (0: 승인, 1: 취소) | `0` | O |
| `ISTMMON` | 할부개월 (00: 일시불) | `00` | O |
| `CHECK_FLAG` | 체크카드 여부 | `체크카드` / `` | O |
| `SIMPLE_PAY_NAME` | 간편결제 | `삼성페이` / `` | O |
| `DEPDATE` | 입금예정일 | `` | O |
| `DPAMT` | 입금예정액 | `0` | O |
| `TSFEE` | 수수료 | `0` | O |
| `AMT2` | 부가세 | `0` | O |
| `AMT3` | 봉사료 | `627` | O |
| `COMP_NAME` | 가맹점명 | `힘이나는커피생활 젊음의거리점` | O |
| `TERMID` | 단말기번호 | `2188219004` | O |
| `TAXNO` | 사업자번호 | `6642101278` | - |
| `TAXIDX` | 사업자 IDX | `00` | - |
| `ACQBID` | 매입사 사업자번호 | `830553325` | - |
| `MTRCNO` | 매입처 번호 | `0004894851` | - |
| `TR_TYPE` | 거래 타입 (IC/MS) | `IC` | - |
| `NRSPC_MSG` | 응답 코드 | `00` | - |
| `HCODE_MSG` | 에러 메시지 | `` | - |
| `ORGDATE` | 원거래일자 (취소 시) | `` | - |
| `ORGTIME` | 원거래시간 (취소 시) | `` | - |
| `TOT_CNT` | 총 건수 (메타) | `149` | - |
| `TOT_AMT` | 총 금액 (메타) | `838200` | - |
| `TOTPAGE` | 총 페이지 (메타) | `2` | - |
| `CURRPAGE` | 현재 페이지 (메타) | `0` | - |

## 수집 방식

HTML 파싱 없이 **세션 쿠키를 활용한 직접 API 호출**로 데이터 수집 가능:

1. Playwright로 로그인 → 세션 쿠키 획득
2. 쿠키를 사용하여 `selectSaleDetail.do` API 직접 호출
3. `CURRPAGE`를 증가시키며 전체 데이터 수집 (50건씩)
