import React from 'react';
import type { WorkflowStatus } from '../types';

interface Props {
  status: WorkflowStatus | string;
}

export const StatusBadge: React.FC<Props> = ({ status }) => {
  const sStr = typeof status === 'string' ? status : (status != null ? String(status) : '');

  const getBadgeClass = (s: string) => {
    switch (s) {
      case 'CREATED':
      case 'READY_FOR_CONFIRMATION':
      case 'CONFIRMED':
      case 'AGREED':
        return 'badge-success';
      case 'EXTRACTION_CONFLICT':
      case 'DUPLICATE':
        return 'badge-warning';
      case 'MISSING_FIELDS':
      case 'SAP_ERROR':
      case 'FAILED':
      case 'CANCELLED':
        return 'badge-danger';
      case 'EXTRACTING':
      case 'VALIDATING':
      case 'CREATING_IN_SAP':
      case 'UPLOADED':
        return 'badge-info';
      default:
        return 'badge-neutral';
    }
  };

  const formatText = (s: string) => {
    if (s === 'MISSING_FIELDS') return 'MANDATORY FIELD REQUIRED';
    if (s === 'READY_FOR_CONFIRMATION' || s === 'AGREED') return 'MANDATORY PASSED';
    return s ? s.replace(/_/g, ' ') : 'N/A';
  };

  return (
    <span className={`badge ${getBadgeClass(sStr)}`}>
      <span style={{ width: 6, height: 6, borderRadius: '50%', background: 'currentColor' }} />
      {formatText(sStr)}
    </span>
  );
};
