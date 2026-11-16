import React from 'react';
import { MasterDataModule } from '../components/MasterDataModule';

interface Props {
  onNavigateToAudit?: () => void;
}

export const BusinessPartnerPage: React.FC<Props> = ({ onNavigateToAudit }) => {
  return (
    <MasterDataModule
      masterType="business_partner"
      title="Business Partner Master"
      serviceLayerEndpoint="/b1s/v2/BusinessPartners"
      description="Create, validate, and manage Vendors, Customers, and Leads with strict SAP Service Layer compliance."
      onNavigateToAudit={onNavigateToAudit}
    />
  );
};
