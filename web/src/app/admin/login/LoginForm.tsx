"use client";

import { useFormState, useFormStatus } from "react-dom";

import { loginAdmin } from "../actions";
import type { LoginAdminState } from "../types";
import { Button } from "@/components/Button";

const initialState: LoginAdminState = {};

export function LoginForm() {
  const [state, formAction] = useFormState(loginAdmin, initialState);

  return (
    <form action={formAction} className="mt-6 space-y-4">
      <div>
        <label className="text-xs font-medium text-ink-700">Email</label>
        <input
          name="email"
          type="email"
          required
          className="mt-2 w-full rounded-2xl border border-blush-100 bg-white px-4 py-3 text-sm text-ink-900"
          placeholder="owner@example.com"
        />
      </div>
      <div>
        <label className="text-xs font-medium text-ink-700">Пароль</label>
        <input
          name="password"
          type="password"
          required
          className="mt-2 w-full rounded-2xl border border-blush-100 bg-white px-4 py-3 text-sm text-ink-900"
          placeholder="••••••"
        />
      </div>
      {state?.error ? <p className="text-sm text-red-600">{state.error}</p> : null}
      <SubmitButton />
    </form>
  );
}

function SubmitButton() {
  const { pending } = useFormStatus();

  return (
    <Button type="submit" className="w-full" disabled={pending}>
      {pending ? "Входим..." : "Войти"}
    </Button>
  );
}
