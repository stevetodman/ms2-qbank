import { useEffect, useRef, useState } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import { AppFrame } from './AppFrame';
import { AppHeader, type NavigationItem } from './AppHeader';
import { AppSecondaryNav } from './AppSecondaryNav';
import { ResponsiveGrid } from './ResponsiveGrid';
import '../../styles/layout.css';

const navigationItems: NavigationItem[] = [
  { label: 'Dashboard', path: '/dashboard' },
  { label: 'QBank', path: '/qbank' },
  { label: 'Self-Assessment', path: '/self-assessment' },
  { label: 'Flashcards', path: '/flashcards' },
  { label: 'Library', path: '/library' },
  { label: 'Study Planner', path: '/study-planner' },
  { label: 'Notebook', path: '/notebook' },
  { label: 'Performance', path: '/performance' },
  { label: 'Videos', path: '/videos' },
  { label: 'Help', path: '/help' },
  { label: 'Account', path: '/account' },
];

export const AppLayout = () => {
  const location = useLocation();
  const [collapsed, setCollapsed] = useState(false);
  const mainRef = useRef<HTMLElement>(null);

  useEffect(() => {
    mainRef.current?.focus();
  }, [location.pathname]);

  return (
    <AppFrame>
      <a href="#main-content" className="skip-link">
        Skip to main content
      </a>
      <AppHeader navItems={navigationItems} />
      <ResponsiveGrid
        sidebar={
          <AppSecondaryNav
            navItems={navigationItems}
            collapsed={collapsed}
            onToggle={() => setCollapsed((value) => !value)}
          />
        }
        collapsed={collapsed}
      >
        <main
          id="main-content"
          className="app-main"
          ref={mainRef}
          tabIndex={-1}
          role="main"
          aria-live="polite"
        >
          <Outlet />
        </main>
      </ResponsiveGrid>
    </AppFrame>
  );
};
