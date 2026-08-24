# Wire Transfer Guidelines and Operations

## 1. Domestic Wire Transfers (Fedwire)
Domestic wire transfers are processed through the Fedwire Funds Service. The standard daily cut-off time for same-day domestic wire processing is 4:30 PM EST. Any wire submitted after this time will be processed on the next business day. The standard transaction limit for retail accounts is $50,000 per day. For corporate accounts, limits are configured individually up to $5,000,000 per day, subject to multi-signature authorization.

## 2. International Wire Transfers (SWIFT)
International wire transfers require the recipient's full legal name, physical address, IBAN or account number, and the receiving bank's SWIFT/BIC code. SWIFT transfers typically take 2 to 5 business days to clear, depending on intermediary bank routing. A flat processing fee of $35 USD applies to all outgoing international wires. Incoming international wires incur a $15 USD processing fee. Our primary SWIFT clearing code for US Dollar transactions is **ABCBUS33XXX**.

## 3. High-Value Transfer Verification (HVTV)
Any wire transfer exceeding $100,000 USD must undergo the High-Value Transfer Verification (HVTV) protocol. This requires a dual-authorization check:
1. Outbound phone call verification to the registered account holder using a pre-established security phrase.
2. Secondary sign-off by a senior operations manager in the banking backend.
If verification fails or contact cannot be established within 4 hours, the wire is automatically cancelled, and a security hold is placed on the account.

## 4. Recalling Fraudulent or Erroneous Wires
Once a wire transfer is completed and sent to the Federal Reserve or SWIFT network, it cannot be unilaterally cancelled. If a transfer was sent in error or due to fraud:
1. Immediately submit a SWIFT MT192 (Request for Cancellation) or Fedwire recall request.
2. Contact the receiving bank's compliance department to request a temporary hold on the funds.
Recalls are processed on a "best-efforts" basis, and recovery of funds is not guaranteed if the recipient has already withdrawn them.
