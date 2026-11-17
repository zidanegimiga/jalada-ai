import "server-only";

import { cache } from "react";

import { apiGet } from "@/shared/api/server-api";

import type { Category, ReviewItem } from "../types";

/** What waits on To check. Asked once per page, however many parts of the page need it. */
export const getReviewQueue = cache(async (): Promise<ReviewItem[]> => {
  return (await apiGet<{ items: ReviewItem[] }>("/v1/review"))?.items ?? [];
});

export async function getCategories(): Promise<Category[]> {
  return (await apiGet<Category[]>("/v1/categories")) ?? [];
}
