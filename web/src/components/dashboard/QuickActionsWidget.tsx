import { DashboardWidget } from './DashboardWidget';

export interface DashboardQuickAction {
  id: string;
  label: string;
  description?: string;
  onClick: () => void;
}

interface QuickActionsWidgetProps {
  actions: DashboardQuickAction[];
}

export const QuickActionsWidget = ({ actions }: QuickActionsWidgetProps) => {
  return (
    <DashboardWidget
      title="Quick actions"
      description="Jump back into the tools you use most frequently."
    >
      <div className="dashboard-quick-actions">
        {actions.map((action) => (
          <button key={action.id} type="button" className="dashboard-quick-actions__button" onClick={action.onClick}>
            <span className="dashboard-quick-actions__label">{action.label}</span>
            {action.description && <span className="dashboard-quick-actions__description">{action.description}</span>}
          </button>
        ))}
      </div>
    </DashboardWidget>
  );
};
