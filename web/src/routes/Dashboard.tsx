import { useCallback, useEffect, useMemo, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import type { DashboardAnnouncement } from '../components/dashboard/AnnouncementsWidget';
import { AnnouncementsWidget } from '../components/dashboard/AnnouncementsWidget';
import type { DashboardQuickAction } from '../components/dashboard/QuickActionsWidget';
import { QuickActionsWidget } from '../components/dashboard/QuickActionsWidget';
import { MetricCardsWidget } from '../components/dashboard/MetricCardsWidget';
import { ProgressWidget } from '../components/dashboard/ProgressWidget';
import { TaskListWidget } from '../components/dashboard/TaskListWidget';
import { WeakAreasWidget } from '../components/dashboard/WeakAreasWidget';
import { loadDashboardData, type DashboardDataResult } from '../services/dashboard';
import type { DashboardTask } from '../components/dashboard/TaskListWidget';
import '../styles/dashboard.css';

export const DashboardRoute = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [data, setData] = useState<DashboardDataResult | null>(null);

  const handleLoad = useCallback(async () => {
    setRefreshing(true);
    try {
      const result = await loadDashboardData();
      setData(result);
    } finally {
      setRefreshing(false);
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void handleLoad();
  }, [handleLoad]);

  const quickActions = useMemo<DashboardQuickAction[]>(() => {
    if (!data?.snapshot.quickActions) {
      return [];
    }

    return data.snapshot.quickActions.map((action) => {
      const handleNavigation = () => {
        switch (action.id) {
          case 'action-planner':
            navigate('/study-planner');
            break;
          case 'action-qbank':
            navigate('/qbank');
            break;
          case 'action-flashcards':
            navigate('/flashcards');
            break;
          case 'action-notebook':
            navigate('/notebook');
            break;
          default:
            navigate('/dashboard');
        }
      };

      return { ...action, onClick: handleNavigation };
    });
  }, [data?.snapshot.quickActions, navigate]);

  const announcements = useMemo<DashboardAnnouncement[]>(() => {
    if (!data?.snapshot.announcements) {
      return [];
    }

    return data.snapshot.announcements.map((announcement) => ({
      ...announcement,
      onAction:
        announcement.actionLabel === 'View library update'
          ? () => navigate('/library')
          : undefined,
    }));
  }, [data?.snapshot.announcements, navigate]);

  const tasks = useMemo<DashboardTask[]>(() => {
    if (!data?.snapshot.tasks) {
      return [];
    }

    return data.snapshot.tasks.map((task) => ({
      ...task,
      onAction: task.actionLabel ? () => navigate('/study-planner') : undefined,
    }));
  }, [data?.snapshot.tasks, navigate]);

  return (
    <div className="dashboard-page">
      <section className="dashboard-hero">
        <div>
          <h1>MS2 QBank Learner Experience</h1>
          <p>
            Build focused practice sessions, take questions in timed or tutor mode, and log review
            actions without leaving the browser. This dashboard surfaces the tasks, metrics, and
            guidance you need to stay on track with your study plan.
          </p>
        </div>
        <div className="dashboard-hero__actions">
          <button
            type="button"
            className="primary-button"
            onClick={() => navigate('/qbank')}
          >
            Launch practice workspace
          </button>
          <Link className="secondary-button" to="/library">
            Explore medical library
          </Link>
          <Link className="secondary-button" to="/study-planner">
            Open study planner
          </Link>
        </div>
      </section>

      {loading && <p>Loading dashboard data…</p>}

      {!loading && data && (
        <div className="dashboard-grid">
          <div className="dashboard-grid__column">
            <TaskListWidget
              tasks={tasks}
              loading={refreshing && !data.snapshot.tasks.length}
              error={data.errors.planner ? `Planner unavailable: ${data.errors.planner}` : undefined}
              onViewPlanner={() => navigate('/study-planner')}
            />

            <ProgressWidget points={data.snapshot.progress} />

            <AnnouncementsWidget announcements={announcements} />
          </div>

          <div className="dashboard-grid__column">
            <MetricCardsWidget
              metrics={data.snapshot.metrics}
              loading={refreshing}
              error={data.errors.analytics ? `Analytics unavailable: ${data.errors.analytics}` : undefined}
              generatedLabel={data.snapshot.analyticsGeneratedLabel}
              isFresh={data.snapshot.analyticsIsFresh}
              onRefresh={() => {
                void handleLoad();
              }}
            />

            <QuickActionsWidget actions={quickActions} />

            <WeakAreasWidget areas={data.snapshot.weakAreas} />
          </div>
        </div>
      )}
    </div>
  );
};
