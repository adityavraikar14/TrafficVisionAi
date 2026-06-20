import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { ShieldCheck } from "lucide-react";
import { useAuth } from "../context/AuthContext";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await login(username, password);
      navigate("/");
    } catch {
      setError("Invalid username or password.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-tv-bg px-4">
      <div className="tv-card w-full max-w-sm p-7">
        <div className="flex items-center gap-3 mb-1">
          <div className="w-11 h-11 rounded-2xl bg-tv-primary/15 border border-tv-primary/35 flex items-center justify-center">
            <ShieldCheck size={20} className="text-tv-primary" />
          </div>
          <div>
            <div className="font-black text-[16px] text-tv-text leading-tight">TrafficVision AI</div>
            <div className="text-[11px] text-tv-muted leading-tight mt-0.5">Officer Console Login</div>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="mt-6 flex flex-col gap-4">
          <div>
            <label className="text-[12px] font-bold text-tv-muted">Username</label>
            <input
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="mt-1 w-full bg-tv-bg-soft border border-tv-border rounded-xl px-3 py-2.5 text-sm text-tv-text outline-none focus:border-tv-primary/55"
              autoFocus
            />
          </div>
          <div>
            <label className="text-[12px] font-bold text-tv-muted">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="mt-1 w-full bg-tv-bg-soft border border-tv-border rounded-xl px-3 py-2.5 text-sm text-tv-text outline-none focus:border-tv-primary/55"
            />
          </div>

          {error && <div className="text-[12px] font-semibold text-tv-violation">{error}</div>}

          <button
            type="submit"
            disabled={loading || !username || !password}
            className="bg-gradient-to-br from-tv-primary to-tv-primary/80 text-white font-bold px-5 py-2.5 rounded-xl hover:-translate-y-0.5 transition disabled:opacity-60 disabled:translate-y-0"
          >
            {loading ? "Signing in…" : "Sign In"}
          </button>
        </form>

        <div className="mt-5 text-[11px] text-tv-muted text-center">
          Demo credentials: <span className="font-semibold">officer1 / TrafficPolice@123</span>
        </div>
      </div>
    </div>
  );
}
