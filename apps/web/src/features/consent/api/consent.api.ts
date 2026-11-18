import type { Schema } from "@/shared/api/api-schema";

export type ModelConsent = Schema<"ConsentResponse">;

/** Agree, or take the agreement back. The API answers with the new state. */
export async function setModelConsent(agree: boolean): Promise<ModelConsent> {
  const response = await fetch("/v1/account/model-consent", {
    method: agree ? "POST" : "DELETE",
  });
  if (!response.ok) throw new Error("That did not save. Try again.");
  return (await response.json()) as ModelConsent;
}
