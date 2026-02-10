import { adminFetch } from "@/lib/api";
import type { AdminProfile, AuditLog } from "@/lib/types";

export default async function AdminLogsPage() {
  const me = await adminFetch<AdminProfile>("/admin/auth/me");
  if (me.role !== "SYS_ADMIN") {
    return <p className="mx-auto max-w-5xl px-6 text-sm text-red-600">Недостаточно прав для просмотра логов.</p>;
  }

  const logs = await adminFetch<AuditLog[]>("/admin/logs?limit=200&offset=0");

  return (
    <div className="mx-auto max-w-6xl px-6">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-2xl font-semibold text-ink-900">Логи</h2>
        <a href="/admin/logs" className="rounded-2xl border border-blush-100 px-4 py-2 text-sm">
          Обновить
        </a>
      </div>
      <div className="overflow-x-auto rounded-2xl border border-blush-100 bg-white p-3">
        <table className="min-w-full text-left text-xs">
          <thead>
            <tr className="border-b border-blush-100">
              <th className="p-2">datetime</th>
              <th className="p-2">actor</th>
              <th className="p-2">role</th>
              <th className="p-2">action</th>
              <th className="p-2">entity_type</th>
              <th className="p-2">entity_id</th>
              <th className="p-2">summary</th>
              <th className="p-2">ip</th>
              <th className="p-2">user_agent</th>
            </tr>
          </thead>
          <tbody>
            {logs.map((item) => (
              <tr key={item.id} className="border-b border-blush-50 align-top">
                <td className="p-2 whitespace-nowrap">{new Date(item.created_at).toLocaleString()}</td>
                <td className="p-2">{item.actor_user_id ?? item.actor_tg_user_id ?? "-"}</td>
                <td className="p-2">{item.actor_role ?? "-"}</td>
                <td className="p-2">{item.action}</td>
                <td className="p-2">{item.entity_type}</td>
                <td className="p-2">{item.entity_id ?? "-"}</td>
                <td className="p-2 max-w-60 truncate">{JSON.stringify(item.meta || {})}</td>
                <td className="p-2">{item.ip ?? "-"}</td>
                <td className="p-2 max-w-60 truncate">{item.user_agent ?? "-"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
