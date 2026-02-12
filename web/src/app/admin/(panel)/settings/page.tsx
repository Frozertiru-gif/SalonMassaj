import { adminFetch } from "@/lib/api";
import { Button } from "@/components/Button";
import { Card } from "@/components/Card";
import { Container } from "@/components/Container";
import { saveTelegramNotifications, sendTelegramTestMessage, updateSetting } from "../../actions";

type AdminSettingResponse = {
  value_jsonb: Record<string, unknown>;
};

type TgSettings = {
  enabled: boolean;
  admin_chat_id: string | number | null;
  thread_id: number | null;
  template_booking_created: string | null;
  template_booking_confirmed_admin: string | null;
  template_booking_assigned_master: string | null;
  send_inline_actions: boolean;
  public_webhook_base_url: string | null;
  webhook_secret: string | null;
};

async function updateAction(formData: FormData) {
  "use server";
  const key = String(formData.get("key"));
  const payload = String(formData.get("value_jsonb"));
  await updateSetting(key, JSON.parse(payload));
}

async function updateTelegramAction(formData: FormData) {
  "use server";
  await saveTelegramNotifications({}, formData);
}

async function sendTestAction(formData: FormData) {
  "use server";
  await sendTelegramTestMessage({}, formData);
}

const settingKeys = ["business_hours", "slot_step_min", "booking_rules", "contacts"];

export default async function AdminSettingsPage() {
  const [tgSetting, ...settings] = await Promise.all([
    adminFetch<AdminSettingResponse>(`/admin/settings/tg_notifications`),
    ...settingKeys.map((key) => adminFetch<AdminSettingResponse>(`/admin/settings/${key}`))
  ]);

  const tg = tgSetting.value_jsonb as unknown as TgSettings;

  return (
    <Container className="space-y-6">
      <div>
        <p className="text-sm uppercase tracking-[0.3em] text-blush-600">Настройки</p>
        <h2 className="mt-2 text-2xl font-semibold text-ink-900">Глобальные параметры</h2>
      </div>

      <Card className="space-y-3">
        <h3 className="text-lg font-semibold text-ink-900">Telegram-уведомления</h3>
        <form action={updateTelegramAction} className="grid gap-3 md:grid-cols-2">
          <label className="text-sm md:col-span-2">
            <input type="checkbox" name="enabled" className="mr-2" defaultChecked={Boolean(tg.enabled)} />
            Включить уведомления
          </label>
          <input
            name="admin_chat_id"
            placeholder="admin_chat_id"
            defaultValue={tg.admin_chat_id ? String(tg.admin_chat_id) : ""}
            className="rounded-2xl border border-blush-100 px-4 py-3 text-sm"
          />
          <input
            name="thread_id"
            type="number"
            placeholder="thread_id (optional)"
            defaultValue={tg.thread_id ?? ""}
            className="rounded-2xl border border-blush-100 px-4 py-3 text-sm"
          />
          <label className="text-sm md:col-span-2">
            <input type="checkbox" name="send_inline_actions" className="mr-2" defaultChecked={Boolean(tg.send_inline_actions)} />
            Inline-кнопки в Telegram
          </label>
          <input
            name="public_webhook_base_url"
            placeholder="public_webhook_base_url"
            defaultValue={tg.public_webhook_base_url ?? ""}
            className="rounded-2xl border border-blush-100 px-4 py-3 text-sm md:col-span-2"
          />
          <input
            name="webhook_secret"
            placeholder="webhook_secret"
            defaultValue={tg.webhook_secret ?? ""}
            className="rounded-2xl border border-blush-100 px-4 py-3 text-sm md:col-span-2"
          />
          <textarea
            name="template_booking_created"
            rows={5}
            defaultValue={tg.template_booking_created ?? ""}
            placeholder="Шаблон создания записи"
            className="rounded-2xl border border-blush-100 px-4 py-3 text-sm md:col-span-2"
          />
          <textarea
            name="template_booking_confirmed_admin"
            rows={2}
            defaultValue={tg.template_booking_confirmed_admin ?? ""}
            placeholder="Шаблон подтверждения для админа"
            className="rounded-2xl border border-blush-100 px-4 py-3 text-sm md:col-span-2"
          />
          <textarea
            name="template_booking_assigned_master"
            rows={4}
            defaultValue={tg.template_booking_assigned_master ?? ""}
            placeholder="Шаблон уведомления мастеру"
            className="rounded-2xl border border-blush-100 px-4 py-3 text-sm md:col-span-2"
          />
          <Button type="submit" variant="secondary" className="md:col-span-2">
            Сохранить Telegram
          </Button>
        </form>

        <form action={sendTestAction} className="space-y-3">
          <textarea
            name="test_text"
            rows={3}
            defaultValue="Тестовое сообщение из админ-панели SalonMassaj"
            className="w-full rounded-2xl border border-blush-100 px-4 py-3 text-sm"
          />
          <Button type="submit" variant="secondary">
            Отправить тест
          </Button>
        </form>
      </Card>

      <div className="space-y-4">
        {settings.map((setting, index) => (
          <Card key={settingKeys[index]} className="space-y-3">
            <h3 className="text-lg font-semibold text-ink-900">{settingKeys[index]}</h3>
            <form action={updateAction} className="space-y-3">
              <input type="hidden" name="key" value={settingKeys[index]} />
              <textarea
                name="value_jsonb"
                rows={6}
                defaultValue={JSON.stringify(setting.value_jsonb, null, 2)}
                className="w-full rounded-2xl border border-blush-100 px-4 py-3 text-sm"
              />
              <Button type="submit" variant="secondary">
                Сохранить
              </Button>
            </form>
          </Card>
        ))}
      </div>
    </Container>
  );
}
