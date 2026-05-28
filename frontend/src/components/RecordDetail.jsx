import { useState } from 'react';
import { SourceBadge, ScopeBadge, StatusBadge } from './StatusBadge';
import { X, AlertTriangle, CheckCircle, XCircle, Lock } from 'lucide-react';

export default function RecordDetail({ record, onClose, onApprove, onReject }) {
  const [activeTab, setActiveTab] = useState('normalized');
  const [comment, setComment] = useState('');

  if (!record) return null;

  const fields = [
    { label: 'Source Type', value: <SourceBadge type={record.source_type} /> },
    { label: 'Scope', value: <ScopeBadge scope={record.scope} /> },
    { label: 'Category', value: record.category || '—' },
    { label: 'Date', value: record.activity_date || '—' },
    { label: 'Description', value: record.description || '—' },
    { label: 'Quantity', value: record.quantity ? Number(record.quantity).toLocaleString() : '—' },
    { label: 'Unit', value: record.unit || '—' },
    { label: 'Original Unit', value: record.original_unit || '—' },
    { label: 'Amount', value: record.amount ? `${record.currency || ''} ${Number(record.amount).toLocaleString()}` : '—' },
    { label: 'Status', value: <StatusBadge status={record.review_status} /> },
  ];

  const metadata = record.source_metadata || {};
  const rawData = record.raw_data || record.raw_record_data || {};
  const flagReasons = record.flag_reasons || [];
  const auditTrail = record.audit_trail || [];

  return (
    <>
      {/* Overlay */}
      <div className="panel-overlay" onClick={onClose} />

      {/* Panel */}
      <div className="detail-panel">
        {/* Header */}
        <div className="panel-header">
          <div>
            <div className="panel-header-title">Record Detail</div>
            <div className="panel-header-id">#{record.id?.slice(0, 8)}</div>
          </div>
          <button className="btn-ghost" onClick={onClose}>
            <X size={20} />
          </button>
        </div>

        {/* Flag Banner */}
        {record.is_flagged && flagReasons.length > 0 && (
          <div className={`panel-flag-banner ${record.flag_severity === 'warning' ? 'warning' : ''}`}>
            <AlertTriangle size={16} />
            <div>
              {flagReasons.map((reason, i) => (
                <div key={i}>{reason}</div>
              ))}
            </div>
          </div>
        )}

        {/* Tabs */}
        <div className="panel-tabs">
          <button
            className={`panel-tab ${activeTab === 'normalized' ? 'active' : ''}`}
            onClick={() => setActiveTab('normalized')}
          >
            Normalized
          </button>
          <button
            className={`panel-tab ${activeTab === 'raw' ? 'active' : ''}`}
            onClick={() => setActiveTab('raw')}
          >
            Raw Data
          </button>
        </div>

        {/* Body */}
        <div className="panel-body">
          {activeTab === 'normalized' ? (
            <>
              {fields.map((field) => (
                <div className="panel-field" key={field.label}>
                  <span className="panel-field-label">{field.label}</span>
                  <span className="panel-field-value">{field.value}</span>
                </div>
              ))}

              {Object.keys(metadata).length > 0 && (
                <div className="panel-section">
                  <div className="panel-section-title">Source Metadata</div>
                  <div className="panel-metadata">
                    {Object.entries(metadata).map(([key, val]) => (
                      <div key={key}>
                        <span className="text-muted">{key}:</span> {String(val)}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {auditTrail.length > 0 && (
                <div className="panel-section">
                  <div className="panel-section-title">Audit History</div>
                  <div className="audit-timeline">
                    {auditTrail.map((entry, i) => (
                      <div className="audit-entry" key={i}>
                        <div className="audit-entry-time">{entry.performed_at}</div>
                        <div className="audit-entry-text">
                          {entry.performed_by} — {entry.action}
                          {entry.comment && `: "${entry.comment}"`}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          ) : (
            <div className="panel-metadata" style={{ whiteSpace: 'pre-wrap', lineHeight: 1.6 }}>
              {JSON.stringify(rawData, null, 2)}
            </div>
          )}
        </div>

        {/* Actions */}
        {record.review_status !== 'locked' && (
          <div className="panel-actions">
            <input
              type="text"
              className="form-input"
              placeholder="Add a comment (optional)"
              value={comment}
              onChange={(e) => setComment(e.target.value)}
            />
            <div className="panel-actions-buttons">
              <button
                className="btn btn-primary"
                style={{ flex: 1 }}
                onClick={() => onApprove(record.id)}
              >
                <CheckCircle size={16} /> Approve
              </button>
              <button
                className="btn btn-danger"
                style={{ flex: 1 }}
                onClick={() => onReject(record.id)}
              >
                <XCircle size={16} /> Reject
              </button>
            </div>
          </div>
        )}
      </div>
    </>
  );
}
