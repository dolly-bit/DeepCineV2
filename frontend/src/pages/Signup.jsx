import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ArrowRight, Eye, EyeOff, Mail, Lock, UserRound, LoaderCircle } from "lucide-react";
import AuthShell from "../components/auth/AuthShell";
import api from "../services/api";

export default function Signup() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ username: "", email: "", password: "" });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [showPassword, setShowPassword] = useState(false);

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (loading) return;
    setLoading(true);
    setError("");
    try {
      await api.post("/auth/register", form);
      navigate("/login", { replace: true, state: { registered: true } });
    } catch (err) {
      setError(err.response?.data?.detail || "We couldn't create your account. Please review your details.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthShell mode="signup" eyebrow="YOUR TASTE. YOUR CINEMA." title={<>Find films that<br /><em>find you.</em></>} description="Build your own corner of cinema. Save the films you love and let your viewing taste shape what comes next." footer={<>Already have an account? <Link to="/login">Sign in <ArrowRight size={14} /></Link></>}>
      <form onSubmit={handleSubmit} className="auth-form">
        {error && <div role="alert" className="auth-error">{error}</div>}
        <label className="auth-label" htmlFor="signup-name">Your name</label>
        <div className="auth-input-wrap"><UserRound size={17} /><input id="signup-name" name="username" type="text" autoComplete="username" placeholder="How should we call you?" value={form.username} onChange={(e) => setForm({ ...form, username: e.target.value })} required minLength={2} /></div>
        <label className="auth-label" htmlFor="signup-email">Email address</label>
        <div className="auth-input-wrap"><Mail size={17} /><input id="signup-email" name="email" type="email" autoComplete="email" placeholder="you@example.com" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} required /></div>
        <label className="auth-label" htmlFor="signup-password">Create password</label>
        <div className="auth-input-wrap"><Lock size={17} /><input id="signup-password" name="password" type={showPassword ? "text" : "password"} autoComplete="new-password" placeholder="At least 8 characters" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} required minLength={8} /><button type="button" className="auth-icon-button" onClick={() => setShowPassword((value) => !value)} aria-label={showPassword ? "Hide password" : "Show password"}>{showPassword ? <EyeOff size={17} /> : <Eye size={17} />}</button></div>
        <button className="auth-submit" type="submit" disabled={loading}>{loading ? <><LoaderCircle className="animate-spin" size={17} /> Creating your account…</> : <>Create my account <ArrowRight size={17} /></>}</button>
      </form>
    </AuthShell>
  );
}
