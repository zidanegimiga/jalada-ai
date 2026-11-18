# Transfers of personal data out of Kenya

A record of every service outside Kenya that receives people's data, why, on what basis and with what safeguards, kept to show the Data Protection Commissioner on request (Data Protection Act, 2019, Part VI; General Regulations, 2021). It is a working record, to be reviewed by a Kenyan data protection practitioner before launch and kept up to date with the privacy notice at `/privacy` (`apps/web/src/app/(auth)/privacy/page.tsx`).

Last reviewed: 18 November 2026. Review again when a service is added or changed, and at least once a year.

## Data Jalada AI handles
- **Account:** name, email, a password hash or a Google account id, sessions.
- **Evidence:** receipts, PDFs and M-Pesa messages people send. M-Pesa records and receipts may count as "property details", which section 2 lists as sensitive personal data.
- **Records:** what is read from evidence, and each change the person makes.
- **Optional:** a Telegram chat link; questions to the assistant and its answers.
- **Operations:** logs, traces and error reports, which never hold evidence, records, messages or questions.

## Services and transfers

| Service | Purpose | Location | Data received | Basis (s.48) | Safeguards |
|---|---|---|---|---|---|
| Render | Runs the API and the job loop | Frankfurt, Germany | Everything the app handles, while handling it | Performing the service the person signed up for | Provider's data processing terms; TLS in transit |
| Neon | Postgres database | AWS Frankfurt, Germany | Accounts and records | Performing the service | Provider's data processing terms; TLS; encryption at rest by the provider |
| Cloudflare R2 | Evidence files | Outside Kenya | Evidence files, encrypted by the app with AES-256-GCM before upload (decision 0011) | Performing the service | The provider holds only ciphertext; the keys stay in the app's settings |
| Netlify | Serves the web app | Outside Kenya | Page requests | Performing the service | Provider's data processing terms; pages are served without records |
| Sentry | Error reports | Outside Kenya | Code errors, with request bodies, local variables, user details and messages removed (decision 0017) | Legitimate interest in a working service | Data minimised before sending |
| Google | Sign-in, if chosen | Outside Kenya | That the person signs in to Jalada AI | The person's choice to sign in with Google | Standard OpenID Connect; no records sent |
| Telegram | Bot, if linked | Outside Kenya | What the person sends the bot, and the replies | The person's choice to use Telegram | Only after the person links their chat |
| Language model provider | Reads photos; answers questions | Outside Kenya | Evidence, records and questions, for people who agreed | Consent (s.49), recorded per person with the exact notice agreed to | Asked before any record is sent; withdrawable on the Account page; provider's terms exclude training on the data (decision 0026); the app refuses to start in production without a named provider |
| Traces endpoint, if set | Assistant performance | Set in `JALADA_AGENT_TRACES_URL` | Names, outcomes, token counts and times; no content (decision 0025) | Legitimate interest | No personal data beyond ids |

## How consent for the model provider is kept
- The question names the provider, says it is outside Kenya and says what happens without it (`apps/web/src/features/consent`).
- Each agreement is stored with the notice agreed to and the time (`model_consents` table). A new provider notice asks everyone again.
- The pipeline and the assistant check it before every use (`ConsentToModels.allows`); withdrawing stops future use at once. Data already sent stays under the provider's own retention (Google: up to 55 days of logs if logging is on, which it should not be; see decision 0026).

## Still to do before launch
- A practitioner's review of this record, the privacy notice and the consent wording.
- Each provider's data processing terms accepted for the production accounts, with copies or links kept here.
- Registration with the Office of the Data Protection Commissioner, if the app's size or purpose requires it under the Registration Regulations, 2021.
- A contact address for data requests, set in `PRIVACY_CONTACT` so the privacy notice shows it.
