import { cache } from "react";
import { adminFetch } from "@/lib/api";
import type { CurrentAdmin } from "@/lib/types";

export const API_BASE_URL =
  process.env.API_INTERNAL_BASE_URL ?? process.env.API_URL ?? "http://localhost:8000";

export const getCurrentAdmin = cache(async (): Promise<CurrentAdmin> => adminFetch<CurrentAdmin>("/admin/me"));
