export function SourceBadge({ type }) {
  const className = `badge badge-${type}`;
  const labels = { sap: 'SAP', utility: 'Utility', travel: 'Travel' };
  return <span className={className}>{labels[type] || type}</span>;
}

export function ScopeBadge({ scope }) {
  const map = {
    scope_1: { className: 'badge-scope1', label: 'Scope 1' },
    scope_2: { className: 'badge-scope2', label: 'Scope 2' },
    scope_3: { className: 'badge-scope3', label: 'Scope 3' },
  };
  const config = map[scope] || { className: 'badge-scope3', label: scope };
  return <span className={`badge ${config.className}`}>{config.label}</span>;
}

export function StatusBadge({ status }) {
  const map = {
    pending: 'badge-pending',
    approved: 'badge-approved',
    rejected: 'badge-rejected',
    locked: 'badge-locked',
    flagged: 'badge-flagged',
    completed: 'badge-completed',
    failed: 'badge-failed',
    processing: 'badge-processing',
  };
  const className = map[status] || 'badge-pending';
  const label = status ? status.charAt(0).toUpperCase() + status.slice(1) : 'Unknown';
  return <span className={`badge ${className}`}>{label}</span>;
}

export function FlagDot({ severity }) {
  if (!severity) return <span style={{ width: 8, display: 'inline-block' }} />;
  return <span className={`flag-dot ${severity}`} title={severity} />;
}
