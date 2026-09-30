
import { useState } from "react";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { apiClient } from "@/lib/api-client";
import { showToast } from "@/utils/toast";
import { useNavigate } from "react-router";
import { PATHS } from "@/app/routes/paths";

export default function LoginPage() {
  const [email, setEmail] = useState(""); const [password, setPassword] = useState(""); const [loading, setLoading] = useState(false);
  const nav = useNavigate();
  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault(); setLoading(true);
    try {
      const { data } = await apiClient.post<{ token: string }>("/auth/login", { email, password });
      localStorage.setItem("rh_token", data.token);
      showToast({ message: "Logged in", type: "success" });
      nav(PATHS.dashboard);
    } catch (err: any) { showToast({ message: err.message, type: "error" }); } finally { setLoading(false); }
  };
  return <div className="flex min-h-dvh items-center justify-center p-6 bg-[var(--color-bg)]"><Card className="w-full max-w-sm p-8"><h1 className="text-xl font-semibold text-white">Rabbit Hire</h1><p className="mt-1 text-sm text-slate-500">Sign in to continue</p><form onSubmit={onSubmit} className="mt-6 space-y-4"><Input label="Email" value={email} onChange={e => setEmail(e.target.value)} placeholder="you@company.com" required /><Input label="Password" type="password" value={password} onChange={e => setPassword(e.target.value)} required /><Button type="submit" loading={loading} className="w-full">Sign in</Button></form></Card></div>;
}
