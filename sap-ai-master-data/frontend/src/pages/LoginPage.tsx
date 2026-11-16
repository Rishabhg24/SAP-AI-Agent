import React, { useState, useEffect } from 'react';
import {
  Mail,
  Lock,
  Eye,
  EyeOff,
  Sparkles,
  Loader2,
  CheckCircle2,
  ShieldCheck,
  ArrowRight
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import '../styles/login-page.css';
import smartAiOrb from '../assets/smart_ai_orb.jpg';
import cinntraLogo from '../assets/cinntra_logo.png';

export const LoginPage: React.FC = () => {
  const { login, demoLogin, googleLogin, activeCompanyDb, availableCompanies } = useAuth();

  const [companyDb, setCompanyDb] = useState(activeCompanyDb || 'TEST_SHOES_10SEP26');
  const [email, setEmail] = useState('alex.johnson@cinntra.com');
  const [password, setPassword] = useState('password123');
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [forgotModalOpen, setForgotModalOpen] = useState(false);
  const [forgotSent, setForgotSent] = useState(false);

  useEffect(() => {
    if (activeCompanyDb) {
      setCompanyDb(activeCompanyDb);
    }
  }, [activeCompanyDb]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) return;

    setSubmitting(true);
    try {
      await login({
        email,
        password,
        companyDb,
        rememberMe
      });
    } finally {
      setSubmitting(false);
    }
  };

  const handleDemoClick = () => {
    setSubmitting(true);
    setTimeout(() => {
      demoLogin();
      setSubmitting(false);
    }, 280);
  };

  const handleGoogleClick = () => {
    setSubmitting(true);
    setTimeout(() => {
      googleLogin();
      setSubmitting(false);
    }, 320);
  };

  return (
    <div className="login-viewport">
      {/* Background Ambient Glows */}
      <div className="login-ambient-glow login-ambient-glow-1" />
      <div className="login-ambient-glow login-ambient-glow-2" />

      {/* Main Glassmorphic Split Card */}
      <div className="login-card-container">
        {/* ==========================================================
            LEFT COLUMN: HERO ARTWORK PANEL (SAP AI BRAND THEME)
            ========================================================== */}
        <div className="login-hero-panel">
          <div className="login-hero-top">
            {/* Live SAP Company Database chip */}
            <div className="login-hero-chips-row">
              <div className="login-hero-chip">
                <span className="login-pulse-dot" />
                <span>SAP: {activeCompanyDb || 'TEST_SHOES_10SEP26'}</span>
              </div>
            </div>

            <div style={{ display: 'flex', alignItems: 'baseline' }}>
              <span className="login-hero-tagline-smart">SAP</span>
              <span className="login-hero-tagline-ai">AI</span>
            </div>
            <div className="login-hero-tagline-sub">MASTER DATA AUTOMATION</div>
          </div>

          {/* 3D Iridescent Orb Graphic */}
          <div className="login-hero-orb-stage">
            <img
              src={smartAiOrb}
              alt="SAP AI Master Data Orb"
              className="login-hero-orb-img"
            />
            <div className="login-hero-orb-podium" />
          </div>

          {/* Bottom Hero Description */}
          <div className="login-hero-bottom">
            <h2 className="login-hero-title">Intelligent SAP Master Data</h2>
            <p className="login-hero-desc">
              Autonomous AI extraction &amp; consensus for Item Master,
              Business Partners, and Warehouses with deterministic validation.
            </p>
          </div>
        </div>

        {/* ==========================================================
            RIGHT COLUMN: AUTHENTICATION FORM & SOCIAL LOGIN
            ========================================================== */}
        <div className="login-form-panel">
          <div className="login-form-header-area">
            {/* Top SAP Platform Logo Badge */}
            <div className="login-logo-badge">
              <img src={cinntraLogo} alt="CINNTRA" className="login-cinntra-logo" />
            </div>

            <h1 className="login-form-title">Welcome Back</h1>
            <p className="login-form-subtitle">
              Sign in to SAP AI Master Data Automation Platform
            </p>

            {/* Main Form */}
            <form onSubmit={handleSubmit}>
              {/* SAP Company Database Selection */}
              <div className="login-form-group">
                <label className="login-label" htmlFor="login-company-db">
                  SAP Company Database
                </label>
                <div className="login-input-wrapper">
                  <select
                    id="login-company-db"
                    value={companyDb}
                    onChange={(e) => setCompanyDb(e.target.value)}
                    className="login-input"
                    style={{ cursor: 'pointer', appearance: 'auto', paddingLeft: 12 }}
                  >
                    {availableCompanies.length > 0 ? (
                      availableCompanies.map((c, idx) => (
                        <option key={`${c.company_db}-${idx}`} value={c.company_db}>
                          {c.company_name} ({c.company_db})
                        </option>
                      ))
                    ) : (
                      <>
                        <option value="TEST_SHOES_10SEP26">TEST_SHOES_10SEP26 (SAP Live)</option>
                        <option value="CINNTRA_DEMO_NEW">Cinntra Infotech Solutions (CINNTRA_DEMO_NEW)</option>
                        <option value="SBODEMOUS">SAP US Demonstration (SBODEMOUS)</option>
                        <option value="SBODEMOIN">SAP India Demo (SBODEMOIN)</option>
                      </>
                    )}
                  </select>
                </div>
              </div>

              {/* Email Field */}
              <div className="login-form-group">
                <label className="login-label" htmlFor="login-email">
                  Enterprise Email / User ID
                </label>
                <div className="login-input-wrapper">
                  <Mail size={16} className="login-input-icon-left" />
                  <input
                    id="login-email"
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="alex.johnson@cinntra.com"
                    required
                    className="login-input"
                  />
                </div>
              </div>

              {/* Password Field */}
              <div className="login-form-group">
                <label className="login-label" htmlFor="login-password">
                  Password
                </label>
                <div className="login-input-wrapper">
                  <Lock size={16} className="login-input-icon-left" />
                  <input
                    id="login-password"
                    type={showPassword ? 'text' : 'password'}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••"
                    required
                    className="login-input"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="login-input-icon-right"
                    title={showPassword ? 'Hide password' : 'Show password'}
                  >
                    {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                  </button>
                </div>
              </div>

              {/* Remember Me & Forgot Password Row */}
              <div className="login-options-row">
                <label className="login-remember-label">
                  <input
                    type="checkbox"
                    checked={rememberMe}
                    onChange={(e) => setRememberMe(e.target.checked)}
                    className="login-checkbox"
                  />
                  <span>Remember me</span>
                </label>
                <button
                  type="button"
                  onClick={() => {
                    setForgotSent(false);
                    setForgotModalOpen(true);
                  }}
                  className="login-forgot-link"
                >
                  Forgot Password?
                </button>
              </div>

              {/* Sign In Button */}
              <button
                type="submit"
                disabled={submitting}
                className="login-submit-btn"
              >
                {submitting ? (
                  <>
                    <Loader2 size={16} className="animate-spin" />
                    <span>Signing in...</span>
                  </>
                ) : (
                  <>
                    <span>Sign In to Platform</span>
                    <ArrowRight size={15} />
                  </>
                )}
              </button>
            </form>

            {/* Divider */}
            <div className="login-divider">
              <span>Or Continue With</span>
            </div>

            {/* Google SSO Button */}
            <button
              type="button"
              onClick={handleGoogleClick}
              disabled={submitting}
              className="login-google-btn"
            >
              <svg width="18" height="18" viewBox="0 0 24 24">
                <path
                  fill="#4285F4"
                  d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                />
                <path
                  fill="#34A853"
                  d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                />
                <path
                  fill="#FBBC05"
                  d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"
                />
                <path
                  fill="#EA4335"
                  d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"
                />
              </svg>
              <span>Google Workspace SSO</span>
            </button>

            {/* Quick Demo Access Pill Button */}
            <button
              type="button"
              onClick={handleDemoClick}
              disabled={submitting}
              className="login-demo-pill-btn"
              title="Click for instant 1-click access to the SAP AI Platform"
            >
              <Sparkles size={14} color="#1A56DB" />
              <span>One-Click Demo Access (Cinntra1 / Admin)</span>
            </button>
          </div>
        </div>
      </div>

      {/* ==========================================================
          FORGOT PASSWORD MODAL
          ========================================================== */}
      {forgotModalOpen && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(0, 28, 61, 0.55)',
            backdropFilter: 'blur(6px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 100,
            padding: 20
          }}
          onClick={() => setForgotModalOpen(false)}
        >
          <div
            style={{
              background: '#FFFFFF',
              borderRadius: 20,
              padding: 28,
              width: '100%',
              maxWidth: 420,
              boxShadow: '0 20px 40px rgba(0, 28, 61, 0.2)',
              border: '1px solid #E2EEFA'
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 12 }}>
              <div
                style={{
                  width: 36,
                  height: 36,
                  borderRadius: 10,
                  background: '#EFF6FF',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}
              >
                <ShieldCheck size={20} color="#1A56DB" />
              </div>
              <h3 style={{ fontSize: 18, fontWeight: 700, color: '#0A1931', margin: 0 }}>
                Reset Password
              </h3>
            </div>

            {forgotSent ? (
              <div style={{ textAlign: 'center', padding: '16px 0' }}>
                <CheckCircle2 size={42} color="#10B981" style={{ margin: '0 auto 12px' }} />
                <p style={{ fontSize: 14, fontWeight: 600, color: '#0A1931' }}>
                  Reset link dispatched!
                </p>
                <p style={{ fontSize: 12.5, color: '#64748B', marginTop: 4 }}>
                  Instructions have been sent to <strong>{email}</strong>.
                </p>
                <button
                  type="button"
                  onClick={() => setForgotModalOpen(false)}
                  className="login-submit-btn"
                  style={{ marginTop: 18, height: 40 }}
                >
                  Close
                </button>
              </div>
            ) : (
              <>
                <p style={{ fontSize: 13, color: '#64748B', lineHeight: 1.5, marginBottom: 16 }}>
                  Enter your enterprise email to receive an SAP Service Layer password recovery link.
                </p>
                <div className="login-form-group">
                  <label className="login-label">Email Address</label>
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="login-input"
                    style={{ paddingLeft: 14 }}
                  />
                </div>
                <div style={{ display: 'flex', gap: 10, marginTop: 18 }}>
                  <button
                    type="button"
                    onClick={() => setForgotModalOpen(false)}
                    className="login-demo-pill-btn"
                    style={{ margin: 0, height: 42 }}
                  >
                    Cancel
                  </button>
                  <button
                    type="button"
                    onClick={() => setForgotSent(true)}
                    className="login-submit-btn"
                    style={{ height: 42 }}
                  >
                    Send Recovery Link
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default LoginPage;
