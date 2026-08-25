import { useState } from "react";
import { login, updateSiteSettings } from "../api";

export default function SettingsModal({ open, onClose, token, email, settings, onAuthed, onSaved, onLogout }) {
  const [emailInput, setEmailInput] = useState("");
  const [passwordInput, setPasswordInput] = useState("");
  const [form, setForm] = useState(settings);
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);

  if (!open) return null;

  async function handleLogin(e) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      const res = await login(emailInput.trim(), passwordInput);
      onAuthed(res.token, res.email);
      setForm(settings);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  async function handleSave(e) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      const updated = await updateSiteSettings(form, token);
      onSaved(updated);
      onClose();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-card" onClick={(e) => e.stopPropagation()}>
        <button type="button" className="modal-close" onClick={onClose} aria-label="Close">
          &times;
        </button>

        {!token ? (
          <form onSubmit={handleLogin}>
            <h2>Sign in to edit dissertation details</h2>
            {error && <p className="modal-error">{error}</p>}
            <div className="field">
              <label htmlFor="login-email">Email</label>
              <input
                id="login-email"
                type="email"
                required
                autoFocus
                value={emailInput}
                onChange={(e) => setEmailInput(e.target.value)}
              />
            </div>
            <div className="field">
              <label htmlFor="login-password">Password</label>
              <input
                id="login-password"
                type="password"
                required
                value={passwordInput}
                onChange={(e) => setPasswordInput(e.target.value)}
              />
            </div>
            <button type="submit" disabled={busy}>
              {busy ? "Signing in…" : "Sign in"}
            </button>
          </form>
        ) : (
          <form onSubmit={handleSave}>
            <h2>Edit dissertation details</h2>
            <p className="modal-subtext">Signed in as {email}</p>
            {error && <p className="modal-error">{error}</p>}
            <div className="field">
              <label htmlFor="set-university">University / Department / Degree line</label>
              <input
                id="set-university"
                type="text"
                required
                value={form.university_line}
                onChange={(e) => setForm((f) => ({ ...f, university_line: e.target.value }))}
              />
            </div>
            <div className="field">
              <label htmlFor="set-submitted">Submitted by</label>
              <input
                id="set-submitted"
                type="text"
                required
                value={form.submitted_by}
                onChange={(e) => setForm((f) => ({ ...f, submitted_by: e.target.value }))}
              />
            </div>
            <div className="field">
              <label htmlFor="set-supervised">Supervised by</label>
              <input
                id="set-supervised"
                type="text"
                required
                value={form.supervised_by}
                onChange={(e) => setForm((f) => ({ ...f, supervised_by: e.target.value }))}
              />
            </div>
            <div className="modal-actions">
              <button type="submit" disabled={busy}>
                {busy ? "Saving…" : "Save"}
              </button>
              <button type="button" className="modal-link-btn" onClick={onLogout}>
                Log out
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
