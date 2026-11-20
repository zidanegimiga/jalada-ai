/** The event Chrome, Edge and Samsung Internet fire when the app can be installed. */
export type InstallPromptEvent = Event & {
  prompt: () => Promise<void>;
  userChoice: Promise<{ outcome: "accepted" | "dismissed" }>;
};

export type InstallState = "installed" | "ready" | "ios" | "unavailable";

let saved: InstallPromptEvent | null = null;
let installed = false;
const listeners = new Set<() => void>();

function changed() {
  for (const listener of listeners) listener();
}

/**
 * Keeps the browser's install offer for later. The browser makes it once, early, often
 * before the Account page is open, so it is caught as soon as the app loads.
 */
export function catchInstallPrompt(): () => void {
  const keep = (event: Event) => {
    event.preventDefault();
    saved = event as InstallPromptEvent;
    changed();
  };
  const done = () => {
    saved = null;
    installed = true;
    changed();
  };
  window.addEventListener("beforeinstallprompt", keep);
  window.addEventListener("appinstalled", done);
  return () => {
    window.removeEventListener("beforeinstallprompt", keep);
    window.removeEventListener("appinstalled", done);
  };
}

export function subscribe(listener: () => void): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

/** Whether the app is installed, can be, or how. iPhones and iPads have no install offer. */
export function installState(): InstallState {
  const standalone =
    matchMedia("(display-mode: standalone)").matches ||
    (navigator as { standalone?: boolean }).standalone === true;
  if (installed || standalone) return "installed";
  if (saved) return "ready";
  if (/iPhone|iPad|iPod/.test(navigator.userAgent)) return "ios";
  return "unavailable";
}

/** Shows the browser's own install question. True when the person said yes. */
export async function askToInstall(): Promise<boolean> {
  const offer = saved;
  if (!offer) return false;
  await offer.prompt();
  const { outcome } = await offer.userChoice;
  saved = null;
  changed();
  return outcome === "accepted";
}
