import React from 'react';
import { MasterDataModule } from '../components/MasterDataModule';

interface Props {
  onNavigateToAudit?: () => void;
}

export const WarehouseMasterPage: React.FC<Props> = ({ onNavigateToAudit }) => {
  return (
    <MasterDataModule
      masterType="warehouse"
      title="Warehouse Master"
      serviceLayerEndpoint="/b1s/v2/Warehouses"
      description="Create, validate, and manage physical and virtual storage facilities, bin locations, and logistics centers via SAP Service Layer."
      onNavigateToAudit={onNavigateToAudit}
    />
  );
};
