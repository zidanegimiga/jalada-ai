import "server-only";

import { apiGet } from "@/lib/server-api";

import type { Category, ReviewItem } from "../types";

export async function getReviewQueue(): Promise<ReviewItem[]> {
  return (await apiGet<{ items: ReviewItem[] }>("/v1/review"))?.items ?? [];
}

export async function getCategories(): Promise<Category[]> {
  return (await apiGet<Category[]>("/v1/categories")) ?? [];
}
