CREATE TABLE card_sales (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  transaction_date TIMESTAMPTZ NOT NULL,       -- 거래일시 (TSDATE + TSTIME)
  card_number VARCHAR(20) NOT NULL,            -- 카드번호 (CDNO, 마스킹 처리)
  approval_number VARCHAR(20) NOT NULL,        -- 승인번호 (AUTHNO)
  approval_amount BIGINT NOT NULL,             -- 승인금액 (AMT1)
  vat_amount BIGINT NOT NULL DEFAULT 0,        -- 부가세 (AMT2)
  tip_amount BIGINT NOT NULL DEFAULT 0,        -- 봉사료 (AMT3)
  acquirer VARCHAR(20) NOT NULL,               -- 매입사 (ACQHID)
  issuer VARCHAR(20) NOT NULL,                 -- 발급사 (HID)
  transaction_type VARCHAR(10) NOT NULL,       -- 거래구분: 승인/취소 (GBN: 0=승인, 1=취소)
  status VARCHAR(10) NOT NULL,                 -- 거래상태 (NRSPC_NM)
  installment_months VARCHAR(5) DEFAULT '00',  -- 할부개월 (ISTMMON, 00=일시불)
  is_check_card BOOLEAN DEFAULT FALSE,         -- 체크카드 여부 (CHECK_FLAG)
  simple_pay VARCHAR(20) DEFAULT '',           -- 간편결제 (SIMPLE_PAY_NAME)
  deposit_date VARCHAR(10) DEFAULT '',         -- 입금예정일 (DEPDATE)
  deposit_amount BIGINT DEFAULT 0,             -- 입금예정액 (DPAMT)
  fee BIGINT DEFAULT 0,                        -- 수수료 (TSFEE)
  store_name VARCHAR(100) DEFAULT '',          -- 가맹점명 (COMP_NAME)
  terminal_id VARCHAR(20) DEFAULT '',          -- 단말기번호 (TERMID)
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_card_sales_date ON card_sales(transaction_date DESC);
CREATE INDEX idx_card_sales_acquirer ON card_sales(acquirer);
CREATE UNIQUE INDEX idx_card_sales_unique ON card_sales(approval_number, acquirer, transaction_date);
