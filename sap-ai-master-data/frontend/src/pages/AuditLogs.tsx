import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import type { AuditLogRecord } from '../types';
import { StatusBadge } from '../components/StatusBadge';
import {
  History,
  ShieldCheck,
  RefreshCw,
  Eye,
  Download,
  Search,
  User,
  Database,
  CheckCircle2,
  XCircle,
  X
} from 'lucide-react';

export const AuditLogs: React.FC = () => {
  const [logs, setLogs] = useState<AuditLogRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [downloading, setDownloading] = useState(false);
  const [selectedRecord, setSelectedRecord] = useState<AuditLogRecord | null>(null);

  // Filters
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCompany, setSelectedCompany] = useState('');
  const [selectedUser, setSelectedUser] = useState('');
  const [selectedActivity, setSelectedActivity] = useState('');
  const [daysFilter, setDaysFilter] = useState<number | null>(null);

  const fetchLogs = async () => {
    setLoading(true);
    try {
      const data = await api.getAuditLogs({
        limit: 150,
        days: daysFilter,
        userId: selectedUser || undefined,
        companyDb: selectedCompany || undefined,
        activity: selectedActivity || undefined,
        search: searchQuery || undefined,
      });
      setLogs(data);
    } catch (e) {
      console.error('Failed to fetch audit logs', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, [selectedCompany, selectedUser, selectedActivity, daysFilter]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    fetchLogs();
  };

  const handleDownloadLogFile = async () => {
    setDownloading(true);
    try {
      const { blob, filename } = await api.downloadAuditLogFile();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (e) {
      console.error('Failed to download log file', e);
    } finally {
      setDownloading(false);
    }
  };

  // Extract unique users and companies for filter dropdowns
  const uniqueUsers = Array.from(new Set(logs.map((l) => l.user_id || l.user_identifier).filter(Boolean)));
  const uniqueCompanies = Array.from(new Set(logs.map((l) => l.company_db).filter(Boolean)));
  const uniqueActivities = Array.from(new Set(logs.map((l) => l.activity || l.action).filter(Boolean)));

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      {/* Header Bar */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 14 }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <h2 style={{ fontSize: 22, fontWeight: 700, letterSpacing: -0.4, margin: 0 }}>
              System Transaction &amp; User Activity Audit Log
            </h2>
            <span style={{
              fontSize: 11,
              padding: '2px 8px',
              borderRadius: 9999,
              background: '#DCFCE7',
              color: '#166534',
              fontWeight: 600,
              border: '1px solid #BBF7D0'
            }}>
              Persistent Trail
            </span>
          </div>
          <p style={{ fontSize: 12.5, color: 'var(--text-secondary)', marginTop: 3, margin: 0 }}>
            Captures User ID, Timestamp, Company/Database, Transaction/Doc #, Activity, Previous Value, and Updated Value
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <button
            onClick={handleDownloadLogFile}
            disabled={downloading}
            className="btn btn-secondary"
            style={{ fontSize: 12, padding: '7px 14px', background: '#1E293B', borderColor: '#334155' }}
            title="Download full raw text log file for administrative audits"
          >
            <Download size={14} className={downloading ? 'pulse-animation' : ''} />
            <span>{downloading ? 'Downloading...' : 'Download Log File (.log)'}</span>
          </button>

          <button
            onClick={fetchLogs}
            disabled={loading}
            className="btn btn-secondary"
            style={{ fontSize: 12, padding: '7px 14px' }}
          >
            <RefreshCw size={14} className={loading ? 'pulse-animation' : ''} />
            <span>Refresh Trail</span>
          </button>
        </div>
      </div>

      {/* Filter & Search Bar */}
      <div className="glass-panel" style={{ padding: 14 }}>
        <form onSubmit={handleSearch} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
          {/* Search Box */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, flex: 1, minWidth: 220 }}>
            <div style={{ position: 'relative', width: '100%' }}>
              <Search size={15} style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)', color: '#64748B' }} />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search transaction #, doc ID, user, or details..."
                className="login-input"
                style={{ paddingLeft: 32, fontSize: 12, height: 36 }}
              />
            </div>
            <button type="submit" className="btn btn-primary" style={{ padding: '7px 14px', fontSize: 12 }}>
              Filter
            </button>
          </div>

          {/* Quick Selectors */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
            {/* User Filter */}
            <select
              value={selectedUser}
              onChange={(e) => setSelectedUser(e.target.value)}
              className="login-input"
              style={{ width: 'auto', fontSize: 12, height: 36, padding: '4px 10px', cursor: 'pointer' }}
            >
              <option value="">All Users</option>
              {uniqueUsers.map((u) => (
                <option key={u} value={u}>{u}</option>
              ))}
            </select>

            {/* Company DB Filter */}
            <select
              value={selectedCompany}
              onChange={(e) => setSelectedCompany(e.target.value)}
              className="login-input"
              style={{ width: 'auto', fontSize: 12, height: 36, padding: '4px 10px', cursor: 'pointer' }}
            >
              <option value="">All Databases</option>
              {uniqueCompanies.map((c) => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>

            {/* Activity Filter */}
            <select
              value={selectedActivity}
              onChange={(e) => setSelectedActivity(e.target.value)}
              className="login-input"
              style={{ width: 'auto', fontSize: 12, height: 36, padding: '4px 10px', cursor: 'pointer' }}
            >
              <option value="">All Activities</option>
              {uniqueActivities.map((a) => (
                <option key={a} value={a}>{a}</option>
              ))}
            </select>

            {/* Timeframe Filter */}
            <select
              value={daysFilter || ''}
              onChange={(e) => setDaysFilter(e.target.value ? Number(e.target.value) : null)}
              className="login-input"
              style={{ width: 'auto', fontSize: 12, height: 36, padding: '4px 10px', cursor: 'pointer' }}
            >
              <option value="">All Time</option>
              <option value="1">Last 24 Hours</option>
              <option value="7">Last 7 Days</option>
              <option value="30">Last 30 Days</option>
              <option value="90">Last 90 Days</option>
            </select>
          </div>
        </form>
      </div>

      {/* Main Table */}
      <div className="glass-panel" style={{ padding: 18 }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 14 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <ShieldCheck size={18} color="#10B981" />
            <h3 style={{ fontSize: 14, fontWeight: 700, margin: 0 }}>
              Audit Entries ({logs.length})
            </h3>
          </div>
          <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>
            Showing latest {logs.length} logged actions
          </span>
        </div>

        {logs.length > 0 ? (
          <div style={{ overflowX: 'auto' }}>
            <table className="data-table" style={{ width: '100%', fontSize: 12 }}>
              <thead>
                <tr>
                  <th style={{ width: 140 }}>Date &amp; Time</th>
                  <th>User ID</th>
                  <th>Company / DB</th>
                  <th>Transaction / Doc #</th>
                  <th>Activity</th>
                  <th>Previous Value</th>
                  <th>Updated Value</th>
                  <th>Outcome</th>
                  <th style={{ textAlign: 'center' }}>Inspect</th>
                </tr>
              </thead>
              <tbody>
                {logs.map((log) => {
                  const activityLabel = log.activity || log.action || 'TRANSACTION';
                  const userId = log.user_id || log.user_identifier || 'system';
                  const companyDb = log.company_db || 'CINNTRA_DEMO_NEW';
                  const transNum = log.transaction_num || log.sap_object_id || log.workflow_id || '—';

                  return (
                    <tr key={log.id}>
                      <td style={{ fontSize: 11.5, color: '#94A3B8', whiteSpace: 'nowrap' }}>
                        {new Date(log.timestamp).toLocaleString()}
                      </td>

                      {/* User ID */}
                      <td>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
                          <User size={12} color="#38BDF8" />
                          <span style={{ fontWeight: 600, color: '#F1F5F9' }}>
                            {userId}
                          </span>
                        </div>
                      </td>

                      {/* Company DB */}
                      <td>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
                          <Database size={12} color="#A78BFA" />
                          <span style={{ fontFamily: 'monospace', color: '#C4B5FD', fontSize: 11 }}>
                            {companyDb}
                          </span>
                        </div>
                      </td>

                      {/* Transaction / Document Number */}
                      <td>
                        <span style={{
                          fontWeight: 600,
                          color: '#60A5FA',
                          fontFamily: 'monospace',
                          background: 'rgba(96, 165, 250, 0.1)',
                          padding: '2px 6px',
                          borderRadius: 4
                        }}>
                          {transNum}
                        </span>
                      </td>

                      {/* Activity */}
                      <td>
                        <span style={{
                          fontSize: 10.5,
                          fontWeight: 700,
                          padding: '2px 7px',
                          borderRadius: 4,
                          background: activityLabel.includes('CREATE') ? '#065F46' : activityLabel.includes('UPDATE') ? '#1E40AF' : activityLabel.includes('COPY') ? '#854D0E' : 'rgba(255,255,255,0.1)',
                          color: '#FFFFFF',
                          letterSpacing: 0.3
                        }}>
                          {activityLabel}
                        </span>
                      </td>

                      {/* Previous Value */}
                      <td style={{ maxWidth: 140, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {log.previous_value ? (
                          <span style={{ color: '#F87171', fontFamily: 'monospace', fontSize: 11 }} title={log.previous_value}>
                            {log.previous_value}
                          </span>
                        ) : (
                          <span style={{ color: '#64748B', fontStyle: 'italic' }}>None</span>
                        )}
                      </td>

                      {/* Updated Value */}
                      <td style={{ maxWidth: 140, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {log.updated_value ? (
                          <span style={{ color: '#34D399', fontFamily: 'monospace', fontSize: 11 }} title={log.updated_value}>
                            {log.updated_value}
                          </span>
                        ) : (
                          <span style={{ color: '#94A3B8', fontSize: 11 }}>
                            {log.details || '—'}
                          </span>
                        )}
                      </td>

                      {/* Outcome */}
                      <td>
                        <StatusBadge status={log.success ? 'CREATED' : 'SAP_ERROR'} />
                      </td>

                      {/* Action */}
                      <td style={{ textAlign: 'center' }}>
                        <button
                          onClick={() => setSelectedRecord(log)}
                          className="btn btn-secondary"
                          style={{ padding: '3px 8px', fontSize: 11 }}
                          title="Inspect full audit record and field diff"
                        >
                          <Eye size={12} /> Diff
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        ) : (
          <div style={{ textAlign: 'center', padding: '40px 12px', color: 'var(--text-secondary)' }}>
            <History size={36} color="var(--text-muted)" style={{ margin: '0 auto 12px' }} />
            <p style={{ fontWeight: 600 }}>No audit trail records found matching filters.</p>
            <p style={{ fontSize: 12, color: 'var(--text-muted)' }}>Try adjusting your filters or resetting the search query.</p>
          </div>
        )}
      </div>

      {/* Diff Inspector Modal */}
      {selectedRecord && (
        <div style={{
          position: 'fixed',
          inset: 0,
          background: 'rgba(5, 8, 16, 0.85)',
          backdropFilter: 'blur(8px)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 100,
          padding: 20
        }}>
          <div className="glass-panel" style={{ width: '100%', maxWidth: 680, padding: 24, maxHeight: '90vh', overflowY: 'auto' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 18, borderBottom: '1px solid rgba(255,255,255,0.08)', paddingBottom: 12 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <ShieldCheck size={20} color="#10B981" />
                <h3 style={{ fontSize: 16, fontWeight: 700, margin: 0 }}>
                  Audit Trail Inspection #{selectedRecord.id}
                </h3>
              </div>
              <button
                onClick={() => setSelectedRecord(null)}
                style={{ background: 'none', border: 'none', color: '#94A3B8', cursor: 'pointer' }}
              >
                <X size={18} />
              </button>
            </div>

            {/* Metadata Badges */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 12, marginBottom: 18 }}>
              <div style={{ background: '#0B1120', padding: 10, borderRadius: 8, border: '1px solid rgba(255,255,255,0.05)' }}>
                <span style={{ fontSize: 10.5, color: '#64748B', display: 'block', textTransform: 'uppercase' }}>User ID / Login</span>
                <strong style={{ fontSize: 12.5, color: '#38BDF8' }}>
                  {selectedRecord.user_id || selectedRecord.user_identifier}
                </strong>
              </div>

              <div style={{ background: '#0B1120', padding: 10, borderRadius: 8, border: '1px solid rgba(255,255,255,0.05)' }}>
                <span style={{ fontSize: 10.5, color: '#64748B', display: 'block', textTransform: 'uppercase' }}>Company / Database</span>
                <strong style={{ fontSize: 12.5, color: '#C4B5FD', fontFamily: 'monospace' }}>
                  {selectedRecord.company_db || 'CINNTRA_DEMO_NEW'}
                </strong>
              </div>

              <div style={{ background: '#0B1120', padding: 10, borderRadius: 8, border: '1px solid rgba(255,255,255,0.05)' }}>
                <span style={{ fontSize: 10.5, color: '#64748B', display: 'block', textTransform: 'uppercase' }}>Transaction / Doc #</span>
                <strong style={{ fontSize: 12.5, color: '#60A5FA', fontFamily: 'monospace' }}>
                  {selectedRecord.transaction_num || selectedRecord.sap_object_id || selectedRecord.workflow_id}
                </strong>
              </div>

              <div style={{ background: '#0B1120', padding: 10, borderRadius: 8, border: '1px solid rgba(255,255,255,0.05)' }}>
                <span style={{ fontSize: 10.5, color: '#64748B', display: 'block', textTransform: 'uppercase' }}>Date &amp; Time</span>
                <span style={{ fontSize: 12, color: '#F1F5F9' }}>
                  {new Date(selectedRecord.timestamp).toLocaleString()}
                </span>
              </div>
            </div>

            {/* Previous vs Updated Value Diff Box */}
            <div style={{ marginBottom: 18 }}>
              <span style={{ fontSize: 12, fontWeight: 700, color: '#E2E8F0', display: 'block', marginBottom: 8 }}>
                Change Comparison (Previous Value vs Updated Value):
              </span>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                {/* Previous Value */}
                <div style={{
                  background: 'rgba(239, 68, 68, 0.08)',
                  border: '1px solid rgba(239, 68, 68, 0.25)',
                  borderRadius: 8,
                  padding: 12
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 6 }}>
                    <XCircle size={13} color="#EF4444" />
                    <span style={{ fontSize: 11, fontWeight: 700, color: '#FCA5A5', textTransform: 'uppercase' }}>
                      Previous Value
                    </span>
                  </div>
                  <pre style={{ margin: 0, fontSize: 11, color: '#F87171', fontFamily: 'monospace', whiteSpace: 'pre-wrap', wordBreak: 'break-all' }}>
                    {selectedRecord.previous_value || 'No prior value recorded (Created new)'}
                  </pre>
                </div>

                {/* Updated Value */}
                <div style={{
                  background: 'rgba(16, 185, 129, 0.08)',
                  border: '1px solid rgba(16, 185, 129, 0.25)',
                  borderRadius: 8,
                  padding: 12
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 6 }}>
                    <CheckCircle2 size={13} color="#10B981" />
                    <span style={{ fontSize: 11, fontWeight: 700, color: '#6EE7B7', textTransform: 'uppercase' }}>
                      Updated / Applied Value
                    </span>
                  </div>
                  <pre style={{ margin: 0, fontSize: 11, color: '#34D399', fontFamily: 'monospace', whiteSpace: 'pre-wrap', wordBreak: 'break-all' }}>
                    {selectedRecord.updated_value || selectedRecord.details || 'Successfully committed'}
                  </pre>
                </div>
              </div>
            </div>

            {/* Execution Details */}
            <div style={{ marginBottom: 18 }}>
              <span style={{ fontSize: 12, fontWeight: 700, color: '#E2E8F0', display: 'block', marginBottom: 6 }}>
                Execution Details &amp; Payload Hash:
              </span>
              <div style={{ background: '#0B1120', padding: 12, borderRadius: 8, fontSize: 12, color: '#94A3B8' }}>
                <p style={{ margin: '0 0 8px 0', color: '#F1F5F9' }}>
                  {selectedRecord.details || 'Transaction executed and confirmed successfully.'}
                </p>
                {selectedRecord.payload_hash && (
                  <div style={{ fontSize: 11, fontFamily: 'monospace', color: '#64748B' }}>
                    Payload SHA-256: {selectedRecord.payload_hash}
                  </div>
                )}
              </div>
            </div>

            {/* Modal Footer */}
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10 }}>
              <button onClick={() => setSelectedRecord(null)} className="btn btn-secondary" style={{ fontSize: 12 }}>
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

