import type { components } from "./api-types";

/**
 * A response or request body as the API declares it. api-types.ts is generated from
 * apps/api/openapi.json by `make web-types`, so these never drift from the API.
 */
export type Schema<Name extends keyof components["schemas"]> =
  components["schemas"][Name];
