import type { Certificate } from "./types";

async function send(path: string, method: string, body?: unknown) {
  const response = await fetch(path, {
    method,
    headers: body ? { "Content-Type": "application/json" } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok)
    throw new Error(data.error?.message ?? "That did not save. Try again.");
  return data as Certificate;
}

export function linkPayment(certificateId: string, paymentId: string) {
  return send(`/v1/certificates/${certificateId}/payments`, "POST", {
    payment_id: paymentId,
  });
}

export function unlinkPayment(certificateId: string, paymentId: string) {
  return send(
    `/v1/certificates/${certificateId}/payments/${paymentId}`,
    "DELETE",
  );
}
