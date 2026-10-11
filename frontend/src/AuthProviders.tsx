import { API, AuthConfig } from "./api";

type Provider = "google" | "github";
const providers: { id: Provider; label: string; mark: string }[] = [
  { id: "google", label: "Google", mark: "G" },
  { id: "github", label: "GitHub", mark: "GH" },
];

export function AuthProviders({ config, destination, action }: { config: AuthConfig | null; destination: string; action: "sign in" | "sign up" }) {
  return (
    <div className="auth-provider-list" aria-label={`Use a provider to ${action}`}>
      {providers.map(({ id, label, mark }) => {
        const enabled = config?.providers.includes(id) ?? false;
        return <a key={id} className={`auth-provider ${enabled ? "" : "unavailable"}`} href={enabled ? `${API}/auth/oauth/${id}/start?next=${encodeURIComponent(destination)}` : undefined} aria-disabled={!enabled} tabIndex={enabled ? 0 : -1}>
          <span className={`auth-provider-mark ${id}`} aria-hidden="true">{mark}</span>
          <span>Continue with {label}</span>
          <small>{enabled ? "→" : "Not configured"}</small>
        </a>;
      })}
    </div>
  );
}
