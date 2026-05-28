import { useState, useEffect } from 'react';
import Layout from '../components/Layout';
import { SourceBadge, ScopeBadge, StatusBadge } from '../components/StatusBadge';
import { getDashboardSummary, getJobs } from '../api/client';
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { Database, Clock, CheckCircle, AlertTriangle, FileText } from 'lucide-react';

const SCOPE_COLORS = ['#2D6A4F', '#E9B44C', '#6B5B95'];
const SOURCE_COLORS = { sap: '#2D6A4F', utility: '#E9B44C', travel: '#6B5B95' };

export default function DashboardPage() {
  const [summary, setSummary] = useState(null);
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [summaryRes, jobsRes] = await Promise.all([
        getDashboardSummary(),
        getJobs(),
      ]);
      setSummary(summaryRes.data);
      setJobs(jobsRes.data.results || jobsRes.data || []);
    } catch (err) {
      console.error('Failed to load dashboard:', err);
      // Set default values if API not ready
      setSummary({
        total: 0,
        pending: 0,
        approved: 0,
        flagged: 0,
        by_scope: [],
        by_source: [],
      });
      setJobs([]);
    } finally {
      setLoading(false);
    }
  };

  const stats = [
    { label: 'Total Records', value: summary?.total || 0, icon: Database, color: 'blue' },
    { label: 'Pending Review', value: summary?.pending || 0, icon: Clock, color: 'amber' },
    { label: 'Approved', value: summary?.approved || 0, icon: CheckCircle, color: 'green' },
    { label: 'Flagged', value: summary?.flagged || 0, icon: AlertTriangle, color: 'red' },
  ];

  const scopeData = summary?.by_scope || [];
  const sourceData = summary?.by_source || [];

  const formatTimeAgo = (dateStr) => {
    if (!dateStr) return '—';
    const diff = Date.now() - new Date(dateStr).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 60) return `${mins}m ago`;
    const hrs = Math.floor(mins / 60);
    if (hrs < 24) return `${hrs}h ago`;
    const days = Math.floor(hrs / 24);
    return `${days}d ago`;
  };

  if (loading) {
    return (
      <Layout title="Dashboard">
        <div className="flex items-center justify-center" style={{ height: '60vh' }}>
          <span className="spinner" style={{ width: 40, height: 40 }} />
        </div>
      </Layout>
    );
  }

  return (
    <Layout title="Dashboard">
      {/* Stat Cards */}
      <div className="stat-grid">
        {stats.map((stat) => (
          <div className={`stat-card border-${stat.color}`} key={stat.label}>
            <div className={`stat-icon ${stat.color}`}>
              <stat.icon size={22} />
            </div>
            <div>
              <div className="stat-value">{stat.value.toLocaleString()}</div>
              <div className="stat-label">{stat.label}</div>
            </div>
          </div>
        ))}
      </div>

      {/* Charts */}
      <div className="charts-grid">
        <div className="card">
          <div className="card-title">Records by Scope</div>
          {scopeData.length > 0 ? (
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie
                  data={scopeData}
                  dataKey="count"
                  nameKey="scope"
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={90}
                  paddingAngle={4}
                  strokeWidth={0}
                >
                  {scopeData.map((_, index) => (
                    <Cell key={index} fill={SCOPE_COLORS[index % SCOPE_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{ background: '#FFFFFF', border: '1px solid #E5E2DC', borderRadius: 6, boxShadow: '0 2px 8px rgba(0,0,0,0.05)' }}
                  labelStyle={{ color: '#1A1A1A', fontWeight: 600 }}
                />
                <Legend
                  formatter={(value) => <span style={{ color: '#6B6B6B', fontSize: 13, textTransform: 'capitalize' }}>{value}</span>}
                />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="empty-state" style={{ padding: 40 }}>
              <p className="text-muted">No data yet</p>
            </div>
          )}
        </div>

        <div className="card">
          <div className="card-title">Records by Source</div>
          {sourceData.length > 0 ? (
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={sourceData} layout="vertical" margin={{ left: 20 }}>
                <XAxis type="number" tick={{ fill: '#64748B', fontSize: 12 }} />
                <YAxis
                  type="category"
                  dataKey="source"
                  tick={{ fill: '#94A3B8', fontSize: 13 }}
                  width={60}
                />
                <Tooltip
                  contentStyle={{ background: '#FFFFFF', border: '1px solid #E5E2DC', borderRadius: 6, boxShadow: '0 2px 8px rgba(0,0,0,0.05)' }}
                  labelStyle={{ color: '#1A1A1A', fontWeight: 600 }}
                />
                <Bar dataKey="count" radius={[0, 4, 4, 0]} barSize={28}>
                  {sourceData.map((entry) => (
                    <Cell key={entry.source} fill={SOURCE_COLORS[entry.source] || '#2D6A4F'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="empty-state" style={{ padding: 40 }}>
              <p className="text-muted">No data yet</p>
            </div>
          )}
        </div>
      </div>

      {/* Recent Jobs */}
      <div className="table-container">
        <div className="table-toolbar">
          <div className="card-title" style={{ marginBottom: 0 }}>Recent Uploads</div>
        </div>
        <table>
          <thead>
            <tr>
              <th>File Name</th>
              <th>Source</th>
              <th>Status</th>
              <th>Records</th>
              <th>Uploaded</th>
            </tr>
          </thead>
          <tbody>
            {jobs.length > 0 ? (
              jobs.slice(0, 5).map((job) => (
                <tr key={job.id}>
                  <td>
                    <span className="flex items-center gap-2">
                      <FileText size={16} className="text-muted" />
                      {job.file_name}
                    </span>
                  </td>
                  <td><SourceBadge type={job.data_source_type || job.source_type} /></td>
                  <td><StatusBadge status={job.status} /></td>
                  <td className="text-secondary">
                    {job.parsed_rows} parsed · {job.failed_rows} failed
                  </td>
                  <td className="text-muted">{formatTimeAgo(job.completed_at || job.started_at)}</td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={5} className="text-center text-muted" style={{ padding: 40 }}>
                  No uploads yet. Upload data to get started.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </Layout>
  );
}
