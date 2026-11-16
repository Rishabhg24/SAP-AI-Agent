import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import type { SapHealthResponse } from '../types';
import {
  Server,
  RefreshCw,
  CheckCircle,
  Lock,
  AlertTriangle,
  Save,
  FileCode,
  Sparkles,
  Database,
  Check
} from 'lucide-react';

interface ConnectionsConfig {
  server: {
    host: string;
    port: number;
    frontend_url: string;
    frontend_port?: number;
    cors_origins?: string[];
    environment: string;
    log_level: string;
  };
  sap: {
    service_layer_url: string;
    company_db: string;
    username: string;
    password_is_set: boolean;
    verify_ssl: boolean;
    timeout_seconds: number;
    is_configured: boolean;
  };
  ai: {
    nvidia_base_url: string;
    nvidia_model: string;
    nvidia_temperature: number;
    nvidia_max_tokens: number;
    api_key_is_set: boolean;
    is_configured: boolean;
  };
  database: {
    database_url: string;
    rag_collection_name: string;
    rag_db_path: string;
    embedding_model: string;
    rag_top_k: number;
    max_file_size_mb: number;
    upload_dir: string;
  };
  active_config_file: string;
}

export const SapStatus: React.FC = () => {
  const [health, setHealth] = useState<SapHealthResponse | null>(null);
  const [testing, setTesting] = useState(false);
  const [config, setConfig] = useState<ConnectionsConfig | null>(null);
  const [loadingConfig, setLoadingConfig] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState<string | null>(null);
  const [saveError, setSaveError] = useState<string | null>(null);

  // Form state for dynamic configuration
  const [formServerHost, setFormServerHost] = useState('');
  const [formServerPort, setFormServerPort] = useState<number>(8000);
  const [formFrontendUrl, setFormFrontendUrl] = useState('');
  const [formCorsOrigins, setFormCorsOrigins] = useState('');
  const [formSapUrl, setFormSapUrl] = useState('');
  const [formSapCompanyDb, setFormSapCompanyDb] = useState('');
  const [formSapUsername, setFormSapUsername] = useState('');
  const [formSapPassword, setFormSapPassword] = useState('');
  const [formAiKey, setFormAiKey] = useState('');
  const [formAiModel, setFormAiModel] = useState('');
  const [formAiBaseUrl, setFormAiBaseUrl] = useState('');

  const fetchConfig = async () => {
    setLoadingConfig(true);
    try {
      const data = await api.getConnectionsConfig();
      setConfig(data);
      if (data?.server) {
        setFormServerHost(data.server.host || '');
        setFormServerPort(data.server.port || 8000);
        setFormFrontendUrl(data.server.frontend_url || '');
        setFormCorsOrigins(
          Array.isArray(data.server.cors_origins)
            ? data.server.cors_origins.join(', ')
            : data.server.cors_origins || ''
        );
      }
      if (data?.sap) {
        setFormSapUrl(data.sap.service_layer_url || '');
        setFormSapCompanyDb(data.sap.company_db || '');
        setFormSapUsername(data.sap.username || '');
      }
      if (data?.ai) {
        setFormAiModel(data.ai.nvidia_model || '');
        setFormAiBaseUrl(data.ai.nvidia_base_url || '');
      }
    } catch (e) {
      console.error('Failed to load connections configuration', e);
    } finally {
      setLoadingConfig(false);
    }
  };

  const testConnection = async () => {
    setTesting(true);
    try {
      const data = await api.getSapHealth();
      setHealth(data);
    } catch (e: any) {
      console.error('SAP Health check failed:', e);
      setHealth({
        connected: false,
        status: 'DISCONNECTED',
        message: e?.response?.data?.message || e?.message || 'Failed to connect to SAP Service Layer or backend server.',
        service_layer_url: config?.sap?.service_layer_url || formSapUrl,
        company_db: config?.sap?.company_db || formSapCompanyDb,
        username: config?.sap?.username || formSapUsername,
      } as any);
    } finally {
      setTesting(false);
    }
  };

  const handleSwitchToSimulation = async () => {
    setSaving(true);
    setSaveSuccess(null);
    setSaveError(null);
    try {
      const res = await api.updateConnectionsConfig({
        sap: {
          service_layer_url: 'https://YOUR_SAP_SERVER:50000/b1s/v2',
          company_db: 'CINNTRA_DEMO_NEW',
          username: 'Cinntra1',
          password: 'YOUR_SAP_PASSWORD'
        }
      });
      setSaveSuccess(res.message || 'Switched to Simulated Sandbox mode. Local mock master data is now active.');
      setFormSapUrl('https://YOUR_SAP_SERVER:50000/b1s/v2');
      setFormSapPassword('');
      await fetchConfig();
      await testConnection();
    } catch (err: any) {
      setSaveError(err?.response?.data?.detail || err.message || 'Failed to switch to simulation mode.');
    } finally {
      setSaving(false);
    }
  };

  const handleLoadCinntraPresets = () => {
    setFormSapUrl('http://103.89.45.237:50001/b1s/v2');
    setFormSapCompanyDb('CINNTRA_DEMO_NEW');
    setFormSapUsername('Cinntra1');
    setFormSapPassword('1234');
  };

  const handleSaveConfig = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setSaveSuccess(null);
    setSaveError(null);

    const payload: any = {
      server: {
        host: formServerHost,
        port: Number(formServerPort),
        frontend_url: formFrontendUrl,
        cors_origins: formCorsOrigins
          .split(',')
          .map((s) => s.trim())
          .filter(Boolean),
      },
      sap: {
        service_layer_url: formSapUrl,
        company_db: formSapCompanyDb,
        username: formSapUsername,
      },
      ai: {
        nvidia_model: formAiModel,
        nvidia_base_url: formAiBaseUrl,
      },
    };

    if (formSapPassword.trim()) {
      payload.sap.password = formSapPassword.trim();
    }
    if (formAiKey.trim()) {
      payload.ai.nvidia_api_key = formAiKey.trim();
    }

    try {
      const res = await api.updateConnectionsConfig(payload);
      setSaveSuccess(res.message || 'Configuration saved and applied dynamically to connections.json.');
      setFormSapPassword('');
      setFormAiKey('');
      await fetchConfig();
      await testConnection();
    } catch (err: any) {
      setSaveError(err?.response?.data?.detail || err.message || 'Failed to save configuration.');
    } finally {
      setSaving(false);
    }
  };

  const handleReloadConfig = async () => {
    setLoadingConfig(true);
    setSaveSuccess(null);
    setSaveError(null);
    try {
      const res = await api.reloadConnectionsConfig();
      setSaveSuccess(res.message || 'Configuration reloaded from disk.');
      await fetchConfig();
      await testConnection();
    } catch (err: any) {
      setSaveError('Failed to reload configuration from disk.');
    } finally {
      setLoadingConfig(false);
    }
  };

  useEffect(() => {
    testConnection();
    fetchConfig();
  }, []);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
      <div>
        <h2 style={{ fontSize: 24, fontWeight: 700, letterSpacing: -0.4 }}>
          Service Layer & Web Server Configuration
        </h2>
        <p style={{ fontSize: 13, color: 'var(--text-secondary)' }}>
          Authoritative connection diagnostics, dynamic credentials management, and zero-SQL policy enforcement
        </p>
      </div>

      {/* Live Status Overview Card */}
      <div className="glass-panel" style={{ padding: 28 }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20, flexWrap: 'wrap', gap: 14 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <div style={{
              width: 42,
              height: 42,
              borderRadius: 10,
              background: 'rgba(59, 130, 246, 0.15)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              <Server size={22} color="#3B82F6" />
            </div>
            <div>
              <h3 style={{ fontSize: 16, fontWeight: 600 }}>Active Connection Status</h3>
              <p style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
                Target Server: <span style={{ fontFamily: 'monospace', color: '#93C5FD' }}>{health?.service_layer_url || config?.sap?.service_layer_url || 'Configured via connections.json'}</span>
              </p>
            </div>
          </div>

          <div style={{ display: 'flex', gap: 10 }}>
            <button
              onClick={handleReloadConfig}
              disabled={loadingConfig}
              className="btn btn-secondary"
              style={{ fontSize: 13, gap: 6 }}
              title="Reload configuration directly from connections.json"
            >
              <RefreshCw size={14} className={loadingConfig ? 'pulse-animation' : ''} />
              Reload from File
            </button>
            <button
              onClick={testConnection}
              disabled={testing}
              className="btn btn-primary"
              style={{ fontSize: 13, gap: 6 }}
            >
              <RefreshCw size={14} className={testing ? 'pulse-animation' : ''} />
              {testing ? 'Testing Service Layer...' : 'Run Connectivity Test'}
            </button>
          </div>
        </div>

        <div className="grid-3" style={{ marginBottom: 24 }}>
          <div style={{ background: '#F8FAFC', padding: 16, borderRadius: 'var(--radius-md)', border: '1px solid #E2E8F0' }}>
            <span style={{ fontSize: 11, color: '#64748B', display: 'block' }}>COMPANY DATABASE</span>
            <strong style={{ fontSize: 15, color: '#0F172A' }}>{health?.company_db || config?.sap?.company_db || 'Not Configured'}</strong>
          </div>
          <div style={{ background: '#F8FAFC', padding: 16, borderRadius: 'var(--radius-md)', border: '1px solid #E2E8F0' }}>
            <span style={{ fontSize: 11, color: '#64748B', display: 'block' }}>SAP USERNAME</span>
            <strong style={{ fontSize: 15, color: '#0F172A' }}>{health?.username || config?.sap?.username || 'Not Configured'}</strong>
          </div>
          <div style={{ background: '#F8FAFC', padding: 16, borderRadius: 'var(--radius-md)', border: '1px solid #E2E8F0' }}>
            <span style={{ fontSize: 11, color: '#64748B', display: 'block' }}>PASSWORD STATUS</span>
            <strong style={{ fontSize: 15, color: config?.sap?.password_is_set ? '#166534' : '#B45309', display: 'flex', alignItems: 'center', gap: 6 }}>
              <Lock size={14} /> {config?.sap?.password_is_set ? 'Active in Config' : 'Not Set'}
            </strong>
          </div>
        </div>

        {/* Authoritative Connection Diagnostics Banner */}
        {(() => {
          const isConn = Boolean(health?.connected || health?.status === 'CONNECTED' || (health as any)?.data?.connected);
          const isSimulation = health?.status === 'DEVELOPMENT_SIMULATION';

          return (
            <div style={{
              padding: '16px 20px',
              borderRadius: 'var(--radius-md)',
              background: testing
                ? '#EFF6FF'
                : isConn
                ? '#ECFDF5'
                : isSimulation
                ? '#F0FDF4'
                : '#FEF2F2',
              border: `1px solid ${
                testing
                  ? '#BFDBFE'
                  : isConn
                  ? '#A7F3D0'
                  : isSimulation
                  ? '#BBF7D0'
                  : '#FECACA'
              }`,
              display: 'flex',
              alignItems: 'flex-start',
              gap: 14,
              transition: 'all 0.2s ease'
            }}>
              <div style={{ marginTop: 2 }}>
                {testing ? (
                  <RefreshCw size={20} color="#2563EB" className="pulse-animation" />
                ) : isConn ? (
                  <CheckCircle size={20} color="#059669" />
                ) : isSimulation ? (
                  <Database size={20} color="#16A34A" />
                ) : (
                  <AlertTriangle size={20} color="#DC2626" />
                )}
              </div>
              <div style={{ flex: 1 }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 8 }}>
                  <strong style={{
                    fontSize: 14,
                    fontWeight: 700,
                    color: testing
                      ? '#1E40AF'
                      : isConn
                      ? '#065F46'
                      : isSimulation
                      ? '#166534'
                      : '#991B1B'
                  }}>
                    Status: {testing ? 'Testing Service Layer Connectivity...' : isConn ? 'CONNECTED (Live Master Data)' : `NOT CONNECTED (${health?.status || 'DISCONNECTED'})`}
                  </strong>
                  {(testing || health?.status) && (
                    <span style={{
                      fontSize: 11,
                      fontWeight: 600,
                      padding: '2px 8px',
                      borderRadius: 4,
                      background: testing
                        ? '#DBEAFE'
                        : isConn
                        ? '#D1FAE5'
                        : isSimulation
                        ? '#DCFCE7'
                        : '#FEE2E2',
                      color: testing
                        ? '#1E40AF'
                        : isConn
                        ? '#065F46'
                        : isSimulation
                        ? '#166534'
                        : '#991B1B'
                    }}>
                      {testing ? 'PROBING...' : isConn ? 'CONNECTED' : `NOT CONNECTED • ${health?.status}`}
                    </span>
                  )}
                </div>
                <p style={{
                  fontSize: 13,
                  color: testing
                    ? '#1D4ED8'
                    : isConn
                    ? '#047857'
                    : isSimulation
                    ? '#15803D'
                    : '#B91C1C',
                  marginTop: 4,
                  lineHeight: 1.5
                }}>
                  {testing
                    ? `Connecting to SAP Service Layer at ${health?.service_layer_url || config?.sap?.service_layer_url || formSapUrl || 'configured target server'}...`
                    : (health?.message || 'No connectivity response received. Click "Run Connectivity Test" to diagnose.')}
                </p>

                {!testing && !isConn && !isSimulation && (
                  <div style={{
                    marginTop: 12,
                    paddingTop: 10,
                    borderTop: '1px dashed #FCD34D',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    flexWrap: 'wrap',
                    gap: 10
                  }}>
                    <span style={{ fontSize: 12, color: '#78350F' }}>
                      Remote SAP server offline or unreachable? Switch to local development sandbox mode with instant mock data:
                    </span>
                    <button
                      type="button"
                      onClick={handleSwitchToSimulation}
                      className="btn btn-secondary"
                      style={{
                        padding: '5px 12px',
                        fontSize: 12,
                        background: '#FFFFFF',
                        borderColor: '#FCD34D',
                        color: '#92400E',
                        fontWeight: 600
                      }}
                    >
                      ⚡ Enable Simulated Sandbox Mode
                    </button>
                  </div>
                )}
              </div>
            </div>
          );
        })()}
      </div>

      {/* Dynamic Configuration Form Card */}
      <div className="glass-panel" style={{ padding: 28 }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20, flexWrap: 'wrap', gap: 12 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <FileCode size={20} color="#60A5FA" />
            <div>
              <h3 style={{ fontSize: 16, fontWeight: 700 }}>Dynamic Configuration File (`connections.json`)</h3>
              <p style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
                Modify parameters below to update <code>connections.json</code> dynamically without code changes
              </p>
            </div>
          </div>
          {config?.active_config_file && (
            <span style={{
              fontSize: 11,
              fontFamily: 'monospace',
              padding: '4px 10px',
              borderRadius: 6,
              background: 'rgba(59, 130, 246, 0.12)',
              color: '#93C5FD',
              border: '1px solid rgba(59, 130, 246, 0.3)'
            }}>
              Active File: {config.active_config_file.split('\\').pop() || 'connections.json'}
            </span>
          )}
        </div>

        {saveSuccess && (
          <div style={{
            padding: '12px 16px',
            marginBottom: 20,
            borderRadius: 'var(--radius-md)',
            background: 'rgba(16, 185, 129, 0.15)',
            border: '1px solid rgba(16, 185, 129, 0.35)',
            color: '#34D399',
            fontSize: 13,
            display: 'flex',
            alignItems: 'center',
            gap: 8
          }}>
            <Check size={16} />
            <span>{saveSuccess}</span>
          </div>
        )}

        {saveError && (
          <div style={{
            padding: '12px 16px',
            marginBottom: 20,
            borderRadius: 'var(--radius-md)',
            background: 'rgba(239, 68, 68, 0.15)',
            border: '1px solid rgba(239, 68, 68, 0.35)',
            color: '#F87171',
            fontSize: 13,
            display: 'flex',
            alignItems: 'center',
            gap: 8
          }}>
            <AlertTriangle size={16} />
            <span>{saveError}</span>
          </div>
        )}

        <form onSubmit={handleSaveConfig} style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
          {/* Web Server Parameters */}
          <div style={{ borderBottom: '1px solid var(--border-subtle)', paddingBottom: 20 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 14 }}>
              <Server size={16} color="#0284C7" />
              <h4 style={{ fontSize: 14, fontWeight: 600, color: '#0F172A' }}>Web Server Configuration</h4>
            </div>
            <div className="grid-3">
              <div>
                <label style={{ fontSize: 11.5, color: 'var(--text-secondary)', display: 'block', marginBottom: 6, fontWeight: 500 }}>
                  Server Host
                </label>
                <input
                  type="text"
                  className="form-input"
                  value={formServerHost}
                  onChange={(e) => setFormServerHost(e.target.value)}
                  placeholder="127.0.0.1"
                  required
                />
              </div>
              <div>
                <label style={{ fontSize: 11.5, color: 'var(--text-secondary)', display: 'block', marginBottom: 6, fontWeight: 500 }}>
                  Server Port
                </label>
                <input
                  type="number"
                  className="form-input"
                  value={formServerPort}
                  onChange={(e) => setFormServerPort(parseInt(e.target.value) || 8000)}
                  placeholder="8000"
                  required
                />
              </div>
              <div>
                <label style={{ fontSize: 11.5, color: 'var(--text-secondary)', display: 'block', marginBottom: 6, fontWeight: 500 }}>
                  Frontend Client URL
                </label>
                <input
                  type="text"
                  className="form-input"
                  value={formFrontendUrl}
                  onChange={(e) => setFormFrontendUrl(e.target.value)}
                  placeholder="http://localhost:5173"
                  required
                />
              </div>
            </div>
            <div style={{ marginTop: 14 }}>
              <label style={{ fontSize: 11.5, color: 'var(--text-secondary)', display: 'block', marginBottom: 6, fontWeight: 500 }}>
                Allowed CORS Origins (comma-separated origins)
              </label>
              <input
                type="text"
                className="form-input"
                value={formCorsOrigins}
                onChange={(e) => setFormCorsOrigins(e.target.value)}
                placeholder="http://localhost:5173, http://127.0.0.1:5173"
              />
            </div>
          </div>

          {/* SAP Service Layer Credentials */}
          <div style={{ borderBottom: '1px solid var(--border-subtle)', paddingBottom: 20 }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 14, flexWrap: 'wrap', gap: 10 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <Database size={16} color="#7C3AED" />
                <h4 style={{ fontSize: 14, fontWeight: 600, color: '#0F172A' }}>SAP Service Layer Parameters</h4>
              </div>
              <div style={{ display: 'flex', gap: 8 }}>
                <button
                  type="button"
                  onClick={handleLoadCinntraPresets}
                  className="btn btn-secondary"
                  style={{ fontSize: 11.5, padding: '4px 10px' }}
                  title="Fill in Cinntra Live demo credentials"
                >
                  Load Cinntra Live Credentials
                </button>
                <button
                  type="button"
                  onClick={handleSwitchToSimulation}
                  className="btn btn-secondary"
                  style={{ fontSize: 11.5, padding: '4px 10px' }}
                  title="Switch to safe local simulated sandbox"
                >
                  Use Simulation Sandbox
                </button>
              </div>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
              <div>
                <label style={{ fontSize: 11.5, color: 'var(--text-secondary)', display: 'block', marginBottom: 6, fontWeight: 500 }}>
                  Service Layer Base URL (SAP v2)
                </label>
                <input
                  type="text"
                  className="form-input"
                  value={formSapUrl}
                  onChange={(e) => setFormSapUrl(e.target.value)}
                  placeholder="https://your-sap-server:50000/b1s/v2"
                  required
                />
              </div>

              <div className="grid-3">
                <div>
                  <label style={{ fontSize: 11.5, color: 'var(--text-secondary)', display: 'block', marginBottom: 6, fontWeight: 500 }}>
                    Company Database (CompanyDB)
                  </label>
                  <input
                    type="text"
                    className="form-input"
                    value={formSapCompanyDb}
                    onChange={(e) => setFormSapCompanyDb(e.target.value)}
                    placeholder="YOUR_COMPANY_DB"
                    required
                  />
                </div>
                <div>
                  <label style={{ fontSize: 11.5, color: 'var(--text-secondary)', display: 'block', marginBottom: 6, fontWeight: 500 }}>
                    SAP Username (UserName)
                  </label>
                  <input
                    type="text"
                    className="form-input"
                    value={formSapUsername}
                    onChange={(e) => setFormSapUsername(e.target.value)}
                    placeholder="YOUR_SAP_USER"
                    required
                  />
                </div>
                <div>
                  <label style={{ fontSize: 11.5, color: 'var(--text-secondary)', display: 'block', marginBottom: 6, fontWeight: 500 }}>
                    Password {config?.sap?.password_is_set ? '(leave empty to keep current)' : ''}
                  </label>
                  <input
                    type="password"
                    className="form-input"
                    value={formSapPassword}
                    onChange={(e) => setFormSapPassword(e.target.value)}
                    placeholder={config?.sap?.password_is_set ? '••••••••' : 'Enter SAP password'}
                  />
                </div>
              </div>
            </div>
          </div>

          {/* AI LLM Settings */}
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 14 }}>
              <Sparkles size={16} color="#059669" />
              <h4 style={{ fontSize: 14, fontWeight: 600, color: '#0F172A' }}>NVIDIA AI Inference Engine</h4>
            </div>
            <div className="grid-3">
              <div>
                <label style={{ fontSize: 11.5, color: 'var(--text-secondary)', display: 'block', marginBottom: 6, fontWeight: 500 }}>
                  LLM Model Name
                </label>
                <input
                  type="text"
                  className="form-input"
                  value={formAiModel}
                  onChange={(e) => setFormAiModel(e.target.value)}
                  placeholder="nvidia/nemotron-3.5-lightning-30b-a3b"
                />
              </div>
              <div>
                <label style={{ fontSize: 11.5, color: 'var(--text-secondary)', display: 'block', marginBottom: 6, fontWeight: 500 }}>
                  API Base URL
                </label>
                <input
                  type="text"
                  className="form-input"
                  value={formAiBaseUrl}
                  onChange={(e) => setFormAiBaseUrl(e.target.value)}
                  placeholder="https://integrate.api.nvidia.com/v1"
                />
              </div>
              <div>
                <label style={{ fontSize: 11.5, color: 'var(--text-secondary)', display: 'block', marginBottom: 6, fontWeight: 500 }}>
                  NVIDIA API Key {config?.ai?.api_key_is_set ? '(leave empty to keep current)' : ''}
                </label>
                <input
                  type="password"
                  className="form-input"
                  value={formAiKey}
                  onChange={(e) => setFormAiKey(e.target.value)}
                  placeholder={config?.ai?.api_key_is_set ? '••••••••••••••••' : 'nvapi-...'}
                />
              </div>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: 10, paddingTop: 16, borderTop: '1px solid var(--border-subtle)', flexWrap: 'wrap', gap: 12 }}>
            <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>
              Configuration is persisted in <code>connections.json</code> and instantly applied to running services.
            </span>
            <button
              type="submit"
              disabled={saving}
              className="btn btn-primary"
              style={{ padding: '10px 22px', fontSize: 13, gap: 8 }}
            >
              <Save size={15} />
              {saving ? 'Applying Changes...' : 'Save & Apply Configuration'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
