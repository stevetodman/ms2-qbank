import type { PropsWithChildren, ReactNode } from 'react';
import clsx from 'clsx';
import '../../styles/dashboard.css';

interface DashboardWidgetProps extends PropsWithChildren {
  title: string;
  description?: string;
  actions?: ReactNode;
  footer?: ReactNode;
  className?: string;
}

export const DashboardWidget = ({
  title,
  description,
  actions,
  footer,
  className,
  children,
}: DashboardWidgetProps) => {
  return (
    <section className={clsx('dashboard-widget card stack', className)}>
      <header className="dashboard-widget__header">
        <div className="dashboard-widget__heading">
          <h2>{title}</h2>
          {description && <p className="dashboard-widget__description">{description}</p>}
        </div>
        {actions && <div className="dashboard-widget__actions">{actions}</div>}
      </header>
      <div className="dashboard-widget__body">{children}</div>
      {footer && <footer className="dashboard-widget__footer">{footer}</footer>}
    </section>
  );
};
