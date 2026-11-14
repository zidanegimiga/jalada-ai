# 02. The user journey today

What a user can do in Jalada AI as it stands, from first visit to deleting their account, and where each step falls short. This is the starting point for the money model and the chat redesign. It describes the code, not the plan.

## 1. Arriving and signing up
- There is no public page. Anyone who is not signed in is sent to `/signin`.
- Sign up takes a name, an email and a password, or Google. Email addresses are not verified.
- If someone signs in with Google using the email of an existing password account that was never verified, the password, the sessions and any Telegram link on that account are removed, and Home shows a notice.

Falls short: nothing explains what Jalada is before sign up. There is no privacy notice, no password reset and no email verification.

## 2. Home
After signing in, Home shows, top to bottom:
1. "Hello, name".
2. This month's money in and out, split into business and personal. It counts confirmed entries only.
3. "N items to check", when anything is waiting.
4. Add evidence: a photo or PDF, or a pasted M-Pesa message.
5. The Telegram card, to link the bot.
6. Recent: the last pieces of evidence and where each one is. The statuses are "Waiting to be read", "Ready to check", "Needs a look", "Saved to ledger", "You already sent this one" and "Could not read". The list refreshes by itself while anything is still being read.

Falls short: a new user sees empty numbers and no guidance.

## 3. Sending evidence
There are three ways in, and all of them end in the same pipeline:
- **Web upload.** A JPEG, PNG or WebP photo or a PDF, up to 10 MB. The file type is checked from its bytes.
- **Web paste.** The text of an M-Pesa message, up to 5,000 characters.
- **Telegram.** Link once: Home gives a code that lasts 10 minutes and a link that opens the bot. After that the user sends photos, PDFs or forwarded messages, and the bot replies "Got it. I will tell you what I find."

Every file is encrypted and kept permanently. The same file sent twice is caught straight away ("You already sent this one").

## 4. Reading it
A background job runs the pipeline on each piece of evidence:
1. **Detect** what it is from its text: an M-Pesa message, a withholding certificate, a statement, a payslip, free text, or a receipt when it is a photo.
2. **Extract** the date, the amount, the direction (in or out), the counterparty, the reference and the M-Pesa code. M-Pesa messages and certificates are read with rules. Photos are read with Tesseract, and the language model chain fills in what rules cannot.
3. **Classify** what it was for. A choice the user has made before for the same counterparty is used first, then rules, then the model. The result is a category and business, personal or unsure.
4. **Verify.** The amount, date and direction must be present and the date must make sense. The same M-Pesa code already recorded makes it a duplicate. Anything with a confidence under 0.8 needs a look.

The result is **one proposed entry per piece of evidence**: "Ready to check" when everything passed, "Needs a look" with reasons when not. Nothing is saved to the ledger without the user confirming it. On Telegram the bot replies with a summary, for example "KSh 150.00 to JANE WANJIKU on 5 Nov 2026: Transport", the reasons if any, and a link to the review screen.

Falls short:
- **A payment message and the receipt for the same purchase become two entries,** so the purchase is counted twice. Only certificates can be linked to their payments.
- A payment message cannot say what the money was for, so the category is a guess based on the counterparty.
- A receipt is read for its total only. Line items are not kept, so one receipt cannot be split between business and personal.
- A statement is detected but not split into its transactions.
- Moving money from M-Pesa to a bank, or withdrawing at an agent, looks like spending.
- Telegram cannot be used to answer or correct anything. Every reply sends the user to the web.

## 5. Checking ("To check")
A list of cards, one per proposed entry, each with the amount, the counterparty, the date, the category or "We could not tell what this was for", and a link to the original.
- **Confirm** saves it to the ledger. Without a category it opens the form instead.
- **Change** opens a form for the date, amount, direction, counterparty and category, then "Save and confirm".
- Evidence that could not be read can be typed in by hand ("Add to ledger").
- Every confirmation teaches the classifier: the next payment to the same counterparty gets the same category.

Falls short: there is no way to reject an entry that is not a real transaction, and no way to say "this is the same payment as that one". The list is cut off at 100 items.

## 6. The ledger
Confirmed entries, filtered by month, direction (in or out) and purpose (business or personal). Withholding certificates appear with the payments linked to them. A certificate page suggests deposits that match it by expected amount, payer and date, and the user links them so the income is counted once.

Falls short: there is no search, no entry detail page showing the evidence and changes, and no editing after confirming.

## 7. Tax time
On the ledger, pick a year and download an Excel workbook with five sheets, grouped the way the iTax return asks. It counts confirmed entries only, and certificate income once.

Falls short: the workbook says nothing about what is missing, such as unconfirmed items, evidence that could not be read, or certificates with no payment linked. There are no other exports, and no statements over other periods.

## 8. Account
- **Download my data:** one zip with everything, originals included.
- **Delete my account:** type the email to confirm. Everything is removed and the user is signed out.
- Sign out.

Falls short: Telegram cannot be unlinked from here, and there is no settings or help page.

## The journey in one line
Send one document, get one proposed entry, confirm it on the web, and see it in the month view and the tax workbook.

## What this means for the redesign
The journey treats every document as a transaction of its own. Real money has two sides: the record that money moved (a payment message, a statement line) and the documents that say what it was for (a receipt, an invoice, a certificate, a payslip). Money that is owed but not yet paid, such as invoices, has no place at all. Chat is used for sending only, not for asking or correcting. These are the gaps the next design closes.
