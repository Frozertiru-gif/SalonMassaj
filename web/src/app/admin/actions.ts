"use server";

import { cookies } from "next/headers";
import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";
import { adminFetchResponse } from "@/lib/api";
import { ADMIN_TOKEN_COOKIE, buildAdminLoginUrl, normalizeAdminNextPath } from "@/lib/auth";
import { API_BASE_URL } from "./adminApi";
import type { AdminFormState, LoginAdminState } from "./types";

const SESSION_EXPIRED_MESSAGE = "Сессия истекла. Войдите снова.";

async function adminActionFetch(path: string, init?: RequestInit) {
  return adminFetchResponse(path, { ...init, currentPath: "/admin" });
}
function mapAdminErrorDetail(detail?: unknown) {
  if (!detail) {
    return undefined;
  }

  if (Array.isArray(detail)) {
    const messages = detail
      .map((item) => (typeof item === "object" && item !== null && "msg" in item
        ? String((item as { msg?: unknown }).msg ?? "")
        : ""))
      .filter(Boolean);
    if (messages.length > 0) {
      return messages.join("; ");
    }
  }

  const message = typeof detail === "string"
    ? detail
    : typeof detail === "object" && detail !== null && "message" in detail
      ? String((detail as { message?: unknown }).message ?? "")
      : undefined;
  if (!message) {
    return undefined;
  }
  if (message === "Invalid token" || message === "Inactive admin") {
    return SESSION_EXPIRED_MESSAGE;
  }
  return message;
}

function truncateErrorText(value: string, maxLength = 1000): string {
  const text = value.trim();
  if (text.length <= maxLength) {
    return text;
  }

  return `${text.slice(0, maxLength)}…`;
}

async function parseResponseError(response: Response): Promise<{ detail?: unknown; text?: string }> {
  const rawText = await response.text().catch(() => "");
  const normalizedText = rawText.trim();

  if (!normalizedText) {
    return {};
  }

  try {
    const parsed = JSON.parse(normalizedText) as { detail?: unknown };
    return { detail: parsed?.detail };
  } catch {
    return { text: truncateErrorText(normalizedText) };
  }
}

export async function loginAdmin(_: LoginAdminState, formData: FormData): Promise<LoginAdminState> {
  const email = formData.get("email");
  const password = formData.get("password");
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}/admin/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password })
    });
  } catch {
    return { error: "Не удалось связаться с API. Попробуйте позже." };
  }
  if (!response.ok) {
    let message = "Invalid credentials";
    try {
      const data = (await response.json()) as { detail?: string };
      if (data?.detail) {
        message = data.detail;
      }
    } catch {
      message = "Unable to login. Please try again.";
    }
    return { error: message };
  }
  const data = (await response.json()) as { access_token: string };
  cookies().set(ADMIN_TOKEN_COOKIE, data.access_token, {
    httpOnly: true,
    sameSite: "lax",
    path: "/"
  });
  const nextPath = normalizeAdminNextPath(formData.get("next")?.toString());
  redirect(nextPath);
}

export async function logoutAdmin() {
  await fetch("/api/admin/logout", { method: "POST", cache: "no-store" }).catch(() => undefined);
  redirect(buildAdminLoginUrl());
}

export async function updateSetting(key: string, value_jsonb: object) {
    const response = await adminActionFetch(`/admin/settings/${key}`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
      
    },
    body: JSON.stringify({ value_jsonb })
  });
  if (!response.ok) {
    throw new Error("Failed to update setting");
  }
  revalidatePath("/admin/settings");
}

export async function saveTelegramNotifications(_prevState: AdminFormState, formData: FormData): Promise<AdminFormState> {
  const payload = {
    enabled: formData.get("enabled") === "on",
    admin_chat_id: (formData.get("admin_chat_id") as string | null) || null,
    thread_id: formData.get("thread_id") ? Number(formData.get("thread_id")) : null,
    template_booking_created: (formData.get("template_booking_created") as string | null) || null,
    template_booking_confirmed_admin: (formData.get("template_booking_confirmed_admin") as string | null) || null,
    template_booking_assigned_master: (formData.get("template_booking_assigned_master") as string | null) || null,
    send_inline_actions: formData.get("send_inline_actions") === "on",
    public_webhook_base_url: (formData.get("public_webhook_base_url") as string | null) || null,
    webhook_secret: (formData.get("webhook_secret") as string | null) || null
  };

  const response = await adminActionFetch(`/admin/settings/tg_notifications`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
      
    },
    body: JSON.stringify({ value_jsonb: payload })
  });
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    return { error: mapAdminErrorDetail(data?.detail) || "Не удалось сохранить Telegram-настройки" };
  }
  revalidatePath("/admin/settings");
  return { success: "Telegram-настройки сохранены" };
}

export async function sendTelegramTestMessage(_prevState: AdminFormState, formData: FormData): Promise<AdminFormState> {
    const text = (formData.get("test_text") as string | null) || "Тестовое сообщение из админ-панели SalonMassaj";
  const response = await adminActionFetch(`/admin/telegram/test-message`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      
    },
    body: JSON.stringify({ text })
  });
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    return { error: mapAdminErrorDetail(data?.detail) || "Не удалось отправить тест" };
  }
  return { success: "Тестовое сообщение отправлено" };
}

export async function generateMasterTelegramLink(masterId: number): Promise<{ code: string; bot_start_link?: string | null }> {
    const response = await adminActionFetch(`/admin/masters/${masterId}/telegram-link`, {
    method: "POST",
    headers: {
      
    }
  });
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    throw new Error(mapAdminErrorDetail(data?.detail) || "Не удалось сгенерировать ссылку");
  }
  revalidatePath("/admin/masters");
  return data as { code: string; bot_start_link?: string | null };
}

export async function unlinkMasterTelegram(masterId: number) {
    const response = await adminActionFetch(`/admin/masters/${masterId}/telegram-unlink`, {
    method: "POST",
    headers: {
      
    }
  });
  if (!response.ok) {
    const data = await response.json().catch(() => null);
    throw new Error(mapAdminErrorDetail(data?.detail) || "Не удалось отвязать Telegram");
  }
  revalidatePath("/admin/masters");
}

export async function updateBookingStatus(id: number, status: string, is_read: boolean) {
    const response = await adminActionFetch(`/admin/bookings/${id}`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
      
    },
    body: JSON.stringify({ status, is_read })
  });
  if (!response.ok) {
    const data = await response.json().catch(() => null);
    throw new Error(mapAdminErrorDetail(data?.detail) || "Failed to update booking");
  }
  revalidatePath("/admin/bookings");
  revalidatePath("/admin");
}

export async function createCategory(
  _prevState: AdminFormState,
  formData: FormData
): Promise<AdminFormState> {
    const payload = {
    title: formData.get("title"),
    sort_order: Number(formData.get("sort_order") || 0),
    is_active: formData.get("is_active") === "on"
  };
  const response = await adminActionFetch(`/admin/categories`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      
    },
    body: JSON.stringify(payload)
  });
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    return { error: mapAdminErrorDetail(data?.detail) || "Не удалось создать категорию" };
  }
  revalidatePath("/admin/categories");
  return { success: "Категория создана" };
}

export async function createService(
  _prevState: AdminFormState,
  formData: FormData
): Promise<AdminFormState> {
    const payload = {
    category_id: Number(formData.get("category_id")),
    title: formData.get("title"),
    short_description: formData.get("short_description"),
    description: formData.get("description"),
    duration_min: Number(formData.get("duration_min")),
    price_from: Number(formData.get("price_from")),
    price_to: formData.get("price_to") ? Number(formData.get("price_to")) : null,
    discount_percent: formData.get("discount_percent") ? Number(formData.get("discount_percent")) : null,
    image_url: formData.get("image_url") || null,
    tags: (formData.get("tags") as string | null)?.split(",").map((tag) => tag.trim()).filter(Boolean) ?? [],
    is_active: formData.get("is_active") === "on",
    sort_order: Number(formData.get("sort_order") || 0),
    seo_title: formData.get("seo_title") || null,
    seo_description: formData.get("seo_description") || null
  };
  const response = await adminActionFetch(`/admin/services`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      
    },
    body: JSON.stringify(payload)
  });
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    return { error: mapAdminErrorDetail(data?.detail) || "Не удалось создать услугу" };
  }
  revalidatePath("/admin/services");
  return { success: "Услуга создана" };
}

export async function updateCategory(
  _prevState: AdminFormState,
  formData: FormData
): Promise<AdminFormState> {
    const id = Number(formData.get("id"));
  const payload = {
    title: formData.get("title"),
    sort_order: Number(formData.get("sort_order") || 0),
    is_active: formData.get("is_active") === "on"
  };
  const response = await adminActionFetch(`/admin/categories/${id}`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
      
    },
    body: JSON.stringify(payload)
  });
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    return { error: mapAdminErrorDetail(data?.detail) || "Не удалось обновить категорию" };
  }
  revalidatePath("/admin/categories");
  return { success: "Категория обновлена" };
}

export async function deleteCategory(
  _prevState: AdminFormState,
  formData: FormData
): Promise<AdminFormState> {
    const id = Number(formData.get("id"));
  const response = await adminActionFetch(`/admin/categories/${id}`, {
    method: "DELETE",
    headers: {
      
    }
  });
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    return { error: mapAdminErrorDetail(data?.detail) || "Не удалось удалить категорию" };
  }
  revalidatePath("/admin/categories");
  return { success: "Категория удалена" };
}

export async function updateService(
  _prevState: AdminFormState,
  formData: FormData
): Promise<AdminFormState> {
    const id = Number(formData.get("id"));
  const payload = {
    category_id: Number(formData.get("category_id")),
    title: formData.get("title"),
    short_description: formData.get("short_description"),
    description: formData.get("description"),
    duration_min: Number(formData.get("duration_min")),
    price_from: Number(formData.get("price_from")),
    price_to: formData.get("price_to") ? Number(formData.get("price_to")) : null,
    discount_percent: formData.get("discount_percent") ? Number(formData.get("discount_percent")) : null,
    image_url: formData.get("image_url") || null,
    tags: (formData.get("tags") as string | null)?.split(",").map((tag) => tag.trim()).filter(Boolean) ?? [],
    is_active: formData.get("is_active") === "on",
    sort_order: Number(formData.get("sort_order") || 0),
    seo_title: formData.get("seo_title") || null,
    seo_description: formData.get("seo_description") || null
  };
  const response = await adminActionFetch(`/admin/services/${id}`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
      
    },
    body: JSON.stringify(payload)
  });
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    return { error: mapAdminErrorDetail(data?.detail) || "Не удалось обновить услугу" };
  }
  revalidatePath("/admin/services");
  revalidatePath(`/admin/services/${id}`);
  return { success: "Услуга обновлена" };
}

export async function deleteService(
  _prevState: AdminFormState,
  formData: FormData
): Promise<AdminFormState> {
    const id = Number(formData.get("id"));
  const response = await adminActionFetch(`/admin/services/${id}`, {
    method: "DELETE",
    headers: {
      
    }
  });
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    return { error: mapAdminErrorDetail(data?.detail) || "Не удалось удалить услугу" };
  }
  revalidatePath("/admin/services");
  return { success: "Услуга удалена" };
}

export async function createWeeklyRitual(
  _prevState: AdminFormState,
  formData: FormData
): Promise<AdminFormState> {
    const payload = {
    title: formData.get("title"),
    short_description: formData.get("short_description") || null,
    description: formData.get("description"),
    image_url: formData.get("image_url") || null,
    cta_text: formData.get("cta_text") || null,
    cta_url: formData.get("cta_url") || null,
    start_date: formData.get("start_date") || null,
    end_date: formData.get("end_date") || null,
    is_active: formData.get("is_active") === "on",
    sort_order: Number(formData.get("sort_order") || 0)
  };
  const response = await adminActionFetch(`/admin/weekly-rituals`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      
    },
    body: JSON.stringify(payload)
  });
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    return { error: mapAdminErrorDetail(data?.detail) || "Не удалось создать ритуал" };
  }
  revalidatePath("/admin/weekly-rituals");
  return { success: "Ритуал создан" };
}

export async function updateWeeklyRitual(
  _prevState: AdminFormState,
  formData: FormData
): Promise<AdminFormState> {
    const id = Number(formData.get("id"));
  const payload = {
    title: formData.get("title"),
    short_description: formData.get("short_description") || null,
    description: formData.get("description"),
    image_url: formData.get("image_url") || null,
    cta_text: formData.get("cta_text") || null,
    cta_url: formData.get("cta_url") || null,
    start_date: formData.get("start_date") || null,
    end_date: formData.get("end_date") || null,
    is_active: formData.get("is_active") === "on",
    sort_order: Number(formData.get("sort_order") || 0)
  };
  const response = await adminActionFetch(`/admin/weekly-rituals/${id}`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
      
    },
    body: JSON.stringify(payload)
  });
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    return { error: mapAdminErrorDetail(data?.detail) || "Не удалось обновить ритуал" };
  }
  revalidatePath("/admin/weekly-rituals");
  revalidatePath(`/admin/weekly-rituals/${id}`);
  return { success: "Ритуал обновлён" };
}

export async function deleteWeeklyRitual(
  _prevState: AdminFormState,
  formData: FormData
): Promise<AdminFormState> {
    const id = Number(formData.get("id"));
  const response = await adminActionFetch(`/admin/weekly-rituals/${id}`, {
    method: "DELETE",
    headers: {
      
    }
  });
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    return { error: mapAdminErrorDetail(data?.detail) || "Не удалось удалить ритуал" };
  }
  revalidatePath("/admin/weekly-rituals");
  return { success: "Ритуал удалён" };
}

export async function createReview(
  _prevState: AdminFormState,
  formData: FormData
): Promise<AdminFormState> {
    const payload = {
    author_name: formData.get("author_name"),
    rating: formData.get("rating") ? Number(formData.get("rating")) : null,
    text: formData.get("text"),
    source: formData.get("source") || null,
    source_url: formData.get("source_url") || null,
    review_date: formData.get("review_date") || null,
    is_published: formData.get("is_published") === "on",
    sort_order: Number(formData.get("sort_order") || 0)
  };
  const response = await adminActionFetch(`/admin/reviews`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      
    },
    body: JSON.stringify(payload)
  });
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    return { error: mapAdminErrorDetail(data?.detail) || "Не удалось создать отзыв" };
  }
  revalidatePath("/admin/reviews");
  return { success: "Отзыв создан" };
}

export async function updateReview(
  _prevState: AdminFormState,
  formData: FormData
): Promise<AdminFormState> {
    const id = Number(formData.get("id"));
  const payload = {
    author_name: formData.get("author_name"),
    rating: formData.get("rating") ? Number(formData.get("rating")) : null,
    text: formData.get("text"),
    source: formData.get("source") || null,
    source_url: formData.get("source_url") || null,
    review_date: formData.get("review_date") || null,
    is_published: formData.get("is_published") === "on",
    sort_order: Number(formData.get("sort_order") || 0)
  };
  const response = await adminActionFetch(`/admin/reviews/${id}`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
      
    },
    body: JSON.stringify(payload)
  });
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    return { error: mapAdminErrorDetail(data?.detail) || "Не удалось обновить отзыв" };
  }
  revalidatePath("/admin/reviews");
  revalidatePath(`/admin/reviews/${id}`);
  return { success: "Отзыв обновлён" };
}

export async function deleteReview(
  _prevState: AdminFormState,
  formData: FormData
): Promise<AdminFormState> {
    const id = Number(formData.get("id"));
  const response = await adminActionFetch(`/admin/reviews/${id}`, {
    method: "DELETE",
    headers: {
      
    }
  });
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    return { error: mapAdminErrorDetail(data?.detail) || "Не удалось удалить отзыв" };
  }
  revalidatePath("/admin/reviews");
  return { success: "Отзыв удалён" };
}


export type UpdateBookingPayload = {
  id: number;
  status?: string;
  is_read?: boolean;
  master_id?: number | null;
  starts_at?: string;
  ends_at?: string;
  duration_min?: number;
  admin_comment?: string | null;
  final_price_cents?: number | null;
};

export async function updateBookingAdmin(payload: UpdateBookingPayload) {
  const { id, ...patch } = payload;
  const response = await adminActionFetch(`/admin/bookings/${id}`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
      
    },
    body: JSON.stringify(patch)
  });
  if (!response.ok) {
    const errorPayload = await parseResponseError(response);
    const message = mapAdminErrorDetail(errorPayload.detail)
      || errorPayload.text
      || (response.status >= 500 ? "Сервис временно недоступен" : "Не удалось обновить заявку");
    throw new Error(message);
  }
  revalidatePath("/admin/bookings");
  revalidatePath("/admin");
}

export type UpdateBookingActionState = { ok: boolean; error?: string };

export async function updateBookingAdminFormAction(
  _prevState: UpdateBookingActionState,
  formData: FormData
): Promise<UpdateBookingActionState> {
  const status = String(formData.get("status") ?? "");
  const originalStatus = String(formData.get("original_status") ?? "");
  const isRead = formData.get("is_read") === "on";
  const originalIsRead = String(formData.get("original_is_read") ?? "") === "true";
  const masterId = formData.get("master_id") ? Number(formData.get("master_id")) : null;
  const originalMasterId = formData.get("original_master_id") ? Number(formData.get("original_master_id")) : null;
  const startsAt = (formData.get("starts_at") as string | null)?.trim() ?? "";
  const originalStartsAt = (formData.get("original_starts_at") as string | null)?.trim() ?? "";
  const adminComment = ((formData.get("admin_comment") as string | null) || "").trim() || null;
  const originalAdminComment = ((formData.get("original_admin_comment") as string | null) || "").trim() || null;
  const finalPriceRub = (formData.get("final_price_rub") as string | null)?.trim() ?? "";

  if (status === "DONE") {
    const finalPriceNumber = Number(finalPriceRub);
    if (!finalPriceRub || Number.isNaN(finalPriceNumber) || finalPriceNumber <= 0) {
      return { ok: false, error: "Укажите финальную цену" };
    }
  }

  let finalPriceCents: number | null;
  if (status === "DONE") {
    finalPriceCents = Math.round(Number(finalPriceRub) * 100);
  } else if (finalPriceRub === "") {
    finalPriceCents = null;
  } else {
    const parsedPrice = Number(finalPriceRub);
    if (Number.isNaN(parsedPrice)) {
      return { ok: false, error: "Укажите корректную финальную цену" };
    }
    finalPriceCents = Math.round(parsedPrice * 100);
  }

  const originalFinalPriceRaw = (formData.get("original_final_price_cents") as string | null)?.trim() ?? "";
  const originalFinalPriceCents = originalFinalPriceRaw === "" ? null : Number(originalFinalPriceRaw);

  const payload: UpdateBookingPayload = {
    id: Number(formData.get("id"))
  };

  if (status !== originalStatus) {
    payload.status = status;
  }
  if (isRead !== originalIsRead) {
    payload.is_read = isRead;
  }
  if (masterId !== originalMasterId) {
    payload.master_id = masterId;
  }
  if (startsAt && startsAt !== originalStartsAt) {
    payload.starts_at = startsAt;
  }
  if (adminComment !== originalAdminComment) {
    payload.admin_comment = adminComment;
  }
  if (finalPriceCents !== originalFinalPriceCents) {
    payload.final_price_cents = finalPriceCents;
  }

  try {
    await updateBookingAdmin(payload);
    return { ok: true };
  } catch (error) {
    const message = error instanceof Error && error.message
      ? error.message
      : "Сервис временно недоступен";
    return { ok: false, error: message };
  }
}
