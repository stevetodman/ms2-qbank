import type { PropsWithChildren, ReactNode } from 'react';
import clsx from 'clsx';

interface ResponsiveGridProps extends PropsWithChildren {
  sidebar: ReactNode;
  collapsed?: boolean;
}

export const ResponsiveGrid = ({ sidebar, collapsed = false, children }: ResponsiveGridProps) => {
  return (
    <div className={clsx('app-layout-grid', collapsed && 'app-layout-grid--collapsed')}>
      {sidebar}
      {children}
    </div>
  );
};
