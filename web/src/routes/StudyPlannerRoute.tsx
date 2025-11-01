import { useCallback, useEffect, useState } from 'react';
import { fetchStudyPlans, type StudyPlan } from '../api/planner.ts';
import { StudyPlannerWidget } from '../components/StudyPlannerWidget.tsx';

export const StudyPlannerRoute = () => {
  const [plan, setPlan] = useState<StudyPlan | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadPlan = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const plans = await fetchStudyPlans();
      setPlan(plans[0] ?? null);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Unable to load study plans';
      setError(message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadPlan();
  }, [loadPlan]);

  return (
    <div className="stack" data-page="study-planner">
      <section className="card stack">
        <header className="stack">
          <h1>Study Planner</h1>
          <p>
            Design focused study blocks, align them with your exam calendar, and keep momentum by
            logging daily wins. Plans stay in sync with your practice and assessment activity so you
            always know what deserves attention next.
          </p>
        </header>
        <p>
          Refresh your planner after generating new practice blocks or completing assessments to see
          how your roadmap evolves.
        </p>
      </section>
      <StudyPlannerWidget plan={plan} loading={loading} error={error} onRefresh={loadPlan} />
    </div>
  );
};
