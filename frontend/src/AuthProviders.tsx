import { API, AuthConfig } from "./api";

type Provider = "google" | "github";
const providers: { id: Provider; label: string }[] = [
  { id: "google", label: "Google" },
  { id: "github", label: "GitHub" },
];

export function AuthProviders({ config, destination, action, configFailed }: { config: AuthConfig | null; destination: string; action: "sign in" | "sign up"; configFailed: boolean }) {
  return (
    <div className="auth-provider-list" role="group" aria-label={`Use a provider to ${action}`}>
      {providers.map(({ id, label }) => {
        const enabled = config?.providers.includes(id) ?? false;
        const content = <>
          <span className={`auth-provider-mark ${id}`} aria-hidden="true">
            {id === "google" ? (
              <svg viewBox="0 0 48 48" focusable="false"><path fill="#4285F4" d="M43.6 24.5c0-1.4-.1-2.8-.4-4.1H24v7.8h11a9.4 9.4 0 0 1-4.1 6.2v5.1h6.6c3.9-3.6 6.1-8.9 6.1-15Z"/><path fill="#34A853" d="M24 44c5.5 0 10.1-1.8 13.5-4.8l-6.6-5.1c-1.8 1.2-4.1 1.9-6.9 1.9-5.3 0-9.8-3.6-11.4-8.5H5.8v5.3A20 20 0 0 0 24 44Z"/><path fill="#FBBC05" d="M12.6 27.5a12 12 0 0 1 0-7v-5.3H5.8a20 20 0 0 0 0 17.6l6.8-5.3Z"/><path fill="#EA4335" d="M24 12c3 0 5.7 1 7.8 3.1l5.9-5.9A19.7 19.7 0 0 0 24 4 20 20 0 0 0 5.8 15.2l6.8 5.3C14.2 15.6 18.7 12 24 12Z"/></svg>
            ) : (
              <svg viewBox="0 0 24 24" focusable="false"><path fill="currentColor" d="M12 .9a11.1 11.1 0 0 0-3.5 21.6c.6.1.8-.2.8-.5v-2c-3.2.7-3.9-1.4-3.9-1.4-.5-1.3-1.3-1.7-1.3-1.7-1-.7.1-.7.1-.7 1.1.1 1.7 1.1 1.7 1.1 1 .1.7 2.2 3.8 1.6.1-.7.4-1.2.7-1.5-2.6-.3-5.3-1.3-5.3-5.8 0-1.3.5-2.3 1.2-3.1-.1-.3-.5-1.5.1-3.1 0 0 1-.3 3.2 1.2a11 11 0 0 1 5.8 0c2.2-1.5 3.2-1.2 3.2-1.2.6 1.6.2 2.8.1 3.1.8.8 1.2 1.8 1.2 3.1 0 4.5-2.7 5.5-5.3 5.8.4.3.8 1 .8 2v3c0 .3.2.6.8.5A11.1 11.1 0 0 0 12 .9Z"/></svg>
            )}
          </span>
          <span>Continue with {label}</span>
          <small>{enabled ? "Continue" : configFailed ? "Unavailable" : config ? "Not configured" : "Checking…"}</small>
        </>;
        return enabled
          ? <a key={id} className="auth-provider" href={`${API}/auth/oauth/${id}/start?next=${encodeURIComponent(destination)}`}>{content}</a>
          : <div key={id} className="auth-provider unavailable" aria-disabled="true">{content}</div>;
      })}
    </div>
  );
}
