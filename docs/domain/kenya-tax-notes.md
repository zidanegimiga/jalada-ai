# Kenya tax notes

These notes come from preparing a real 2025 individual return. They are context for design, not tax advice. Verify each point against the Kenya Revenue Authority or a tax professional before relying on it in product logic.

## Tax year and filing
- The individual tax year is 1 January to 31 December.
- The return is due 30 June of the following year. Late filing costs at least KES 2,000.
- Income and costs belong to the year they were received or paid. A project paid across two years is split across two returns.

## Kinds of money in
| Kind | Treated as | Evidence |
|---|---|---|
| Salary | Employment income; tax deducted by the employer through payroll (Pay As You Earn) | P9 form, the employer's yearly summary; payslips |
| Consultancy or freelance fees | Business income; some payers withhold 5% and issue a withholding certificate | Withholding certificate with a serial number, invoices |
| Support from relatives and friends | Not income for tax, but useful to explain deposits | Note of who sent it and why |
| Transfers between own accounts | Not income | Both account statements |
| Refunds | Not income | Original payment and refund record |

## Withholding tax
- A certificate shows payer name and tax number, transaction date, gross amount, rate and tax withheld.
- Withheld tax is a credit against the year's tax, not the final tax.
- The same certificate can be downloaded or shared twice; duplicates must be detected by serial number.

## Costs
- Only costs for earning business income can be deducted, and only against business income. Employment income gets no expense deductions.
- Items that last years, such as a laptop, are claimed over time as a capital allowance, not all at once.
- Daily travel between home and a regular workspace is usually commuting, not a business cost.
- Since 2024, costs generally need an electronic tax invoice from the seller (eTIMS, the Kenya Revenue Authority's electronic invoicing system) to be allowed.
- Foreign subscriptions cannot produce eTIMS invoices; keep the email receipt and the card or bank record.

## The iTax return form (individual resident)
The Excel return groups figures into sheets that the tax view should mirror:
| Sheet | What goes in |
|---|---|
| A_Basic_Info | Tax number, period, yes or no questions, bank details for refunds |
| F_Employment_Income | Employer tax number, name, gross pay |
| B_Profit_Loss_Account_Self | Business income (consultancy fees on line 1.2) and operating expenses |
| E2 capital allowance sheets | Assets claimed over time |
| M_Details_of_PAYE_Deducted | Taxable salary and tax deducted by each employer |
| O_WHT_Credits | Each withholding certificate: payer, serial number, date, amount |
| T_Tax_Computation | Pension, housing levy and health insurance deductions; the result |

## M-Pesa
- Every transaction has a unique code, which is the key for spotting duplicates between forwarded messages and statements.
- Full statements are PDFs protected with a password sent to the user. The password must never be stored.
