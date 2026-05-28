import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { LayoutDashboard, Upload, ClipboardList, FolderOpen, LogOut, Leaf } from 'lucide-react';

export default function Layout({ children, title }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const navItems = [
    { to: '/dashboard', icon: LayoutDashboard, label: 'Overview' },
    { to: '/upload', icon: Upload, label: 'Ingest Data' },
    { to: '/review', icon: ClipboardList, label: 'Review Flags' },
    { to: '/jobs', icon: FolderOpen, label: 'Job History' },
  ];

  const initials = user?.email
    ? user.email.split('@')[0].slice(0, 2).toUpperCase()
    : 'U';

  return (
    <div className="app-layout">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-logo">
          <div className="sidebar-logo-icon">
            <Leaf size={20} />
          </div>
          <span className="sidebar-logo-text">Breathe ESG</span>
        </div>

        <nav className="sidebar-nav">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `sidebar-nav-item ${isActive ? 'active' : ''}`
              }
            >
              <item.icon size={18} />
              <span>{item.label}</span>
            </NavLink>
          ))}
        </nav>

        <div className="sidebar-user">
          <div className="sidebar-user-avatar">{initials}</div>
          <div className="sidebar-user-info">
            <div className="sidebar-user-name">
              {user?.email?.split('@')[0] || 'User'}
            </div>
            <div className="sidebar-user-role">{user?.role || 'Analyst'}</div>
          </div>
          <button
            className="btn-ghost"
            onClick={handleLogout}
            title="Logout"
            style={{ marginLeft: 'auto', color: '#A8C4A2' }}
          >
            <LogOut size={16} />
          </button>
        </div>
      </aside>

      {/* Main Content — no top bar */}
      <main className="main-content page-enter">
        <div className="page-header">
          <h1 className="page-title">{title}</h1>
        </div>
        {children}
      </main>
    </div>
  );
}
