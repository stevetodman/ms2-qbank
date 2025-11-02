import { DashboardWidget } from './DashboardWidget';

export interface DashboardMetricDelta {
  direction: 'up' | 'down' | 'steady';
  value: string;
  caption?: string;
}

export interface DashboardMetric {
  id: string;
  label: string;
  value: string;
  helperText?: string;
  delta?: DashboardMetricDelta;
}

interface MetricCardsWidgetProps {
  metrics: DashboardMetric[];
  loading?: boolean;
  error?: string | null;
  generatedLabel?: string;
  isFresh?: boolean;
  onRefresh?: () => void;
}

const deltaSymbols: Record<DashboardMetricDelta['direction'], string> = {
  up: '▲',
  down: '▼',
  steady: '■',
};

export const MetricCardsWidget = ({
  metrics,
  loading = false,
  error,
  generatedLabel,
  isFresh,
  onRefresh,
}: MetricCardsWidgetProps) => {
  return (
    <DashboardWidget
      title="Performance snapshot"
      description="High-level metrics pulled from the latest analytics run."
      actions={
        <button type="button" className="secondary-button" onClick={onRefresh} disabled={loading}>
          {loading ? 'Refreshing…' : 'Refresh analytics'}
        </button>
      }
      footer={
        generatedLabel ? (
          <p className="dashboard-widget__meta">
            Snapshot updated {generatedLabel} • {isFresh ? 'Fresh' : 'Stale'} data
          </p>
        ) : null
      }
    >
      {loading && <p>Loading analytics…</p>}
      {error && !loading && (
        <p role="alert" className="error">
          {error}
        </p>
      )}
      {!loading && !error && (
        <div className="dashboard-metrics">
          {metrics.map((metric) => (
            <article key={metric.id} className="dashboard-metrics__card">
              <h3>{metric.label}</h3>
              <p className="dashboard-metrics__value">{metric.value}</p>
              {metric.helperText && <p className="dashboard-metrics__helper">{metric.helperText}</p>}
              {metric.delta && (
                <p className="dashboard-metrics__delta" aria-label={`Change ${metric.delta.value}`}>
                  <span className={`dashboard-metrics__delta-indicator dashboard-metrics__delta-indicator--${metric.delta.direction}`}>
                    {deltaSymbols[metric.delta.direction]}
                  </span>
                  {metric.delta.value}
                  {metric.delta.caption && <span className="dashboard-metrics__delta-caption">{metric.delta.caption}</span>}
                </p>
              )}
            </article>
          ))}
        </div>
      )}
    </DashboardWidget>
  );
};
