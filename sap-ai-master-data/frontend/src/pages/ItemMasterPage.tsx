import React from 'react';
import { MasterDataModule } from '../components/MasterDataModule';

interface Props {
  onNavigateToAudit?: () => void;
}

export const ItemMasterPage: React.FC<Props> = ({ onNavigateToAudit }) => {
  return (
    <MasterDataModule
      masterType="item"
      title="Item Master"
      serviceLayerEndpoint="/b1s/v2/Items"
      description="Create, validate, and manage inventory, sales, and purchasing items with direct SAP Service Layer integration."
      onNavigateToAudit={onNavigateToAudit}
    />
  );
};
