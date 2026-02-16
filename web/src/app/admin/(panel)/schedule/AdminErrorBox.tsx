export function AdminErrorBox({ message }: { message: string }) {
  return (
    <div className="rounded-2xl border border-rose-200 bg-rose-50 p-4 text-rose-700">
      <p className="text-sm font-medium">Не удалось загрузить расписание</p>
      <p className="mt-1 text-sm">{message}</p>
    </div>
  );
}
