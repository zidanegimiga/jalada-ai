/** What the app takes in and what it gives back, for the "What it does" section. */

export const SENDS = [
  {
    glyph: "mpesa",
    title: "M-Pesa messages",
    text: "Forward the confirmation text, for money sent, paid or received.",
  },
  {
    glyph: "statement",
    title: "Bank alerts and statements",
    text: "Bank texts, and statements as PDFs, a month at a time.",
  },
  {
    glyph: "receipt",
    title: "Receipt photos",
    text: "A photo from your phone. Too blurred to read? It asks you.",
  },
  {
    glyph: "payslip",
    title: "Payslips",
    text: "Pay, deductions and the tax your employer already took.",
  },
  {
    glyph: "certificate",
    title: "Withholding certificates",
    text: "From clients who deduct tax before they pay you.",
  },
  {
    glyph: "note",
    title: "A plain note",
    text: "Cash with no paper behind it, written in one sentence.",
  },
] as const;

export const GETS = [
  {
    glyph: "ledger",
    title: "One ledger",
    text: "Every payment in and out, each linked to its original.",
  },
  {
    glyph: "month",
    title: "Your month at a glance",
    text: "Money in and out by category, and where it went.",
  },
  {
    glyph: "check",
    title: "To check",
    text: "Anything unsure waits for one tap from you.",
  },
  {
    glyph: "workbook",
    title: "A tax-year workbook",
    text: "Figures grouped the way the KRA iTax return asks for them.",
  },
  {
    glyph: "ask",
    title: "Answers",
    text: "Ask in your own words, on the web or in Telegram.",
  },
] as const;

/** How one invented month of money in splits by what it was for. */
export const SPLIT = [
  { label: "Salary", share: 48, tone: "var(--l-paper)" },
  { label: "Client payments", share: 27, tone: "var(--l-pumpkin)" },
  { label: "Support from family", share: 13, tone: "var(--l-flax)" },
  { label: "Between your own accounts", share: 12, tone: "var(--l-forest)" },
];

export const AUDIENCE = [
  "Freelancers",
  "Salaried, with a side income",
  "Small traders",
  "Anyone whose business and household money share one line",
];
