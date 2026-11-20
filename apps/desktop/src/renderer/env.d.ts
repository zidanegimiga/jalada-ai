import type { JaladaBridge } from "@shared/bridge";

declare global {
  interface Window {
    /** Put there by the preload script; the window's only way to the main process. */
    jalada: JaladaBridge;
  }
}
