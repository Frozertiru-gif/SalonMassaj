import { adminFetch } from "@/lib/api";
import { Button } from "@/components/Button";
import { Card } from "@/components/Card";
import { Container } from "@/components/Container";
import { updateSetting } from "../../actions";

async function updateAction(formData: FormData) {
  "use server";
  const key = String(formData.get("key"));
  const payload = String(formData.get("value_jsonb"));
  await updateSetting(key, JSON.parse(payload));
}

const settingKeys = ["business_hours", "slot_step_min", "booking_rules", "contacts", "tg_notifications"];

export default async function AdminSettingsPage() {
  const settings = await Promise.all(
    settingKeys.map(async (key) => ({ key, data: await adminFetch(`/admin/settings/${key}`) }))
  );

  return (
    <Container className="space-y-6">
      <div>
        <p className="text-sm uppercase tracking-[0.3em] text-blush-600">Настройки</p>
        <h2 className="mt-2 text-2xl font-semibold text-ink-900">Глобальные параметры</h2>
      </div>
      <div className="space-y-4">
        {settings.map((setting) => (
          <Card key={setting.key} className="space-y-3">
            <h3 className="text-lg font-semibold text-ink-900">{setting.key}</h3>
            <form action={updateAction} className="space-y-3">
              <input type="hidden" name="key" value={setting.key} />
              <textarea
                name="value_jsonb"
                rows={6}
                defaultValue={JSON.stringify(setting.data.value_jsonb, null, 2)}
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
