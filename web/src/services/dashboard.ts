import { fetchLatestAnalytics, type AnalyticsSnapshot } from '../api/analytics.ts';
import { fetchStudyPlans, type StudyPlan } from '../api/planner.ts';
import { LAST_SUMMARY_STORAGE_KEY, type PracticeSummary } from '../types/practice.ts';
import type { DashboardAnnouncement } from '../components/dashboard/AnnouncementsWidget.tsx';
import type { DashboardMetric } from '../components/dashboard/MetricCardsWidget.tsx';
import type { DashboardProgressPoint } from '../components/dashboard/ProgressWidget.tsx';
import type { DashboardTask } from '../components/dashboard/TaskListWidget.tsx';
import type { DashboardQuickAction } from '../components/dashboard/QuickActionsWidget.tsx';
import type { DashboardWeakArea } from '../components/dashboard/WeakAreasWidget.tsx';

export interface DashboardSnapshot {
  tasks: DashboardTask[];
  metrics: DashboardMetric[];
  progress: DashboardProgressPoint[];
  quickActions: Omit<DashboardQuickAction, 'onClick'>[];
  weakAreas: DashboardWeakArea[];
  announcements: Omit<DashboardAnnouncement, 'onAction'>[];
  analyticsGeneratedLabel?: string;
  analyticsIsFresh?: boolean;
  plannerExamDateLabel?: string;
}

export interface DashboardLoadErrors {
  analytics?: string;
  planner?: string;
}

export interface DashboardDataResult {
  snapshot: DashboardSnapshot;
  errors: DashboardLoadErrors;
}

const formatDate = (input: string | number | Date) => {
  if (!input) {
    return '';
  }

  const date = typeof input === 'string' || typeof input === 'number' ? new Date(input) : input;
  if (Number.isNaN(date.getTime())) {
    return '';
  }

  return date.toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
  });
};

const readPracticeSummary = (): PracticeSummary | null => {
  if (typeof window === 'undefined') {
    return null;
  }

  try {
    const raw = window.localStorage?.getItem(LAST_SUMMARY_STORAGE_KEY);
    if (!raw) {
      return null;
    }

    const parsed = JSON.parse(raw) as PracticeSummary;
    if (!parsed || typeof parsed !== 'object') {
      return null;
    }

    return parsed;
  } catch (error) {
    console.warn('Unable to parse practice summary', error);
    return null;
  }
};

const buildTasks = (plan: StudyPlan | null): DashboardTask[] => {
  if (!plan) {
    return [
      {
        id: 'mock-task-plan',
        title: 'Assign a new practice block',
        detail: 'Use the planner to add 20-question blocks aligned with your exam date.',
        dueLabel: 'Today',
        status: 'pending',
      },
    ];
  }

  return plan.tasks.slice(0, 4).map((task, index) => ({
    id: `${plan.planId}-${index}`,
    title: `${task.subject} review`,
    detail: `Focus for ${task.hours.toFixed(1)} hours based on your schedule.`,
    dueLabel: formatDate(task.date),
    status: task.hours >= plan.dailyStudyHours ? 'in-progress' : 'pending',
    durationLabel: `${task.hours.toFixed(1)} hrs`,
    actionLabel: 'Open block',
  }));
};

const buildMetrics = (
  analytics: AnalyticsSnapshot | null,
  summary: PracticeSummary | null,
  plan: StudyPlan | null
): DashboardMetric[] => {
  const totalQuestions = analytics?.metrics.totalQuestions ?? 0;
  const trackedQuestions = analytics?.metrics.usageSummary.trackedQuestions ?? 0;
  const deliveries = analytics?.metrics.usageSummary.totalUsage ?? 0;

  const accuracy = summary
    ? Math.round((summary.correctCount / Math.max(summary.totalQuestions, 1)) * 100)
    : 68;
  const averageTime = summary ? `${summary.averageTimeSeconds}s avg/question` : '58s avg/question';
  const studyHours = plan ? `${plan.dailyStudyHours.toFixed(1)} hrs / day` : '3.0 hrs / day';

  return [
    {
      id: 'accuracy',
      label: 'Overall accuracy',
      value: `${accuracy}%`,
      helperText: summary
        ? `${summary.correctCount} of ${summary.totalQuestions} questions correct`
        : 'Based on recent tutor mode blocks',
      delta: { direction: accuracy >= 65 ? 'up' : 'down', value: accuracy >= 65 ? '+3%' : '-4%', caption: 'vs last week' },
    },
    {
      id: 'questions',
      label: 'Questions tracked',
      value: totalQuestions > 0 ? totalQuestions.toString() : '—',
      helperText: `${trackedQuestions} in review pipeline`,
      delta: {
        direction: deliveries > 0 ? 'up' : 'steady',
        value: deliveries > 0 ? `+${deliveries}` : 'No change',
        caption: 'deliveries this week',
      },
    },
    {
      id: 'study-hours',
      label: 'Planned study load',
      value: studyHours,
      helperText: plan?.examDate ? `Exam on ${formatDate(plan.examDate)}` : 'Set your exam date to tune workload',
      delta: { direction: 'steady', value: averageTime, caption: 'recent pace' },
    },
  ];
};

const buildProgress = (summary: PracticeSummary | null): DashboardProgressPoint[] => {
  const base: DashboardProgressPoint[] = [
    { id: 'mon', label: 'Mon', correct: 14, total: 20, target: 75 },
    { id: 'tue', label: 'Tue', correct: 16, total: 22, target: 75 },
    { id: 'wed', label: 'Wed', correct: 12, total: 20, target: 75 },
    { id: 'thu', label: 'Thu', correct: 18, total: 24, target: 75 },
    { id: 'fri', label: 'Fri', correct: 20, total: 25, target: 75 },
  ];

  if (summary) {
    const latest: DashboardProgressPoint = {
      id: 'latest',
      label: 'Latest block',
      correct: summary.correctCount,
      total: summary.totalQuestions,
      target: 75,
    };
    return [...base.slice(1), latest];
  }

  return base;
};

const buildWeakAreas = (
  analytics: AnalyticsSnapshot | null,
  summary: PracticeSummary | null
): DashboardWeakArea[] => {
  const subject = summary?.filters.subject;
  const focusSubject = subject && subject.trim().length > 0 ? subject : 'Biostatistics & Study Design';
  const difficultyEntries = Object.entries(analytics?.metrics.difficultyDistribution ?? {});
  const topDifficulty = difficultyEntries.sort((a, b) => b[1] - a[1])[0]?.[0] ?? 'Hard';

  return [
    {
      id: 'weak-area-1',
      title: focusSubject,
      description: `Recent sessions flagged ${focusSubject.toLowerCase()} as below goal accuracy.`,
      mastery: 54,
      recommendation: 'Revisit related flashcards and schedule a 15-question targeted block.',
    },
    {
      id: 'weak-area-2',
      title: `${topDifficulty} difficulty remediation`,
      description: `Accuracy on ${topDifficulty.toLowerCase()} items trailed other levels last week.`,
      mastery: 61,
      recommendation: 'Switch to tutor mode for explanations and bookmark tricky stems for review.',
    },
    {
      id: 'weak-area-3',
      title: 'Endocrine pathology differentials',
      description: 'Students with similar profiles spent extra time on hormone pathway questions.',
      mastery: 67,
      recommendation: 'Skim the endocrine rapid review article before your next timed block.',
    },
  ];
};

const buildAnnouncements = (): Omit<DashboardAnnouncement, 'onAction'>[] => [
  {
    id: 'announcement-1',
    title: 'New cardiology visuals available',
    message: 'We refreshed high-yield ECG diagrams and added tutor notes for recent NBME trends.',
    dateLabel: formatDate(new Date()),
    actionLabel: 'View library update',
  },
  {
    id: 'announcement-2',
    title: 'Scheduled maintenance',
    message: 'Practice sessions and analytics will be read-only on Saturday 06:00–08:00 ET.',
    dateLabel: formatDate(new Date(Date.now() + 2 * 24 * 60 * 60 * 1000)),
  },
];

const buildQuickActions = (): Omit<DashboardQuickAction, 'onClick'>[] => [
  {
    id: 'action-planner',
    label: 'Adjust study planner',
    description: 'Rebalance hours and targets',
  },
  {
    id: 'action-qbank',
    label: 'Launch QBank session',
    description: 'Timed or tutor delivery modes',
  },
  {
    id: 'action-flashcards',
    label: 'Review flashcards',
    description: 'Strengthen weak areas quickly',
  },
  {
    id: 'action-notebook',
    label: 'Capture notebook entry',
    description: 'Log follow-ups from practice',
  },
];

export const loadDashboardData = async (): Promise<DashboardDataResult> => {
  const errors: DashboardLoadErrors = {};
  let analytics: AnalyticsSnapshot | null = null;
  let plan: StudyPlan | null = null;

  try {
    analytics = await fetchLatestAnalytics();
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unable to load analytics';
    errors.analytics = message;
  }

  try {
    const plans = await fetchStudyPlans();
    plan = plans[0] ?? null;
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unable to load study planner';
    errors.planner = message;
  }

  const summary = readPracticeSummary();
  const tasks = buildTasks(plan);
  const metrics = buildMetrics(analytics, summary, plan);
  const progress = buildProgress(summary);
  const weakAreas = buildWeakAreas(analytics, summary);
  const announcements = buildAnnouncements();
  const quickActions = buildQuickActions();

  const analyticsGeneratedLabel = analytics?.generatedAt
    ? new Date(analytics.generatedAt).toLocaleString()
    : undefined;

  const snapshot: DashboardSnapshot = {
    tasks,
    metrics,
    progress,
    weakAreas,
    announcements,
    quickActions,
    analyticsGeneratedLabel,
    analyticsIsFresh: analytics?.isFresh,
    plannerExamDateLabel: plan?.examDate ? formatDate(plan.examDate) : undefined,
  };

  return { snapshot, errors };
};
