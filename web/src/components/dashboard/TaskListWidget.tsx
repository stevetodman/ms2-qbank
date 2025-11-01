import type { ReactNode } from 'react';
import { DashboardWidget } from './DashboardWidget.tsx';

export interface DashboardTask {
  id: string;
  title: string;
  detail: string;
  dueLabel: string;
  status: 'pending' | 'in-progress' | 'completed';
  durationLabel?: string;
  actionLabel?: string;
  actionIcon?: ReactNode;
  onAction?: () => void;
}

interface TaskListWidgetProps {
  tasks: DashboardTask[];
  loading?: boolean;
  error?: string | null;
  onViewPlanner?: () => void;
}

const statusCopy: Record<DashboardTask['status'], string> = {
  pending: 'Not started',
  'in-progress': 'In progress',
  completed: 'Completed',
};

export const TaskListWidget = ({ tasks, loading = false, error, onViewPlanner }: TaskListWidgetProps) => {
  return (
    <DashboardWidget
      title="Today's study plan"
      description="Focus on the highest-impact items from your personalised planner."
      actions={
        <button type="button" className="secondary-button" onClick={onViewPlanner} disabled={loading}>
          View planner
        </button>
      }
      footer={
        !loading && !error && tasks.length === 0 ? (
          <p className="dashboard-widget__empty">You&apos;re all set for today. Add new blocks from the planner.</p>
        ) : null
      }
    >
      {loading && <p>Loading today&apos;s tasks…</p>}
      {error && !loading && (
        <p role="alert" className="error">
          {error}
        </p>
      )}
      {!loading && tasks.length > 0 && (
        <ol className="dashboard-task-list">
          {tasks.map((task) => (
            <li key={task.id} className="dashboard-task-list__item">
              <div className="dashboard-task-list__content">
                <div className="dashboard-task-list__title-group">
                  <span className="badge">{statusCopy[task.status]}</span>
                  <h3>{task.title}</h3>
                </div>
                <p className="dashboard-task-list__detail">{task.detail}</p>
                <p className="dashboard-task-list__meta">
                  <span>{task.dueLabel}</span>
                  {task.durationLabel && <span aria-label="Estimated time">• {task.durationLabel}</span>}
                </p>
              </div>
              {task.actionLabel && task.onAction && (
                <button
                  type="button"
                  className="dashboard-task-list__action"
                  onClick={task.onAction}
                >
                  {task.actionIcon}
                  {task.actionLabel}
                </button>
              )}
            </li>
          ))}
        </ol>
      )}
    </DashboardWidget>
  );
};
