import "server-only";

import { cache } from "react";

import type { Schema } from "@/shared/api/api-schema";
import { apiGet } from "@/shared/api/server-api";

export type ModelConsent = Schema<"ConsentResponse">;

/** Whether a model may read this person's records. One request per page. */
export const getModelConsent = cache(async (): Promise<ModelConsent> => {
  return (
    (await apiGet<ModelConsent>("/v1/account/model-consent")) ?? {
      required: false,
      given: false,
      notice: "",
    }
  );
});
