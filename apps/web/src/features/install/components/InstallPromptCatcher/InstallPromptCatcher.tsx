"use client";

import { useEffect } from "react";

import { catchInstallPrompt } from "../../install-prompt";

/** Catches the browser's install offer as soon as any page loads, for the Account page. */
export function InstallPromptCatcher() {
  useEffect(catchInstallPrompt, []);
  return null;
}
