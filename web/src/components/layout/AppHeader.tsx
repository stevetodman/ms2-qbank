import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';

export type NavigationItem = {
  label: string;
  path: string;
};

interface AppHeaderProps {
  navItems: NavigationItem[];
}

export const AppHeader = ({ navItems }: AppHeaderProps) => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  return (
    <header className="app-header" role="banner">
      <div className="app-header__inner">
        <NavLink to="/dashboard" className="app-header__brand">
          MS2 QBank
        </NavLink>
        <nav aria-label="Primary">
          <div className="app-top-nav">
            {navItems.map((item) => (
              <NavLink key={item.path} to={item.path} end>
                {item.label}
              </NavLink>
            ))}
          </div>
        </nav>
        {user && (
          <div className="app-header__user">
            <span className="user-name">{user.full_name}</span>
            <button type="button" onClick={handleLogout} className="logout-button">
              Logout
            </button>
          </div>
        )}
      </div>
    </header>
  );
};
