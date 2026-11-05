# M-Pesa confirmation messages

How M-Pesa confirmation messages are worded, so the extractor can parse them with rules. All examples here are invented. Names, numbers, codes and links are made up.

## Common parts

- **Transaction code:** the first word, 10 uppercase letters and digits, for example `UK5AB1CD23`. Unique per transaction, and the key for spotting duplicates.
- **Amounts:** `Ksh` followed by digits with comma thousands separators and two decimals, for example `Ksh2,339.58`.
- **Date and time:** `on D/M/YY at H:MM AM|PM`, for example `on 5/11/26 at 2:43 PM`. Day first, two-digit year, no leading zeros.
- **Balance after:** `New M-PESA balance is Ksh...`.
- **Fee:** `Transaction cost, Ksh...`. This is a separate cost of the transaction.
- **Noise to ignore:** the daily limit sentence and the `See all your balances` link.
- Spacing and punctuation are inconsistent: double spaces appear inside names, and the full stop after the time is sometimes missing.

## Sent to a person

```
UK5AB1CD23 Confirmed. Ksh150.00 sent to JANE  WANJIKU 0712345678 on 5/11/26 at 2:43 PM. New M-PESA balance is Ksh2,339.58. Transaction cost, Ksh7.00.  Amount you can transact within the day is 496,142.00. See all your balances now https://example.com/abc
```

Fields: code, amount, counterparty name, counterparty phone, date, time, balance, fee. Direction: out.

## Sent to a paybill or card

```
UK5AB1CD24 Confirmed. Ksh419.00 sent to M-PESA CARD for account Paystack-Shop-Music   +254700000000KE on 5/11/26 at 2:32 PM New M-PESA balance is Ksh2,496.58. Transaction cost, Ksh0.00.Amount you can transact within the day is 496,292.00. See all your balances now https://example.com/def
```

Fields: code, amount, business name (before `for account`), account reference (after it), date, time, balance, fee. Direction: out. The account reference often names the real merchant, so the classifier should read it.

## Received

```
UK4AB1CD25 Confirmed.You have received Ksh1,000.00 from EXAMPLE BANK 1 500000 on 4/11/26 at 4:44 PM New M-PESA balance is Ksh2,211.58.  See all your balances now https://example.com/ghi
```

Fields: code, amount, sender (a bank name and account, or a person's name and phone), date, time, balance. Direction: in. There is no fee line, and no space after `Confirmed.`.

## Other types

Till payments (`paid to`), agent withdrawals, airtime purchases and reversals are not parsed with rules. The detector still recognises them as M-Pesa messages from the code and `Confirmed.`, and the extractor uses the model.
