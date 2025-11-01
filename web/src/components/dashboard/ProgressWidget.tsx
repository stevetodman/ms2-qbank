import { DashboardWidget } from './DashboardWidget.tsx';

export interface DashboardProgressPoint {
  id: string;
  label: string;
  correct: number;
  total: number;
  target?: number;
}

interface ProgressWidgetProps {
  points: DashboardProgressPoint[];
}

const toPercent = (value: number, total: number) => {
  if (total <= 0) {
    return 0;
  }
  return Math.round((value / total) * 100);
};

export const ProgressWidget = ({ points }: ProgressWidgetProps) => {
  return (
    <DashboardWidget
      title="Progress over time"
      description="Track accuracy across recent practice blocks."
    >
      <div className="dashboard-progress">
        {points.map((point) => {
          const percent = toPercent(point.correct, point.total);
          return (
            <div key={point.id} className="dashboard-progress__row">
              <div className="dashboard-progress__label">
                <span>{point.label}</span>
                <span className="dashboard-progress__percent">{percent}%</span>
              </div>
              <div className="dashboard-progress__chart" role="img" aria-label={`${percent}% correct out of ${point.total} questions`}>
                <span style={{ width: `${percent}%` }} />
                {point.target !== undefined && (
                  <span
                    className="dashboard-progress__target"
                    style={{ left: `${Math.min(100, Math.max(0, point.target))}%` }}
                    aria-hidden
                  />
                )}
              </div>
              <p className="dashboard-progress__meta">
                {point.correct} / {point.total} correct
              </p>
            </div>
          );
        })}
      </div>
    </DashboardWidget>
  );
};
