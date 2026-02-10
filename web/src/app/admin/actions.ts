"use server";

import { cookies } from "next/headers";
import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";
import { API_BASE_URL } from "./adminApi";
import type { AdminFormState, LoginAdminState } from "./types";
const UNAUTHORIZED_STATUSES = new Set([401, 403]);
const SESSION_EXPIRED_MESSAGE = "Сессия истекла. Войдите снова.";

function redirectToAdminLogin() {
  cookies().delete("admin_token");
  redirect("/admin/login");
}

function getAdminTokenOrRedirect() {
  const token = cookies().get("admin_token")?.value;
  if (!token) {
    redirect("/admin/login");
  }
  return token;
}

function handleUnauthorizedResponse(response: Response) {
  if (UNAUTHORIZED_STATUSES.has(response.status)) {
    redirectToAdminLogin();
  }
}

function mapAdminErrorDetail(detail?: string) {
  if (!detail) {
    return detail;
  }
  if (detail === "Invalid token" || detail === "Inactive admin") {
    return SESSION_EXPIRED_MESSAGE;
  }
  return detail;
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
  cookies().set("admin_token", data.access_token, {
    httpOnly: true,
    sameSite: "lax",
    path: "/"
  });
  redirect("/admin");
}

export async function logoutAdmin() {
  cookies().delete("admin_token");
  redirect("/admin/login");
}

export async function updateSetting(key: string, value_jsonb: object) {
  const token = getAdminTokenOrRedirect();
  const response = await fetch(`${API_BASE_URL}/admin/settings/${key}`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`
    },
    body: JSON.stringify({ value_jsonb })
  });
  handleUnauthorizedResponse(response);
  if (!response.ok) {
    throw new Error("Failed to update setting");
  }
  revalidatePath("/admin/settings");
}

export async function saveTelegramNotifications(_prevState: AdminFormState, formData: FormData): Promise<AdminFormState> {
  const token = getAdminTokenOrRedirect();
  const payload = {
    enabled: formData.get("enabled") === "on",
    admin_chat_id: (formData.get("admin_chat_id") as string | null) || null,
    admin_thread_id: formData.get("admin_thread_id") ? Number(formData.get("admin_thread_id")) : null,
    template_admin: (formData.get("template_admin") as string | null) || "",
    send_inline_actions: formData.get("send_inline_actions") === "on",
    public_webhook_base_url: (formData.get("public_webhook_base_url") as string | null) || null,
    webhook_secret: (formData.get("webhook_secret") as string | null) || null
  };

  const response = await fetch(`${API_BASE_URL}/admin/settings/tg_notifications`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`
    },
    body: JSON.stringify({ value_jsonb: payload })
  });
  handleUnauthorizedResponse(response);
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    return { error: mapAdminErrorDetail(data?.detail) || "Не удалось сохранить Telegram-настройки" };
  }
  revalidatePath("/admin/settings");
  return { success: "Telegram-настройки сохранены" };
}

export async function sendTelegramTestMessage(_prevState: AdminFormState, formData: FormData): Promise<AdminFormState> {
  const token = getAdminTokenOrRedirect();
  const text = (formData.get("test_text") as string | null) || "Тестовое сообщение из админ-панели SalonMassaj";
  const response = await fetch(`${API_BASE_URL}/admin/telegram/test-message`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`
    },
    body: JSON.stringify({ text })
  });
  handleUnauthorizedResponse(response);
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    return { error: mapAdminErrorDetail(data?.detail) || "Не удалось отправить тест" };
  }
  return { success: "Тестовое сообщение отправлено" };
}

export async function generateMasterTelegramLink(masterId: number): Promise<{ code: string; bot_start_link?: string | null }> {
  const token = getAdminTokenOrRedirect();
  const response = await fetch(`${API_BASE_URL}/admin/masters/${masterId}/telegram-link`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`
    }
  });
  handleUnauthorizedResponse(response);
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    throw new Error(mapAdminErrorDetail(data?.detail) || "Не удалось сгенерировать ссылку");
  }
  revalidatePath("/admin/masters");
  return data as { code: string; bot_start_link?: string | null };
}

export async function unlinkMasterTelegram(masterId: number) {
  const token = getAdminTokenOrRedirect();
  const response = await fetch(`${API_BASE_URL}/admin/masters/${masterId}/telegram-unlink`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`
    }
  });
  handleUnauthorizedResponse(response);
  if (!response.ok) {
    const data = await response.json().catch(() => null);
    throw new Error(mapAdminErrorDetail(data?.detail) || "Не удалось отвязать Telegram");
  }
  revalidatePath("/admin/masters");
}

export async function updateBookingStatus(id: number, status: string, is_read: boolean) {
  const token = getAdminTokenOrRedirect();
  const response = await fetch(`${API_BASE_URL}/admin/bookings/${id}`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`
    },
    body: JSON.stringify({ status, is_read })
  });
  handleUnauthorizedResponse(response);
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
  const token = getAdminTokenOrRedirect();
  const payload = {
    title: formData.get("title"),
    slug: formData.get("slug"),
    sort_order: Number(formData.get("sort_order") || 0),
    is_active: formData.get("is_active") === "on"
  };
  const response = await fetch(`${API_BASE_URL}/admin/categories`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`
    },
    body: JSON.stringify(payload)
  });
  handleUnauthorizedResponse(response);
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
  const token = getAdminTokenOrRedirect();
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
  const response = await fetch(`${API_BASE_URL}/admin/services`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`
    },
    body: JSON.stringify(payload)
  });
  handleUnauthorizedResponse(response);
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
  const token = getAdminTokenOrRedirect();
  const id = Number(formData.get("id"));
  const payload = {
    title: formData.get("title"),
    slug: formData.get("slug"),
    sort_order: Number(formData.get("sort_order") || 0),
    is_active: formData.get("is_active") === "on"
  };
  const response = await fetch(`${API_BASE_URL}/admin/categories/${id}`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`
    },
    body: JSON.stringify(payload)
  });
  handleUnauthorizedResponse(response);
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
  const token = getAdminTokenOrRedirect();
  const id = Number(formData.get("id"));
  const response = await fetch(`${API_BASE_URL}/admin/categories/${id}`, {
    method: "DELETE",
    headers: {
      Authorization: `Bearer ${token}`
    }
  });
  handleUnauthorizedResponse(response);
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
  const token = getAdminTokenOrRedirect();
  const id = Number(formData.get("id"));
  const slugValue = formData.get("slug");
  const payload = {
    category_id: Number(formData.get("category_id")),
    title: formData.get("title"),
    slug: slugValue ? String(slugValue) : undefined,
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
  const response = await fetch(`${API_BASE_URL}/admin/services/${id}`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`
    },
    body: JSON.stringify(payload)
  });
  handleUnauthorizedResponse(response);
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
  const token = getAdminTokenOrRedirect();
  const id = Number(formData.get("id"));
  const response = await fetch(`${API_BASE_URL}/admin/services/${id}`, {
    method: "DELETE",
    headers: {
      Authorization: `Bearer ${token}`
    }
  });
  handleUnauthorizedResponse(response);
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
  const token = getAdminTokenOrRedirect();
  const payload = {
    title: formData.get("title"),
    slug: formData.get("slug") || null,
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
  const response = await fetch(`${API_BASE_URL}/admin/weekly-rituals`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`
    },
    body: JSON.stringify(payload)
  });
  handleUnauthorizedResponse(response);
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
  const token = getAdminTokenOrRedirect();
  const id = Number(formData.get("id"));
  const slugValue = formData.get("slug");
  const payload = {
    title: formData.get("title"),
    slug: slugValue ? String(slugValue) : undefined,
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
  const response = await fetch(`${API_BASE_URL}/admin/weekly-rituals/${id}`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`
    },
    body: JSON.stringify(payload)
  });
  handleUnauthorizedResponse(response);
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
  const token = getAdminTokenOrRedirect();
  const id = Number(formData.get("id"));
  const response = await fetch(`${API_BASE_URL}/admin/weekly-rituals/${id}`, {
    method: "DELETE",
    headers: {
      Authorization: `Bearer ${token}`
    }
  });
  handleUnauthorizedResponse(response);
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
  const token = getAdminTokenOrRedirect();
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
  const response = await fetch(`${API_BASE_URL}/admin/reviews`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`
    },
    body: JSON.stringify(payload)
  });
  handleUnauthorizedResponse(response);
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
  const token = getAdminTokenOrRedirect();
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
  const response = await fetch(`${API_BASE_URL}/admin/reviews/${id}`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`
    },
    body: JSON.stringify(payload)
  });
  handleUnauthorizedResponse(response);
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
  const token = getAdminTokenOrRedirect();
  const id = Number(formData.get("id"));
  const response = await fetch(`${API_BASE_URL}/admin/reviews/${id}`, {
    method: "DELETE",
    headers: {
      Authorization: `Bearer ${token}`
    }
  });
  handleUnauthorizedResponse(response);
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    return { error: mapAdminErrorDetail(data?.detail) || "Не удалось удалить отзыв" };
  }
  revalidatePath("/admin/reviews");
  return { success: "Отзыв удалён" };
}


export async function updateBookingAdmin(payload: { id: number; status?: string; is_read?: boolean; master_id?: number | null; admin_comment?: string | null; final_price_cents?: number | null }) {
  const token = getAdminTokenOrRedirect();
  const response = await fetch(`${API_BASE_URL}/admin/bookings/${payload.id}`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`
    },
    body: JSON.stringify(payload)
  });
  handleUnauthorizedResponse(response);
  if (!response.ok) {
    const data = await response.json().catch(() => null);
    throw new Error(mapAdminErrorDetail(data?.detail) || "Failed to update booking");
  }
  revalidatePath("/admin/bookings");
  revalidatePath("/admin");
}
