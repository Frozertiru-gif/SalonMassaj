"use server";

import { cookies } from "next/headers";
import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";

const API_BASE_URL = process.env.API_URL ?? process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function loginAdmin(formData: FormData) {
  const email = formData.get("email");
  const password = formData.get("password");
  const response = await fetch(`${API_BASE_URL}/admin/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password })
  });
  if (!response.ok) {
    throw new Error("Invalid credentials");
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
  const token = cookies().get("admin_token")?.value;
  const response = await fetch(`${API_BASE_URL}/admin/settings/${key}`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`
    },
    body: JSON.stringify({ value_jsonb })
  });
  if (!response.ok) {
    throw new Error("Failed to update setting");
  }
  revalidatePath("/admin/settings");
}

export async function updateBookingStatus(id: number, status: string, is_read: boolean) {
  const token = cookies().get("admin_token")?.value;
  const response = await fetch(`${API_BASE_URL}/admin/bookings/${id}`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`
    },
    body: JSON.stringify({ status, is_read })
  });
  if (!response.ok) {
    throw new Error("Failed to update booking");
  }
  revalidatePath("/admin/bookings");
  revalidatePath("/admin");
}

export async function createCategory(formData: FormData) {
  const token = cookies().get("admin_token")?.value;
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
  if (!response.ok) {
    throw new Error("Failed to create category");
  }
  revalidatePath("/admin/categories");
}

export async function createService(formData: FormData) {
  const token = cookies().get("admin_token")?.value;
  const payload = {
    category_id: Number(formData.get("category_id")),
    title: formData.get("title"),
    slug: formData.get("slug"),
    short_description: formData.get("short_description"),
    description: formData.get("description"),
    duration_min: Number(formData.get("duration_min")),
    price_from: Number(formData.get("price_from")),
    price_to: formData.get("price_to") ? Number(formData.get("price_to")) : null,
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
  if (!response.ok) {
    throw new Error("Failed to create service");
  }
  revalidatePath("/admin/services");
}
