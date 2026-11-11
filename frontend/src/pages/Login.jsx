import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { ArrowRight, Eye, EyeOff, Mail, Lock, LoaderCircle } from "lucide-react";
import AuthShell from "../components/auth/AuthShell";
import api from "../services/api";
import { setAuthState } from "../services/auth";

export default function Login() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ email: "", password: "" });
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (loading) return;
    setLoading(true);
    setError("");
    try {
      const response = await api.post("/auth/login", form);
      setAuthState({ accessToken: response.data.access_token, userId: response.data.user_id, username: response.data.username });
      navigate("/home", { replace: true });
    } catch (err) {
      setError(err.response?.data?.detail || "We couldn't sign you in. Check your details and try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthShell mode="login" eyebrow="GOOD STORIES. BETTER DISCOVERY." title={<>Less scrolling.<br /><em>More cinema.</em></>} description="A recommendation space that learns what you love, connects the dots, and helps your next great watch find you." footer={<>New to DeepCine? <Link to="/signup">Create your account <ArrowRight size={14} /></Link></>}>
      <form onSubmit={handleSubmit} className="auth-form">
        {error && <div role="alert" className="auth-error">{error}</div>}
        <div className="auth-field">
          <label className="auth-label" htmlFor="login-email">Email address</label>
          <div className="auth-input-wrap"><Mail size={17} aria-hidden="true" /><input id="login-email" name="email" type="email" autoComplete="email" placeholder="you@example.com" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} required /></div>
        </div>
        <div className="auth-field">
          <label className="auth-label" htmlFor="login-password">Password</label>
          <div className="auth-input-wrap"><Lock size={17} aria-hidden="true" /><input id="login-password" name="password" type={showPassword ? "text" : "password"} autoComplete="current-password" placeholder="Enter your password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} required /><button type="button" className="auth-icon-button" onClick={() => setShowPassword((value) => !value)} aria-label={showPassword ? "Hide password" : "Show password"}>{showPassword ? <EyeOff size={17} /> : <Eye size={17} />}</button></div>
        </div>
        <button className="auth-submit" type="submit" disabled={loading}>{loading ? <><LoaderCircle className="animate-spin" size={17} /> Signing you in…</> : <>Enter DeepCine <ArrowRight size={17} /></>}</button>
      </form>
    </AuthShell>
  );
}
