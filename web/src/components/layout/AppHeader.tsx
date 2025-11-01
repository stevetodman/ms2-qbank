import { NavLink } from 'react-router-dom';

export type NavigationItem = {
  label: string;
  path: string;
};

interface AppHeaderProps {
  navItems: NavigationItem[];
}

export const AppHeader = ({ navItems }: AppHeaderProps) => {
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
      </div>
    </header>
  );
};
