import { adminFetch } from "@/lib/api";
import type { Master, Service } from "@/lib/types";
import { Card } from "@/components/Card";
import { Container } from "@/components/Container";
import { API_BASE_URL } from "../../adminApi";
import { cookies } from "next/headers";
import { revalidatePath } from "next/cache";

async function createMaster(formData: FormData) {
  "use server";
  const token = cookies().get("admin_token")?.value;
  const serviceIds = formData.getAll("service_ids").map((value) => Number(value));
  await fetch(`${API_BASE_URL}/admin/masters`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    body: JSON.stringify({
      name: formData.get("name"),
      photo_url: formData.get("photo_url") || null,
      short_bio: formData.get("short_bio") || null,
      bio: formData.get("bio") || null,
      is_active: formData.get("is_active") === "on",
      sort_order: Number(formData.get("sort_order") || 0),
      service_ids: serviceIds
    })
  });
  revalidatePath("/admin/masters");
}

async function deactivateMaster(formData: FormData) {
  "use server";
  const token = cookies().get("admin_token")?.value;
  const id = Number(formData.get("id"));
  await fetch(`${API_BASE_URL}/admin/masters/${id}`, { method: "DELETE", headers: { Authorization: `Bearer ${token}` } });
  revalidatePath("/admin/masters");
}

async function generateTelegramLink(formData: FormData) {
  "use server";
  const token = cookies().get("admin_token")?.value;
  const id = Number(formData.get("id"));
  await fetch(`${API_BASE_URL}/admin/masters/${id}/telegram-link`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` }
  });
  revalidatePath("/admin/masters");
}

async function unlinkTelegram(formData: FormData) {
  "use server";
  const token = cookies().get("admin_token")?.value;
  const id = Number(formData.get("id"));
  await fetch(`${API_BASE_URL}/admin/masters/${id}/telegram-unlink`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` }
  });
  revalidatePath("/admin/masters");
}

export default async function AdminMastersPage() {
  const [masters, services] = await Promise.all([adminFetch<Master[]>("/admin/masters"), adminFetch<Service[]>("/admin/services")]);

  return (
    <Container className="space-y-6">
      <div>
        <p className="text-sm uppercase tracking-[0.3em] text-blush-600">Мастера</p>
        <h2 className="mt-2 text-2xl font-semibold text-ink-900">Управление мастерами</h2>
      </div>
      <Card>
        <h3 className="text-lg font-semibold text-ink-900">Добавить мастера</h3>
        <form action={createMaster} className="mt-4 grid gap-3 md:grid-cols-2">
          <input name="name" required placeholder="ФИО / Ник" className="rounded-2xl border border-blush-100 px-3 py-2 text-sm" />
          <input name="photo_url" placeholder="URL фото" className="rounded-2xl border border-blush-100 px-3 py-2 text-sm" />
          <input name="short_bio" placeholder="Краткое описание" className="rounded-2xl border border-blush-100 px-3 py-2 text-sm" />
          <input name="sort_order" type="number" defaultValue={0} className="rounded-2xl border border-blush-100 px-3 py-2 text-sm" />
          <textarea name="bio" placeholder="Подробное описание" className="md:col-span-2 rounded-2xl border border-blush-100 px-3 py-2 text-sm" />
          <div className="md:col-span-2 grid gap-2 md:grid-cols-3">
            {services.map((service) => <label key={service.id} className="text-sm"><input type="checkbox" name="service_ids" value={service.id} className="mr-2" />{service.title}</label>)}
          </div>
          <label className="text-sm"><input type="checkbox" name="is_active" defaultChecked className="mr-2" />Активен</label>
          <button className="rounded-full bg-blush-200 px-4 py-2 text-sm font-medium" type="submit">Создать</button>
        </form>
      </Card>
      <div className="space-y-3">
        {masters.map((master) => (
          <Card key={master.id}>
            <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
              <div>
                <p className="font-medium text-ink-900">{master.name}</p>
                <p className="text-xs text-ink-500">{master.short_bio ?? "—"}</p>
                <p className="mt-1 text-xs text-ink-600">TG: {master.telegram_user_id ? "привязан" : "не привязан"}</p>
                {master.telegram_link_code ? (
                  <p className="text-xs text-ink-600">Код привязки: <span className="font-mono">{master.telegram_link_code}</span></p>
                ) : null}
              </div>
              <div className="flex flex-wrap gap-2">
                <form action={generateTelegramLink}>
                  <input type="hidden" name="id" value={master.id} />
                  <button className="rounded-full border border-blush-200 px-3 py-1 text-xs" type="submit">Сгенерировать ссылку</button>
                </form>
                <form action={unlinkTelegram}>
                  <input type="hidden" name="id" value={master.id} />
                  <button className="rounded-full border border-blush-200 px-3 py-1 text-xs" type="submit">Отвязать TG</button>
                </form>
                <form action={deactivateMaster}>
                  <input type="hidden" name="id" value={master.id} />
                  <button className="rounded-full border border-blush-200 px-3 py-1 text-xs">Деактивировать</button>
                </form>
              </div>
            </div>
          </Card>
        ))}
      </div>
    </Container>
  );
}
