import { useState, useEffect } from 'react';
import Layout from '../components/Layout';
import { SourceBadge, StatusBadge } from '../components/StatusBadge';
import { getJobs } from '../api/client';
import { FileText, RefreshCcw } from 'lucide-react';

export default function JobsPage() {
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadJobs();
  }, []);

  const loadJobs = async () => {
    setLoading(true);
    try {
      const { data } = await getJobs();
      setJobs(data.results || data || []);
    } catch (err) {
      console.error('Failed to load jobs:', err);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '—';
    return new Date(dateStr).toLocaleString();
  };

  return (
    <Layout title="Ingestion Jobs">
      <div className="flex justify-between items-center mb-4">
        <p className="text-secondary">History of all file uploads and their processing results.</p>
        <button className="btn btn-secondary btn-sm" onClick={loadJobs}>
          <RefreshCcw size={14} /> Refresh
        </button>
      </div>

      <div className="table-container">
        <table>
          <thead>
            <tr>
              <th>File Name</th>
              <th>Source</th>
              <th>Status</th>
              <th>Total</th>
              <th>Parsed</th>
              <th>Failed</th>
              <th>Flagged</th>
              <th>Uploaded By</th>
              <th>Date</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={9} className="text-center" style={{ padding: 40 }}>
                  <span className="spinner" style={{ margin: '0 auto' }} />
                </td>
              </tr>
            ) : jobs.length === 0 ? (
              <tr>
                <td colSpan={9} className="text-center text-muted" style={{ padding: 60 }}>
                  No ingestion jobs yet. Upload a file to create one.
                </td>
              </tr>
            ) : (
              jobs.map((job) => (
                <tr key={job.id}>
                  <td>
                    <span className="flex items-center gap-2">
                      <FileText size={16} className="text-muted" />
                      {job.file_name}
                    </span>
                  </td>
                  <td><SourceBadge type={job.data_source_type || job.source_type} /></td>
                  <td><StatusBadge status={job.status} /></td>
                  <td>{job.total_rows || 0}</td>
                  <td className="text-green">{job.parsed_rows || 0}</td>
                  <td className={job.failed_rows > 0 ? 'text-red' : 'text-muted'}>{job.failed_rows || 0}</td>
                  <td className={job.flagged_rows > 0 ? 'text-amber' : 'text-muted'}>{job.flagged_rows || 0}</td>
                  <td className="text-secondary">{job.uploaded_by_email || '—'}</td>
                  <td className="text-muted">{formatDate(job.started_at)}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </Layout>
  );
}
