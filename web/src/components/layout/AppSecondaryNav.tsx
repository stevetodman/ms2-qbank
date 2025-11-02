import clsx from 'clsx';
import { NavLink } from 'react-router-dom';
import type { NavigationItem } from './AppHeader';

interface AppSecondaryNavProps {
  navItems: NavigationItem[];
  collapsed: boolean;
  onToggle: () => void;
}

export const AppSecondaryNav = ({ navItems, collapsed, onToggle }: AppSecondaryNavProps) => {
  return (
    <aside
      className={clsx('app-secondary-nav', collapsed && 'app-secondary-nav--collapsed')}
      aria-label="Secondary navigation"
    >
      <button
        type="button"
        className="app-secondary-nav__toggle"
        onClick={onToggle}
        aria-expanded={!collapsed}
        aria-controls="app-secondary-nav-list"
      >
        <span aria-hidden="true">{collapsed ? '▶' : '◀'}</span>
        <span className={collapsed ? 'visually-hidden' : undefined}>
          {collapsed ? 'Expand navigation' : 'Collapse navigation'}
        </span>
      </button>
      <ul className="app-secondary-nav__list" id="app-secondary-nav-list">
        {navItems.map((item) => {
          const abbreviation = item.label
            .split(/\s+/)
            .map((word) => word.charAt(0))
            .join('')
            .slice(0, 3)
            .toUpperCase();

          return (
            <li key={item.path}>
              <NavLink
                to={item.path}
                end
                className="app-secondary-nav__link"
                aria-label={item.label}
              >
                <span
                  className={clsx(
                    'app-secondary-nav__abbr',
                    !collapsed && 'visually-hidden'
                  )}
                  aria-hidden="true"
                >
                  {abbreviation}
                </span>
                <span
                  className={clsx(
                    'app-secondary-nav__label',
                    collapsed && 'visually-hidden'
                  )}
                >
                  {item.label}
                </span>
              </NavLink>
            </li>
          );
        })}
      </ul>
    </aside>
  );
};
