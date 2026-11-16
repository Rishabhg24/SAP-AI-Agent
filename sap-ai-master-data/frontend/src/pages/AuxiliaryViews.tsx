import React, { useState } from 'react';
import {
  DollarSign,
  Search,
  CheckCircle,
  Clock,
  Plus
} from 'lucide-react';

/* ==========================================================
   1. Orders View (46 Orders)
   ========================================================== */
export const OrdersView: React.FC = () => {
  const [filter, setFilter] = useState<'all' | 'pending' | 'completed' | 'processing'>('all');
  const [search, setSearchSearch] = useState('');

  const orders = [
    { id: 'ORD-9021', customer: 'Nexus Electronics Ltd', items: 3, total: '$1,420.00', status: 'pending', date: 'Jan 31, 2025' },
    { id: 'ORD-9020', customer: 'Global Supply Partners', items: 12, total: '$5,890.50', status: 'completed', date: 'Jan 30, 2025' },
    { id: 'ORD-9019', customer: 'Apex Manufacturing Co', items: 1, total: '$420.00', status: 'processing', date: 'Jan 30, 2025' },
    { id: 'ORD-9018', customer: 'Vanguard Retail Chain', items: 6, total: '$2,750.00', status: 'completed', date: 'Jan 29, 2025' },
    { id: 'ORD-9017', customer: 'Horizon Direct Stores', items: 2, total: '$890.00', status: 'pending', date: 'Jan 28, 2025' },
    { id: 'ORD-9016', customer: 'Silverline Distributors', items: 8, total: '$4,120.00', status: 'completed', date: 'Jan 28, 2025' },
    { id: 'ORD-9015', customer: 'Precision Dynamics', items: 4, total: '$1,650.00', status: 'processing', date: 'Jan 27, 2025' },
  ];

  const filtered = orders.filter(o => {
    if (filter !== 'all' && o.status !== filter) return false;
    if (search && !o.customer.toLowerCase().includes(search.toLowerCase()) && !o.id.toLowerCase().includes(search.toLowerCase())) return false;
    return true;
  });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <h2 style={{ fontSize: 24, fontWeight: 700 }}>Orders Management</h2>
          <p style={{ fontSize: 13, color: 'var(--md-text-secondary)', marginTop: 2 }}>46 Active customer and wholesale orders</p>
        </div>
        <button className="md-btn-export"><Plus size={15} /> Create Order</button>
      </div>

      <div className="md-card">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
          <div style={{ display: 'flex', gap: 8 }}>
            {(['all', 'pending', 'processing', 'completed'] as const).map(tab => (
              <button
                key={tab}
                onClick={() => setFilter(tab)}
                style={{
                  padding: '6px 14px',
                  borderRadius: 'var(--md-radius-full)',
                  border: filter === tab ? '1px solid #2563EB' : '1px solid var(--md-border)',
                  background: filter === tab ? '#EFF6FF' : '#FFFFFF',
                  color: filter === tab ? '#2563EB' : 'var(--md-text-secondary)',
                  fontSize: 12,
                  fontWeight: 600,
                  cursor: 'pointer',
                  textTransform: 'capitalize'
                }}
              >
                {tab} {tab === 'all' && '(46)'}
              </button>
            ))}
          </div>
          <div style={{ position: 'relative' }}>
            <Search size={14} style={{ position: 'absolute', left: 10, top: 9, color: '#94A3B8' }} />
            <input
              type="text"
              placeholder="Search orders..."
              value={search}
              onChange={(e) => setSearchSearch(e.target.value)}
              style={{
                padding: '7px 12px 7px 32px',
                fontSize: 12,
                border: '1px solid var(--md-border)',
                borderRadius: 'var(--md-radius-full)',
                outline: 'none',
                width: 200
              }}
            />
          </div>
        </div>

        <div className="md-table-wrap">
          <table className="md-table">
            <thead>
              <tr>
                <th>ORDER ID</th>
                <th>CUSTOMER</th>
                <th>ITEMS</th>
                <th>TOTAL</th>
                <th>STATUS</th>
                <th>DATE</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map(o => (
                <tr key={o.id}>
                  <td style={{ fontWeight: 600, color: '#2563EB' }}>{o.id}</td>
                  <td style={{ fontWeight: 500 }}>{o.customer}</td>
                  <td>{o.items} items</td>
                  <td style={{ fontWeight: 600 }}>{o.total}</td>
                  <td>
                    <span style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: 4,
                      fontSize: 11,
                      fontWeight: 600,
                      padding: '3px 8px',
                      borderRadius: 12,
                      background: o.status === 'completed' ? '#E6FBF2' : o.status === 'pending' ? '#FEF3C7' : '#EFF6FF',
                      color: o.status === 'completed' ? '#10B981' : o.status === 'pending' ? '#D97706' : '#2563EB'
                    }}>
                      {o.status === 'completed' ? <CheckCircle size={12} /> : <Clock size={12} />}
                      {o.status.toUpperCase()}
                    </span>
                  </td>
                  <td style={{ color: 'var(--md-text-muted)', fontSize: 12 }}>{o.date}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

/* ==========================================================
   2. Products View
   ========================================================== */
export const ProductsView: React.FC = () => {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <h2 style={{ fontSize: 24, fontWeight: 700 }}>Products Catalog</h2>
          <p style={{ fontSize: 13, color: 'var(--md-text-secondary)', marginTop: 2 }}>Synchronized with SAP Items</p>
        </div>
        <button className="md-btn-export"><Plus size={15} /> Add New Product</button>
      </div>

      <div className="md-card">
        <div className="md-table-wrap">
          <table className="md-table">
            <thead>
              <tr>
                <th>CODE</th>
                <th>NAME</th>
                <th>CATEGORY</th>
                <th>PRICE</th>
                <th>STOCK</th>
                <th>SAP STATUS</th>
              </tr>
            </thead>
            <tbody>
              {[
                { code: 'ITM-83009', name: 'Hybrid Active Noise Cancelling Headphones', cat: 'Audio', price: '$149.00', stock: '482 in stock', sap: 'Synced' },
                { code: 'ITM-83001', name: 'Casio G-Shock Shock Resistant Watch', cat: 'Watches', price: '$89.00', stock: '210 in stock', sap: 'Synced' },
                { code: 'ITM-83004', name: 'SAMSUNG Galaxy S25 Ultra 512GB', cat: 'Electronics', price: '$1,199.00', stock: '64 in stock', sap: 'Synced' },
                { code: 'ITM-83002', name: 'Xbox Wireless Gaming Controller', cat: 'Gaming', price: '$59.00', stock: '148 in stock', sap: 'Synced' },
                { code: 'ITM-83005', name: "Timex Men's Easy Reader Classic", cat: 'Watches', price: '$49.00', stock: '320 in stock', sap: 'Synced' },
              ].map(p => (
                <tr key={p.code}>
                  <td style={{ fontWeight: 600, color: '#2563EB' }}>{p.code}</td>
                  <td style={{ fontWeight: 500 }}>{p.name}</td>
                  <td><span style={{ fontSize: 11, background: '#F1F5F9', padding: '2px 8px', borderRadius: 4 }}>{p.cat}</span></td>
                  <td style={{ fontWeight: 600 }}>{p.price}</td>
                  <td style={{ color: '#10B981', fontWeight: 500 }}>{p.stock}</td>
                  <td>
                    <span style={{ fontSize: 11, color: '#10B981', fontWeight: 600, display: 'inline-flex', alignItems: 'center', gap: 4 }}>
                      <CheckCircle size={12} /> {p.sap}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

/* ==========================================================
   3. Customers View
   ========================================================== */
export const CustomersView: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'retailers' | 'distributors' | 'wholesalers'>('retailers');

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      <div>
        <h2 style={{ fontSize: 24, fontWeight: 700 }}>Customers Directory</h2>
        <p style={{ fontSize: 13, color: 'var(--md-text-secondary)', marginTop: 2 }}>
          Breakdown: 2,884 Retailers • 1,432 Distributors • 562 Wholesalers
        </p>
      </div>

      <div style={{ display: 'flex', gap: 10 }}>
        <button
          onClick={() => setActiveTab('retailers')}
          style={{
            padding: '10px 18px',
            borderRadius: 'var(--md-radius-md)',
            background: activeTab === 'retailers' ? '#2563EB' : '#FFFFFF',
            color: activeTab === 'retailers' ? '#FFFFFF' : '#0F172A',
            border: '1px solid var(--md-border)',
            fontWeight: 600,
            fontSize: 13,
            cursor: 'pointer'
          }}
        >
          Retailers (2,884)
        </button>
        <button
          onClick={() => setActiveTab('distributors')}
          style={{
            padding: '10px 18px',
            borderRadius: 'var(--md-radius-md)',
            background: activeTab === 'distributors' ? '#10B981' : '#FFFFFF',
            color: activeTab === 'distributors' ? '#FFFFFF' : '#0F172A',
            border: '1px solid var(--md-border)',
            fontWeight: 600,
            fontSize: 13,
            cursor: 'pointer'
          }}
        >
          Distributors (1,432)
        </button>
        <button
          onClick={() => setActiveTab('wholesalers')}
          style={{
            padding: '10px 18px',
            borderRadius: 'var(--md-radius-md)',
            background: activeTab === 'wholesalers' ? '#F97316' : '#FFFFFF',
            color: activeTab === 'wholesalers' ? '#FFFFFF' : '#0F172A',
            border: '1px solid var(--md-border)',
            fontWeight: 600,
            fontSize: 13,
            cursor: 'pointer'
          }}
        >
          Wholesalers (562)
        </button>
      </div>

      <div className="md-card">
        <div className="md-table-wrap">
          <table className="md-table">
            <thead>
              <tr>
                <th>BP CODE</th>
                <th>CUSTOMER NAME</th>
                <th>SEGMENT</th>
                <th>TOTAL SPENT</th>
                <th>ORDERS</th>
                <th>STATUS</th>
              </tr>
            </thead>
            <tbody>
              {[
                { code: 'C10024', name: 'Apex Retail Stores Inc', seg: 'Retailer', spent: '$48,200', orders: 34, status: 'Active' },
                { code: 'C10088', name: 'Global Logistics Supply Corp', seg: 'Distributor', spent: '$182,450', orders: 112, status: 'Active' },
                { code: 'C10142', name: 'Western Wholesale Depot', seg: 'Wholesaler', spent: '$240,100', orders: 68, status: 'Active' },
                { code: 'C10219', name: 'Beacon Tech Retailers', seg: 'Retailer', spent: '$29,400', orders: 19, status: 'Active' },
              ].map(c => (
                <tr key={c.code}>
                  <td style={{ fontWeight: 600, color: '#2563EB' }}>{c.code}</td>
                  <td style={{ fontWeight: 500 }}>{c.name}</td>
                  <td>{c.seg}</td>
                  <td style={{ fontWeight: 600, color: '#10B981' }}>{c.spent}</td>
                  <td>{c.orders} orders</td>
                  <td><span style={{ fontSize: 11, background: '#E6FBF2', color: '#10B981', padding: '2px 8px', borderRadius: 10, fontWeight: 600 }}>{c.status}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

/* ==========================================================
   4. Finances View
   ========================================================== */
export const FinancesView: React.FC<{ subview: 'invoices' | 'transactions' | 'reports' }> = ({ subview }) => {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      <div>
        <h2 style={{ fontSize: 24, fontWeight: 700, textTransform: 'capitalize' }}>Finances - {subview}</h2>
        <p style={{ fontSize: 13, color: 'var(--md-text-secondary)', marginTop: 2 }}>
          SAP Service Layer financial entries and AR invoices
        </p>
      </div>

      <div className="md-card">
        <div style={{ padding: '20px 0', textAlign: 'center', color: 'var(--md-text-secondary)' }}>
          <DollarSign size={36} color="#2563EB" style={{ margin: '0 auto 12px' }} />
          <h4 style={{ fontSize: 16, fontWeight: 600, color: 'var(--md-text-primary)' }}>
            Financial Ledger Synced with SAP
          </h4>
          <p style={{ fontSize: 12.5, maxWidth: 440, margin: '6px auto 16px' }}>
            All incoming invoices and credit memos are audited via Service Layer endpoints with zero direct SQL writes.
          </p>
          <div style={{ display: 'inline-flex', gap: 10 }}>
            <button className="md-btn-export">Download Financial Audit PDF</button>
          </div>
        </div>
      </div>
    </div>
  );
};

/* ==========================================================
   5. Settings View
   ========================================================== */
export const SettingsView: React.FC = () => {
  const [sapHealth, setSapHealth] = React.useState<{ connected: boolean; status: string; company_db?: string } | null>(null);

  React.useEffect(() => {
    import('../services/api').then(({ api }) => {
      api.getSapHealth().then((h) => setSapHealth(h)).catch(() => setSapHealth({ connected: false, status: 'DISCONNECTED' }));
    });
  }, []);

  const isConn = Boolean(sapHealth?.connected);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      <div>
        <h2 style={{ fontSize: 24, fontWeight: 700 }}>Workspace Settings</h2>
        <p style={{ fontSize: 13, color: 'var(--md-text-secondary)', marginTop: 2 }}>
          Configuration for SAP Service Layer and AI Agent
        </p>
      </div>

      <div className="md-card" style={{ maxWidth: 640 }}>
        <h3 style={{ fontSize: 15, fontWeight: 600, marginBottom: 16 }}>Connection Status</h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', padding: '10px 14px', background: '#F8FAFC', borderRadius: 8 }}>
            <span style={{ fontSize: 13, color: 'var(--md-text-secondary)' }}>SAP Service Layer</span>
            <span style={{ fontSize: 13, fontWeight: 600, color: isConn ? '#10B981' : '#EF4444' }}>
              ● {isConn ? `Connected (${sapHealth?.company_db || 'Live'})` : `Not Connected (${sapHealth?.status || 'Disconnected'})`}
            </span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', padding: '10px 14px', background: '#F8FAFC', borderRadius: 8 }}>
            <span style={{ fontSize: 13, color: 'var(--md-text-secondary)' }}>AI Agent Model</span>
            <span style={{ fontSize: 13, fontWeight: 600, color: '#2563EB' }}>nvidia/nemotron-3.5-lightning-30b</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', padding: '10px 14px', background: '#F8FAFC', borderRadius: 8 }}>
            <span style={{ fontSize: 13, color: 'var(--md-text-secondary)' }}>Local Vector Store</span>
            <span style={{ fontSize: 13, fontWeight: 600, color: '#10B981' }}>ChromaDB (sap_knowledge)</span>
          </div>
        </div>
      </div>
    </div>
  );
};
