import React from 'react';
import '../styles/executive-timespot.css';
import { Plus } from 'lucide-react';
import type { DashboardStats, SapHealthResponse } from '../types';

interface ExecutiveTimeSpotCardProps {
  stats: DashboardStats | null;
  sapHealth: SapHealthResponse | null;
  sapCounts: { Items: number; BusinessPartners: number; Warehouses: number } | null;
  activeEntityTab: 'Items' | 'BusinessPartners' | 'Warehouses' | 'Workflows';
  onSelectEntityTab: (tab: 'Items' | 'BusinessPartners' | 'Warehouses' | 'Workflows') => void;
  onOpenUpload?: () => void;
}

export const ExecutiveTimeSpotCard: React.FC<ExecutiveTimeSpotCardProps> = ({
  stats,
  sapHealth: _sapHealth,
  sapCounts,
  activeEntityTab,
  onSelectEntityTab,
  onOpenUpload
}) => {
  const liveItemsCount = sapCounts?.Items ?? stats?.sap_counts?.Items ?? stats?.items_total ?? 0;
  const liveBpCount = sapCounts?.BusinessPartners ?? stats?.sap_counts?.BusinessPartners ?? stats?.business_partners_total ?? 0;
  const liveWhCount = sapCounts?.Warehouses ?? stats?.sap_counts?.Warehouses ?? stats?.warehouses_total ?? 0;
  const liveDocsCount = stats?.documents_processed ?? 0;

  // Dynamic heading based on active selected card
  const getMiddleHeading = () => {
    switch (activeEntityTab) {
      case 'BusinessPartners':
        return 'Business Partners';
      case 'Items':
        return 'Master Data Catalog';
      case 'Warehouses':
        return 'Warehouse Facilities';
      case 'Workflows':
        return 'Multi-Document Extraction & Workflows';
      default:
        return 'SAP Master Data Management';
    }
  };

  return (
    <section className="timespot-hero-section">
      {/* Middle Section: Bold Heading, Tagline & Action Button */}
      <div className="timespot-middle-section">
        <div className="timespot-middle-heading-block">
          <h2 className="timespot-middle-heading">
            {getMiddleHeading()}
          </h2>
        </div>

        <button
          type="button"
          onClick={onOpenUpload}
          className="timespot-add-action-btn"
          title="Create new master record or upload document"
        >
          <span>Add Another Record</span>
          <Plus size={15} />
        </button>
      </div>

      {/* 3. Bottom 4 Cards Row (Clicking any card activates the signature dark inverted card) */}
      <div className="timespot-cards-row">
        {/* Card 1: Items */}
        <div
          className={`timespot-subcard ${activeEntityTab === 'Items' ? 'active-dark' : 'light'}`}
          onClick={() => onSelectEntityTab('Items')}
          title="Switch to Item Master"
        >
          <div className="timespot-subcard-top">
            <span className="timespot-subcard-title">Item Masters</span>
          </div>
          <div className="timespot-subcard-bottom">
            <div className="timespot-subcard-number">
              {liveItemsCount.toLocaleString()}
            </div>
            <div className="timespot-subcard-badge">
              <span>📦 Active</span>
            </div>
          </div>
        </div>

        {/* Card 2: Business Partners */}
        <div
          className={`timespot-subcard ${activeEntityTab === 'BusinessPartners' ? 'active-dark' : 'light'}`}
          onClick={() => onSelectEntityTab('BusinessPartners')}
          title="Switch to Business Partners"
        >
          <div className="timespot-subcard-top">
            <span className="timespot-subcard-title">Business Partners</span>
          </div>
          <div className="timespot-subcard-bottom">
            <div className="timespot-subcard-number">
              {liveBpCount.toLocaleString()}
            </div>
            <div className="timespot-subcard-badge">
              <span>👥 Active</span>
            </div>
          </div>
        </div>

        {/* Card 3: Warehouses */}
        <div
          className={`timespot-subcard ${activeEntityTab === 'Warehouses' ? 'active-dark' : 'light'}`}
          onClick={() => onSelectEntityTab('Warehouses')}
          title="Switch to Warehouses"
        >
          <div className="timespot-subcard-top">
            <span className="timespot-subcard-title">Warehouses</span>
          </div>
          <div className="timespot-subcard-bottom">
            <div className="timespot-subcard-number">
              {liveWhCount.toLocaleString()}
            </div>
            <div className="timespot-subcard-badge">
              <span>🏭 Active</span>
            </div>
          </div>
        </div>

        {/* Card 4: Workflows */}
        <div
          className={`timespot-subcard ${activeEntityTab === 'Workflows' ? 'active-dark' : 'light'}`}
          onClick={() => onSelectEntityTab('Workflows')}
          title="Switch to Workflows"
        >
          <div className="timespot-subcard-top">
            <span className="timespot-subcard-title">Workflows</span>
            <span className="timespot-subcard-pill">Studio</span>
          </div>
          <div className="timespot-subcard-bottom">
            <div className="timespot-subcard-number">
              {liveDocsCount.toLocaleString()}
            </div>
            <div className="timespot-subcard-badge">
              <span>⚡ Documents Processed</span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
