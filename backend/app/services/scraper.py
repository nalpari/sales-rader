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
