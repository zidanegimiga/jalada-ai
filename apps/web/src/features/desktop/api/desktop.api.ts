/** Asks the API for a one-time code for the desktop app, as the signed-in person. */
export async function requestDesktopCode(challenge: string): Promise<string> {
  const response = await fetch("/v1/auth/device/codes", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ challenge }),
  });
  if (!response.ok) throw new Error("The code could not be made.");
  const body = (await response.json()) as { code: string };
  return body.code;
}
