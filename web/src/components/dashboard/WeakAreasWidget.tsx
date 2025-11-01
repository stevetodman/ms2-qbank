import { DashboardWidget } from './DashboardWidget.tsx';

export interface DashboardWeakArea {
  id: string;
  title: string;
  description: string;
  mastery: number;
  recommendation: string;
}

interface WeakAreasWidgetProps {
  areas: DashboardWeakArea[];
}

export const WeakAreasWidget = ({ areas }: WeakAreasWidgetProps) => {
  return (
    <DashboardWidget
      title="Weak areas to revisit"
      description="Target the topics where recent accuracy slipped below goal."
    >
      <ul className="dashboard-weak-areas">
        {areas.map((area) => (
          <li key={area.id} className="dashboard-weak-areas__item">
            <div className="dashboard-weak-areas__header">
              <h3>{area.title}</h3>
              <span className="dashboard-weak-areas__score">{area.mastery}% mastery</span>
            </div>
            <p className="dashboard-weak-areas__description">{area.description}</p>
            <div className="dashboard-progress-bar" role="img" aria-label={`${area.mastery}% mastery`}>
              <span style={{ width: `${Math.min(100, Math.max(0, area.mastery))}%` }} />
            </div>
            <p className="dashboard-weak-areas__recommendation">{area.recommendation}</p>
          </li>
        ))}
      </ul>
    </DashboardWidget>
  );
};
