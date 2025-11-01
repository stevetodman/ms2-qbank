import { useCallback } from 'react';
import type { AssessmentSubmissionResponse } from '../api/assessments.ts';
import { fetchLatestAnalytics, type AnalyticsSnapshot } from '../api/analytics.ts';

interface UseAssessmentAnalyticsOptions {
  onSnapshot?: (snapshot: AnalyticsSnapshot) => void;
}

export function useAssessmentAnalytics(options: UseAssessmentAnalyticsOptions = {}) {
  const { onSnapshot } = options;

  return useCallback(
    async (submission: AssessmentSubmissionResponse) => {
      try {
        const snapshot = await fetchLatestAnalytics();
        onSnapshot?.(snapshot);
        return snapshot;
      } catch (err) {
        console.warn('Unable to refresh analytics after assessment completion', err, submission);
        return null;
      }
    },
    [onSnapshot]
  );
}
