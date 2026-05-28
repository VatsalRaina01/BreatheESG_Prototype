import { useState, useEffect } from 'react';
import Layout from '../components/Layout';
import { SourceBadge, ScopeBadge, StatusBadge, FlagDot } from '../components/StatusBadge';
import RecordDetail from '../components/RecordDetail';
import { getRecords, approveRecord, rejectRecord, bulkApprove, bulkReject } from '../api/client';
import { Search, CheckCircle, XCircle, Eye, Lock } from 'lucide-react';

export default function ReviewPage() {
  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedIds, setSelectedIds] = useState(new Set());
  const [detailRecord, setDetailRecord] = useState(null);
  const [filters, setFilters] = useState({
    source_type: '',
    scope: '',
    review_status: '',
    search: '',
  });
  const [page, setPage] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const pageSize = 20;

  useEffect(() => {
    loadRecords();
  }, [filters, page]);

  const loadRecords = async () => {
    setLoading(true);
    try {
      const params = { page, page_size: pageSize };
      if (filters.source_type) params.source_type = filters.source_type;
      if (filters.scope) params.scope = filters.scope;
      if (filters.review_status) params.review_status = filters.review_status;
      if (filters.search) params.search = filters.search;

      const { data } = await getRecords(params);
      setRecords(data.results || data || []);
      setTotalCount(data.count || (data.results || data || []).length);
    } catch (err) {
      console.error('Failed to load records:', err);
      setRecords([]);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectAll = (e) => {
    if (e.target.checked) {
      setSelectedIds(new Set(records.map((r) => r.id)));
    } else {
      setSelectedIds(new Set());
    }
  };

  const handleSelectOne = (id) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const handleApprove = async (id) => {
    try {
      await approveRecord(id);
      loadRecords();
    } catch (err) {
      console.error('Approve failed:', err);
    }
  };

  const handleReject = async (id) => {
    const comment = prompt('Reason for rejection (optional):');
    try {
      await rejectRecord(id, comment || '');
      loadRecords();
    } catch (err) {
      console.error('Reject failed:', err);
    }
  };

  const handleBulkApprove = async () => {
    if (selectedIds.size === 0) return;
    try {
      await bulkApprove(Array.from(selectedIds));
      setSelectedIds(new Set());
      loadRecords();
    } catch (err) {
      console.error('Bulk approve failed:', err);
    }
  };

  const handleBulkReject = async () => {
    if (selectedIds.size === 0) return;
    const comment = prompt('Reason for rejection (optional):');
    try {
      await bulkReject(Array.from(selectedIds), comment || '');
      setSelectedIds(new Set());
      loadRecords();
    } catch (err) {
      console.error('Bulk reject failed:', err);
    }
  };

  const totalPages = Math.ceil(totalCount / pageSize);

  const formatQuantity = (qty, unit) => {
    if (qty == null) return '—';
    const num = Number(qty);
    return `${num.toLocaleString(undefined, { maximumFractionDigits: 1 })} ${unit || ''}`.trim();
  };

  return (
    <Layout title="Review Records">
      <div className="table-container">
        {/* Toolbar */}
        <div className="table-toolbar">
          <div className="table-filters">
            <select
              className="filter-select"
              value={filters.source_type}
              onChange={(e) => { setFilters({ ...filters, source_type: e.target.value }); setPage(1); }}
            >
              <option value="">All Sources</option>
              <option value="sap">SAP</option>
              <option value="utility">Utility</option>
              <option value="travel">Travel</option>
            </select>

            <select
              className="filter-select"
              value={filters.scope}
              onChange={(e) => { setFilters({ ...filters, scope: e.target.value }); setPage(1); }}
            >
              <option value="">All Scopes</option>
              <option value="scope_1">Scope 1</option>
              <option value="scope_2">Scope 2</option>
              <option value="scope_3">Scope 3</option>
            </select>

            <select
              className="filter-select"
              value={filters.review_status}
              onChange={(e) => { setFilters({ ...filters, review_status: e.target.value }); setPage(1); }}
            >
              <option value="">All Statuses</option>
              <option value="pending">Pending</option>
              <option value="approved">Approved</option>
              <option value="rejected">Rejected</option>
              <option value="locked">Locked</option>
            </select>

            <div className="search-wrapper">
              <Search size={14} />
              <input
                type="text"
                className="search-input"
                placeholder="Search records..."
                value={filters.search}
                onChange={(e) => { setFilters({ ...filters, search: e.target.value }); setPage(1); }}
              />
            </div>
          </div>

          <div className="flex gap-2">
            <button
              className="btn btn-primary btn-sm"
              disabled={selectedIds.size === 0}
              onClick={handleBulkApprove}
            >
              <CheckCircle size={16} /> Approve ({selectedIds.size})
            </button>
            <button
              className="btn btn-danger btn-sm"
              disabled={selectedIds.size === 0}
              onClick={handleBulkReject}
            >
              <XCircle size={16} /> Reject ({selectedIds.size})
            </button>
          </div>
        </div>

        {/* Table */}
        <div style={{ overflowX: 'auto' }}>
          <table>
            <thead>
              <tr>
                <th style={{ width: 40 }}>
                  <input
                    type="checkbox"
                    className="table-checkbox"
                    onChange={handleSelectAll}
                    checked={records.length > 0 && selectedIds.size === records.length}
                  />
                </th>
                <th style={{ width: 40 }}>Flag</th>
                <th>Date</th>
                <th>Source</th>
                <th>Description</th>
                <th>Quantity</th>
                <th>Scope</th>
                <th>Status</th>
                <th style={{ width: 120 }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={9} className="text-center" style={{ padding: 40 }}>
                    <span className="spinner" style={{ margin: '0 auto' }} />
                  </td>
                </tr>
              ) : records.length === 0 ? (
                <tr>
                  <td colSpan={9} className="text-center text-muted" style={{ padding: 60 }}>
                    No records found. Upload data to get started.
                  </td>
                </tr>
              ) : (
                records.map((record) => (
                  <tr
                    key={record.id}
                    className={
                      record.is_flagged
                        ? record.flag_severity === 'critical'
                          ? 'row-flagged-critical'
                          : 'row-flagged-warning'
                        : ''
                    }
                  >
                    <td>
                      <input
                        type="checkbox"
                        className="table-checkbox"
                        checked={selectedIds.has(record.id)}
                        onChange={() => handleSelectOne(record.id)}
                        disabled={record.review_status === 'locked'}
                      />
                    </td>
                    <td>
                      <FlagDot severity={record.is_flagged ? record.flag_severity || 'warning' : null} />
                    </td>
                    <td className="text-secondary">
                      {record.activity_date || '—'}
                    </td>
                    <td>
                      <SourceBadge type={record.source_type} />
                    </td>
                    <td style={{ maxWidth: 250, overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      {record.description || '—'}
                    </td>
                    <td className="text-right">
                      {formatQuantity(record.quantity, record.unit)}
                    </td>
                    <td>
                      <ScopeBadge scope={record.scope} />
                    </td>
                    <td>
                      <StatusBadge status={record.review_status} />
                    </td>
                    <td>
                      {record.review_status === 'locked' ? (
                        <Lock size={16} className="text-muted" />
                      ) : (
                        <div className="flex gap-2">
                          {record.review_status !== 'approved' && (
                            <button
                              className="btn-ghost"
                              onClick={() => handleApprove(record.id)}
                              title="Approve"
                            >
                              <CheckCircle size={18} className="text-green" />
                            </button>
                          )}
                          {record.review_status !== 'rejected' && (
                            <button
                              className="btn-ghost"
                              onClick={() => handleReject(record.id)}
                              title="Reject"
                            >
                              <XCircle size={18} className="text-red" />
                            </button>
                          )}
                          <button
                            className="btn-ghost"
                            onClick={() => setDetailRecord(record)}
                            title="View details"
                          >
                            <Eye size={18} />
                          </button>
                        </div>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="table-pagination">
            <span>
              Showing {(page - 1) * pageSize + 1}–{Math.min(page * pageSize, totalCount)} of{' '}
              {totalCount} records
            </span>
            <div className="pagination-buttons">
              <button
                className="pagination-btn"
                disabled={page === 1}
                onClick={() => setPage(page - 1)}
              >
                ← Prev
              </button>
              {Array.from({ length: Math.min(totalPages, 5) }, (_, i) => i + 1).map((p) => (
                <button
                  key={p}
                  className={`pagination-btn ${page === p ? 'active' : ''}`}
                  onClick={() => setPage(p)}
                >
                  {p}
                </button>
              ))}
              <button
                className="pagination-btn"
                disabled={page === totalPages}
                onClick={() => setPage(page + 1)}
              >
                Next →
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Detail Panel */}
      {detailRecord && (
        <RecordDetail
          record={detailRecord}
          onClose={() => setDetailRecord(null)}
          onApprove={(id) => { handleApprove(id); setDetailRecord(null); }}
          onReject={(id) => { handleReject(id); setDetailRecord(null); }}
        />
      )}
    </Layout>
  );
}
