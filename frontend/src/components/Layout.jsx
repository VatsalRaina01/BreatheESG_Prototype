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
    { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
    { to: '/upload', icon: Upload, label: 'Upload' },
    { to: '/review', icon: ClipboardList, label: 'Review' },
    { to: '/jobs', icon: FolderOpen, label: 'Jobs' },
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
              <item.icon size={20} />
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
            style={{ marginLeft: 'auto' }}
          >
            <LogOut size={18} />
          </button>
        </div>
      </aside>

      {/* Top Bar */}
      <div className="topbar">
        <h1 className="topbar-title">{title}</h1>
        <div className="topbar-actions" />
      </div>

      {/* Main Content */}
      <main className="main-content page-enter">
        {children}
      </main>
    </div>
  );
}
