/**
 * The landing page's words and examples, in one place. Every person, shop and amount here
 * is made up.
 */

export const NAV = [
  { label: "How it works", href: "#how" },
  { label: "Reading", href: "#reading" },
  { label: "Ask", href: "#ask" },
  { label: "Privacy", href: "#privacy" },
];

/** The scattered evidence in the opening, and the ledger rows each one becomes. */
export const EVIDENCE = [
  {
    kind: "M-Pesa message",
    body: "SKE3H8Q2LM Confirmed. Ksh2,450.00 paid to NAIVAS WESTGATE on 14/11/26 at 6:42 PM.",
    place: "left-[2%] top-[20%] -rotate-6",
    depth: 0.6,
  },
  {
    kind: "Receipt photo",
    body: "Java House, Kimathi St. Total KES 1,180.00",
    place: "right-[3%] top-[16%] rotate-3",
    depth: 1,
  },
  {
    kind: "Withholding certificate",
    body: "PDF, 1 page. Tax withheld KES 9,000.00",
    place: "left-[5%] bottom-[7%] rotate-2",
    depth: 0.8,
  },
  {
    kind: "Bank message",
    body: "Received KES 35,000.00 from WANJIKU DESIGNS LTD.",
    place: "right-[4%] bottom-[10%] -rotate-3",
    depth: 0.5,
  },
  {
    kind: "Payslip",
    body: "October. Net pay KES 84,300.00",
    place: "right-[24%] top-[9%] rotate-6",
    depth: 1.2,
  },
];

export const LEDGER = [
  {
    name: "Naivas Westgate",
    category: "Groceries",
    amount: "-2,450.00",
    state: "Confirmed",
  },
  {
    name: "Java House",
    category: "Client meeting",
    amount: "-1,180.00",
    state: "To check",
  },
  {
    name: "Wanjiku Designs",
    category: "Client payment",
    amount: "+35,000.00",
    state: "Confirmed",
  },
  {
    name: "Withholding tax",
    category: "Tax withheld",
    amount: "9,000.00",
    state: "Confirmed",
  },
  {
    name: "October salary",
    category: "Salary",
    amount: "+84,300.00",
    state: "Confirmed",
  },
];

export const RIBBON = [
  "M-Pesa messages",
  "Receipt photos",
  "Bank statements",
  "Payslips",
  "Withholding certificates",
  "PDFs",
  "Telegram",
];

export const STEPS = [
  {
    number: "01",
    title: "Send",
    text: "Forward an M-Pesa message, take a photo of a receipt or drop in a PDF. On the web, or in a Telegram chat.",
    detail: ["Photo", "PDF", "Message"],
  },
  {
    number: "02",
    title: "Read",
    text: "Fixed formats like M-Pesa messages are read with rules. A language model helps only when rules cannot cope, and only if you agreed to it.",
    detail: ["Date", "Amount", "Paid to", "Code"],
  },
  {
    number: "03",
    title: "Check",
    text: "Anything it is unsure of waits in To check. Confirm it or correct it with one tap. It never decides for you what is taxable.",
    detail: ["Confirm", "Correct"],
  },
  {
    number: "04",
    title: "Keep",
    text: "Every entry links back to the original and to how it was sorted. At filing time, the figures come grouped the way iTax asks for them.",
    detail: ["Ledger", "Evidence", "Workbook"],
  },
];

/** The message in the reading section, cut into the parts the app takes from it. */
export const MESSAGE: ({ text: string } | { text: string; field: string })[] = [
  { text: "SKE3H8Q2LM", field: "code" },
  { text: " Confirmed. " },
  { text: "Ksh2,450.00", field: "amount" },
  { text: " paid to " },
  { text: "NAIVAS WESTGATE", field: "paid-to" },
  { text: " on " },
  { text: "14/11/26", field: "date" },
  {
    text: " at 6:42 PM. New M-PESA balance is Ksh18,210.50. Transaction cost, ",
  },
  { text: "Ksh0.00", field: "fee" },
  { text: "." },
];

export const FIELDS = [
  { id: "amount", label: "Amount", value: "KES 2,450.00 out" },
  { id: "paid-to", label: "Paid to", value: "Naivas Westgate" },
  { id: "date", label: "Date", value: "14 November 2026" },
  { id: "code", label: "M-Pesa code", value: "SKE3H8Q2LM" },
  { id: "fee", label: "Fee", value: "KES 0.00" },
];

export const PROMISES = [
  {
    title: "Yours before anyone else's.",
    text: "Receipts and messages are encrypted with AES-256-GCM before they are stored. The storage provider only ever holds scrambled bytes; the keys stay with the app.",
    tone: "ink",
  },
  {
    title: "Asked before any model reads it.",
    text: "You choose whether a language model may read your records. The question names the provider and where it is, and you can change your answer on the Account page.",
    tone: "pumpkin",
  },
  {
    title: "Nothing changes without your tap.",
    text: "The assistant can suggest a change, but it waits as a card until you confirm it. Confirming runs the app's own code, with no model involved.",
    tone: "paper",
  },
  {
    title: "Leave with everything.",
    text: "Export your records, or delete them. Financial records are personal data under the Data Protection Act, 2019, and they belong to you.",
    tone: "flax",
  },
];

export const FIGURES = [
  {
    value: 6,
    label: "kinds of evidence it reads",
    note: "M-Pesa, statements, receipts, payslips, certificates and plain notes",
  },
  {
    value: 2,
    label: "places to send them",
    note: "The web app, and a Telegram chat",
  },
  {
    value: 256,
    label: "bit encryption on every file",
    note: "AES-GCM, before anything is stored",
  },
  {
    value: 24,
    label: "hours a suggestion waits",
    note: "Then it expires, unconfirmed",
  },
];

export const QUESTIONS = [
  {
    q: "Who is it for?",
    a: "People in Kenya who keep their own money records: freelancers, salaried people with a side income, small traders, and anyone whose business and household money share one M-Pesa line.",
  },
  {
    q: "Does it file my tax return?",
    a: "No. It keeps your records and, at filing time, gives you the figures grouped the way the KRA iTax return asks for them. You, or your accountant, file the return.",
  },
  {
    q: "What if it reads something wrong?",
    a: "Anything it is unsure of goes to To check instead of your ledger, and you confirm or correct it. A photo too blurred to read is sent back to you to enter by hand, never guessed.",
  },
  {
    q: "Can I use it from Telegram?",
    a: "Yes. Link your chat on the Account page, then forward messages and photos to the bot. Ask it a question by ending your message with a question mark.",
  },
  {
    q: "Can I take my records with me?",
    a: "Yes. Export everything as a workbook, or delete your account and everything in it.",
  },
];
