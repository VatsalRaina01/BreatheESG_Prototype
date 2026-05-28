import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Leaf } from 'lucide-react';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await login(email, password);
      navigate('/dashboard');
    } catch (err) {
      setError(
        err.response?.data?.detail ||
        err.response?.data?.error ||
        'Invalid credentials. Please try again.'
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-container">
      <div className="login-bg-mesh" />

      <form className="login-card" onSubmit={handleSubmit}>
        <div className="login-logo">
          <div className="login-logo-icon">
            <Leaf size={28} />
          </div>
          <h1 className="login-logo-title">Breathe ESG</h1>
          <p className="login-logo-subtitle">Emissions Data Intelligence</p>
        </div>

        {error && <div className="login-error">{error}</div>}

        <div className="form-group">
          <label className="form-label" htmlFor="email">Email</label>
          <input
            id="email"
            type="email"
            className="form-input"
            placeholder="analyst@company.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            autoFocus
          />
        </div>

        <div className="form-group">
          <label className="form-label" htmlFor="password">Password</label>
          <input
            id="password"
            type="password"
            className="form-input"
            placeholder="Enter your password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </div>

        <button
          type="submit"
          className="btn btn-primary btn-lg btn-full"
          disabled={loading}
          style={{ marginTop: 8 }}
        >
          {loading ? (
            <>
              <span className="spinner" />
              Signing in...
            </>
          ) : (
            'Sign In'
          )}
        </button>

        <p
          className="text-center text-muted"
          style={{ marginTop: 24, fontSize: 12 }}
        >
          Secure emissions data management
        </p>
      </form>
    </div>
  );
}
