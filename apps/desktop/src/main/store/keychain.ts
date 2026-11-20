import { safeStorage } from "electron";

import type { KeyProtector } from "./key";

/**
 * The system keychain through Electron's `safeStorage`: the Keychain on macOS, DPAPI on
 * Windows, the Secret Service on Linux. On Linux without a keyring Electron falls back to a
 * fixed password ("basic_text"), which is no protection, so that counts as not secure.
 */
export const keychain: KeyProtector = {
  isSecure: () =>
    safeStorage.isEncryptionAvailable() &&
    !(
      process.platform === "linux" &&
      safeStorage.getSelectedStorageBackend() === "basic_text"
    ),
  seal: (secret) => safeStorage.encryptString(secret),
  open: (sealed) => safeStorage.decryptString(sealed),
};
