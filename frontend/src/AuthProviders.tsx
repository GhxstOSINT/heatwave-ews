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
              <svg viewBox="0 0 24 24" focusable="false"><path fill="currentColor" d="M10.226 17.284c-2.965-.36-5.054-2.493-5.054-5.256 0-1.123.404-2.336 1.078-3.144-.292-.741-.247-2.314.09-2.965.898-.112 2.111.36 2.83 1.01.853-.269 1.752-.404 2.853-.404 1.1 0 1.999.135 2.807.382.696-.629 1.932-1.1 2.83-.988.315.606.36 2.179.067 2.942.72.854 1.101 2 1.101 3.167 0 2.763-2.089 4.852-5.098 5.234.763.494 1.28 1.572 1.28 2.807v2.336c0 .674.561 1.056 1.235.786 4.066-1.55 7.255-5.615 7.255-10.646C23.5 6.188 18.334 1 11.978 1 5.62 1 .5 6.188.5 12.545c0 4.986 3.167 9.12 7.435 10.669.606.225 1.19-.18 1.19-.786V20.63a2.9 2.9 0 0 1-1.078.224c-1.483 0-2.359-.808-2.987-2.313-.247-.607-.517-.966-1.034-1.033-.27-.023-.359-.135-.359-.27 0-.27.45-.471.898-.471.652 0 1.213.404 1.797 1.235.45.651.921.943 1.483.943.561 0 .92-.202 1.437-.719.382-.381.674-.718.944-.943"/></svg>
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
