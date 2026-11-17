/** The steps from a message to a tax return, shown beside sign-in and sign-up. */
export const JOURNEY = [
  { name: "Send", detail: "Forward an M-Pesa message or snap a receipt" },
  {
    name: "Read",
    detail: "Jalada AI reads the amount, the date and who it was with",
  },
  { name: "Check", detail: "You confirm anything it was unsure of" },
  {
    name: "Ledger",
    detail: "Every entry keeps the message or receipt it came from",
  },
  { name: "File", detail: "A workbook grouped the way iTax asks for it" },
] as const;
