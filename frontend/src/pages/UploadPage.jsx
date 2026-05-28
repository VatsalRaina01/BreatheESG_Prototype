import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import Layout from '../components/Layout';
import { StatusBadge } from '../components/StatusBadge';
import { uploadFile, getSources, createSource } from '../api/client';
import { Upload, CloudUpload, CheckCircle, XCircle, AlertTriangle, Plus } from 'lucide-react';

export default function UploadPage() {
  const [sourceType, setSourceType] = useState('');
  const [sources, setSources] = useState([]);
  const [selectedSource, setSelectedSource] = useState('');
  const [newSourceName, setNewSourceName] = useState('');
  const [showNewSource, setShowNewSource] = useState(false);
  const [file, setFile] = useState(null);
  const [dragOver, setDragOver] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const fileInputRef = useRef(null);
  const navigate = useNavigate();

  useEffect(() => {
    loadSources();
  }, []);

  const loadSources = async () => {
    try {
      const { data } = await getSources();
      setSources(data.results || data || []);
    } catch (err) {
      console.error('Failed to load sources:', err);
    }
  };

  const filteredSources = sourceType
    ? sources.filter((s) => s.source_type === sourceType)
    : sources;

  const handleDragOver = (e) => {
    e.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = () => setDragOver(false);

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile) setFile(droppedFile);
  };

  const handleFileSelect = (e) => {
    const selected = e.target.files[0];
    if (selected) setFile(selected);
  };

  const handleCreateSource = async () => {
    if (!newSourceName || !sourceType) return;
    try {
      const { data } = await createSource({
        name: newSourceName,
        source_type: sourceType,
      });
      setSources((prev) => [...prev, data]);
      setSelectedSource(data.id);
      setShowNewSource(false);
      setNewSourceName('');
    } catch (err) {
      setError('Failed to create data source');
    }
  };

  const handleUpload = async () => {
    if (!file || !sourceType || !selectedSource) return;

    setUploading(true);
    setError('');
    setResult(null);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('source_type', sourceType);
    formData.append('data_source_id', selectedSource);

    try {
      const { data } = await uploadFile(formData);
      setResult(data);
      setFile(null);
      if (fileInputRef.current) fileInputRef.current.value = '';
    } catch (err) {
      setError(
        err.response?.data?.error ||
        err.response?.data?.detail ||
        'Upload failed. Please try again.'
      );
    } finally {
      setUploading(false);
    }
  };

  const sourceTypeOptions = [
    { value: 'sap', label: '🏭 SAP — Fuel & Procurement', desc: 'Semicolon-delimited flat file export' },
    { value: 'utility', label: '⚡ Utility — Electricity', desc: 'Portal CSV export with meter readings' },
    { value: 'travel', label: '✈️ Travel — Corporate Travel', desc: 'Concur-style expense report CSV' },
  ];

  return (
    <Layout title="Upload Data">
      <div style={{ maxWidth: 720 }}>
        {/* Step 1: Source Type */}
        <div className="form-group">
          <label className="form-label">Select Source Type</label>
          <select
            className="form-select"
            value={sourceType}
            onChange={(e) => {
              setSourceType(e.target.value);
              setSelectedSource('');
            }}
          >
            <option value="">Choose a data source type...</option>
            {sourceTypeOptions.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
          {sourceType && (
            <p className="text-muted" style={{ fontSize: 13, marginTop: 4 }}>
              {sourceTypeOptions.find((o) => o.value === sourceType)?.desc}
            </p>
          )}
        </div>

        {/* Step 2: Data Source */}
        {sourceType && (
          <div className="form-group">
            <label className="form-label">Select Data Source</label>
            <div className="flex gap-2">
              <select
                className="form-select"
                value={selectedSource}
                onChange={(e) => setSelectedSource(e.target.value)}
                style={{ flex: 1 }}
              >
                <option value="">Choose or create a source...</option>
                {filteredSources.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name}
                  </option>
                ))}
              </select>
              <button
                className="btn btn-secondary"
                onClick={() => setShowNewSource(!showNewSource)}
                title="Create new source"
              >
                <Plus size={18} />
              </button>
            </div>

            {showNewSource && (
              <div className="flex gap-2" style={{ marginTop: 8 }}>
                <input
                  type="text"
                  className="form-input"
                  placeholder={`e.g., "SAP Munich Plant" or "ComEd Portal"`}
                  value={newSourceName}
                  onChange={(e) => setNewSourceName(e.target.value)}
                  style={{ flex: 1 }}
                />
                <button className="btn btn-primary btn-sm" onClick={handleCreateSource}>
                  Create
                </button>
              </div>
            )}
          </div>
        )}

        {/* Step 3: File Upload */}
        {sourceType && selectedSource && (
          <>
            <div
              className={`dropzone ${dragOver ? 'drag-over' : ''}`}
              onClick={() => fileInputRef.current?.click()}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".csv,.txt,.tsv"
                onChange={handleFileSelect}
                hidden
              />
              <div className="dropzone-icon">
                <CloudUpload size={48} />
              </div>
              {file ? (
                <>
                  <div className="dropzone-title">{file.name}</div>
                  <div className="dropzone-subtitle">
                    {(file.size / 1024).toFixed(1)} KB — Click to change
                  </div>
                </>
              ) : (
                <>
                  <div className="dropzone-title">Drag and drop your file here</div>
                  <div className="dropzone-subtitle">or click to browse</div>
                  <div className="dropzone-hint">Supports CSV, TXT files up to 10MB</div>
                </>
              )}
            </div>

            <button
              className="btn btn-primary btn-lg btn-full"
              onClick={handleUpload}
              disabled={!file || uploading}
            >
              {uploading ? (
                <>
                  <span className="spinner" />
                  Processing...
                </>
              ) : (
                <>
                  <Upload size={20} />
                  Upload & Process
                </>
              )}
            </button>
          </>
        )}

        {/* Error */}
        {error && (
          <div className="login-error" style={{ marginTop: 16 }}>
            {error}
          </div>
        )}

        {/* Result */}
        {result && (
          <div className="upload-result" style={{ marginTop: 16 }}>
            <div className="upload-result-info">
              <CheckCircle size={24} className="text-green" />
              <div>
                <div style={{ fontWeight: 500 }}>{result.file_name || 'Upload complete'}</div>
                <div className="upload-result-stats">
                  <span className="text-green">
                    <CheckCircle size={14} /> {result.parsed_rows || 0} parsed
                  </span>
                  <span className="text-red">
                    <XCircle size={14} /> {result.failed_rows || 0} failed
                  </span>
                  <span className="text-amber">
                    <AlertTriangle size={14} /> {result.flagged_rows || 0} flagged
                  </span>
                </div>
              </div>
            </div>
            <button
              className="btn btn-secondary btn-sm"
              onClick={() => navigate('/review')}
            >
              View in Review →
            </button>
          </div>
        )}
      </div>
    </Layout>
  );
}
