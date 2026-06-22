import asyncio
import sys
import threading
from datetime import date, datetime
from urllib.parse import urlencode

from playwright.async_api import async_playwright
from app.config import settings
from app.database import supabase
from app.models import ScrapeResponse


def mask_card_number(cdno: str) -> str:
    """카드번호 마스킹: 앞6자리 + **** + 뒤4자리"""
    if len(cdno) >= 10:
        return f"{cdno[:6]}****{cdno[-4:]}"
    return cdno


def parse_transaction_date(ts_date: str, ts_time: str) -> str:
    """TSDATE(YYYYMMDD) + TSTIME(HHmmss) → ISO 형식 (KST 명시)"""
    dt = datetime.strptime(f"{ts_date}{ts_time}", "%Y%m%d%H%M%S")
    return dt.isoformat() + "+09:00"


def parse_record(record: dict) -> dict:
    """API 응답 레코드를 DB 저장 형식으로 변환"""
    gbn = record.get("GBN", "0")
    return {
        "transaction_date": parse_transaction_date(record["TSDATE"], record["TSTIME"]),
        "card_number": mask_card_number(record.get("CDNO", "")),
        "approval_number": record.get("AUTHNO", ""),
        "approval_amount": int(record.get("AMT1", 0)),
        "vat_amount": int(record.get("AMT2", 0)),
        "tip_amount": int(record.get("AMT3", 0)),
        "acquirer": record.get("ACQHID", ""),
        "issuer": record.get("HID", ""),
        "transaction_type": "취소" if gbn == "1" else "승인",
        "status": record.get("NRSPC_NM", ""),
        "installment_months": record.get("ISTMMON", "00"),
        "is_check_card": record.get("CHECK_FLAG", "") == "체크카드",
        "simple_pay": record.get("SIMPLE_PAY_NAME", "") or "",
        "deposit_date": record.get("DEPDATE", "") or "",
        "deposit_amount": int(record.get("DPAMT", 0)),
        "fee": int(record.get("TSFEE", 0)),
        "store_name": record.get("COMP_NAME", "") or "",
        "terminal_id": record.get("TERMID", "") or "",
    }


async def scrape_card_sales(start_date: date, end_date: date) -> ScrapeResponse:
    """카드매출 스크래핑 진입점.

    Windows에서 uvicorn --reload는 SelectorEventLoop를 강제하는데, 이 루프는
    서브프로세스를 지원하지 않아 Playwright가 NotImplementedError로 실패한다.
    Windows에서는 Playwright를 전용 ProactorEventLoop 스레드에서 실행해 우회한다.
    그 외 플랫폼/no-reload 환경에서는 그대로 현재 루프에서 실행한다.
    """
    if sys.platform == "win32":
        return await asyncio.to_thread(
            _run_in_proactor_loop, start_date, end_date
        )
    return await _scrape_card_sales(start_date, end_date)


def _run_in_proactor_loop(start_date: date, end_date: date) -> ScrapeResponse:
    """별도 스레드에서 ProactorEventLoop를 만들어 스크래핑 코루틴을 실행."""
    box: dict = {}

    def runner() -> None:
        loop = asyncio.ProactorEventLoop()
        asyncio.set_event_loop(loop)
        try:
            box["result"] = loop.run_until_complete(
                _scrape_card_sales(start_date, end_date)
            )
        except BaseException as exc:  # noqa: BLE001 - 호출자에게 그대로 전달
            box["error"] = exc
        finally:
            loop.close()

    thread = threading.Thread(target=runner)
    thread.start()
    thread.join()
    if "error" in box:
        raise box["error"]
    return box["result"]


async def _scrape_card_sales(start_date: date, end_date: date) -> ScrapeResponse:
    """Bizzle 사이트에 로그인 후 카드매출 데이터를 API로 수집하여 Supabase에 저장"""
    all_records = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        try:
            # 1. 로그인
            await page.goto(settings.target_site_url, wait_until="networkidle", timeout=30000)
            await page.fill("#USER_ID", settings.target_login_id)
            await page.fill("#USER_P", settings.target_login_pw)
            await page.click("#btnLogin")
            await page.wait_for_url("**/main.do", timeout=15000)

            # 2. 매출 페이지 접근 (세션 설정)
            await page.goto(settings.target_sales_url, wait_until="networkidle", timeout=30000)

            # 3. 쿠키 획득
            cookies = await context.cookies()
            cookie_str = "; ".join(f"{c['name']}={c['value']}" for c in cookies)

            # 4. API로 페이지별 데이터 수집
            sdate = start_date.strftime("%Y%m%d")
            edate = end_date.strftime("%Y%m%d")
            current_page = 0

            while True:
                form_data = urlencode({
                    "SDATE": sdate,
                    "EDATE": edate,
                    "STIME": "000000",
                    "ETIME": "235959",
                    "GBN": "-1",
                    "HID_GBN": "1",
                    "CURRPAGE": str(current_page),
                    "NRSPC_TYPE": "0",
                    "REJEC_TYPE": "2",
                    "CDNO": "",
                    "AUTHNO": "",
                    "CATID": "",
                    "COMP_NO": "",
                    "COMP_IDX": "",
                    "ORGCOD": "",
                })

                response = await page.evaluate(
                    """async (params) => {
                        const res = await fetch('/svc/sales/selectSaleDetail.do', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                            body: params
                        });
                        return await res.json();
                    }""",
                    form_data,
                )

                obj = response.get("resobj", {}).get("OBJ", [])
                if not obj:
                    break

                all_records.extend(obj)

                # 페이지네이션 확인 (TOTPAGE는 마지막 페이지 인덱스, 0부터 시작)
                tot_page = obj[0].get("TOTPAGE", 0) if obj else 0
                current_page += 1
                if current_page > tot_page:
                    break

        finally:
            await browser.close()

    # 5. Supabase에 upsert
    new_count = 0
    for record in all_records:
        parsed = parse_record(record)
        try:
            supabase.table("card_sales").upsert(
                parsed,
                on_conflict="approval_number,acquirer,transaction_date",
            ).execute()
            new_count += 1
        except Exception:
            pass

    return ScrapeResponse(
        status="success",
        total_count=len(all_records),
        new_count=new_count,
        message=f"{len(all_records)}건 수집, {new_count}건 저장 완료",
    )


# ---------------------------------------------------------------------------
# 카드매출 집계(getSaleDepMonth) 패스스루
# whale-erp 화면(일/월별 집계)용. Bizzle 응답(resobj)을 가공 없이 그대로 반환한다.
# 기존 selectSaleDetail(거래단위) 수집과 별개의 진입점.
# ---------------------------------------------------------------------------
async def scrape_sale_dep(
    start_date: date,
    end_date: date,
    login_id: str | None = None,
    login_pw: str | None = None,
) -> dict:
    """Bizzle getSaleDepMonth(날짜×카드사 집계) 호출 후 resobj를 그대로 반환.

    login_id/login_pw 가 주어지면 해당 자격증명으로 로그인하고(사용자별 계정),
    없으면 .env(TARGET_LOGIN_ID/PW)로 폴백한다.

    Windows에서는 Playwright 서브프로세스 제약을 우회하기 위해 전용 ProactorEventLoop
    스레드에서 실행한다(scrape_card_sales와 동일 패턴).
    """
    if sys.platform == "win32":
        return await asyncio.to_thread(
            _run_sale_dep_in_proactor_loop, start_date, end_date, login_id, login_pw
        )
    return await _scrape_sale_dep(start_date, end_date, login_id, login_pw)


def _run_sale_dep_in_proactor_loop(
    start_date: date,
    end_date: date,
    login_id: str | None = None,
    login_pw: str | None = None,
) -> dict:
    """별도 스레드에서 ProactorEventLoop를 만들어 집계 스크래핑 코루틴을 실행."""
    box: dict = {}

    def runner() -> None:
        loop = asyncio.ProactorEventLoop()
        asyncio.set_event_loop(loop)
        try:
            box["result"] = loop.run_until_complete(
                _scrape_sale_dep(start_date, end_date, login_id, login_pw)
            )
        except BaseException as exc:  # noqa: BLE001 - 호출자에게 그대로 전달
            box["error"] = exc
        finally:
            loop.close()

    thread = threading.Thread(target=runner)
    thread.start()
    thread.join()
    if "error" in box:
        raise box["error"]
    return box["result"]


async def _scrape_sale_dep(
    start_date: date,
    end_date: date,
    login_id: str | None = None,
    login_pw: str | None = None,
) -> dict:
    """Bizzle 로그인 후 getSaleDepMonth.do를 호출해 집계 응답(resobj 포함)을 그대로 반환.

    - 자격증명: login_id/login_pw 우선, 없으면 .env 폴백.
    - DATE: 조회 월 1일(YYYYMMDD). getSaleDepMonth는 해당 월 전체를 반환한다.
    - COMPNO/COMPIDX: 로그인 세션 쿠키(curCompNo/curCompIdx)에서 확보. 없으면 빈값(세션 추론).
    - SRC: SMT_VAN(카드 매출만 수집). 취소는 SALE_LIST의 C_AMT/C_CNT로 포함됨.
    - 반환: Bizzle 응답 JSON 전체 `{ "resobj": { "OBJ": { "USER", "SALE_LIST", ... } } }`
    """
    user_id = login_id or settings.target_login_id
    user_pw = login_pw or settings.target_login_pw

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        try:
            # 1. 로그인 (요청 자격증명 우선, 없으면 .env)
            await page.goto(settings.target_site_url, wait_until="networkidle", timeout=30000)
            await page.fill("#USER_ID", user_id)
            await page.fill("#USER_P", user_pw)
            await page.click("#btnLogin")
            await page.wait_for_url("**/main.do", timeout=15000)

            # 2. saledep 페이지 진입 (세션 설정 + referer 확보 + curCompNo 쿠키 세팅)
            await page.goto(settings.target_sales_url, wait_until="networkidle", timeout=30000)

            # 3. 가맹점 식별자 확보 (세션 쿠키)
            cookies = await context.cookies()
            cookie_map = {c["name"]: c["value"] for c in cookies}
            comp_no = cookie_map.get("curCompNo", "")
            comp_idx = cookie_map.get("curCompIdx", "00")

            # 4. 월별 집계 조회 (DATE=해당 월 1일 → 달 전체 반환)
            date_param = start_date.strftime("%Y%m%d")
            form_data = urlencode({
                "DATE": date_param,
                "COMPNO": comp_no,
                "COMPIDX": comp_idx,
                "SRC": "SMT_VAN",  # 카드 매출만
            })

            result = await page.evaluate(
                """async (params) => {
                    const res = await fetch('/svc/saledep/api/getSaleDepMonth.do', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                        body: params
                    });
                    return await res.json();
                }""",
                form_data,
            )

            return result

        finally:
            await browser.close()
