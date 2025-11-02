import { resolveEnv } from '../utils/env';

const PLANNER_API_BASE_URL = resolveEnv('VITE_PLANNER_API_BASE_URL', '/api/planner');

interface RawStudyPlanTask {
  date?: string;
  subject?: string;
  hours?: number;
}

interface RawStudyPlanSubjectBreakdown {
  subject?: string;
  allocated_hours?: number;
  percentage?: number;
}

interface RawStudyPlan {
  plan_id?: string;
  created_at?: string;
  start_date?: string;
  exam_date?: string;
  days?: number;
  daily_study_hours?: number;
  total_study_hours?: number;
  tasks?: RawStudyPlanTask[];
  subject_breakdown?: RawStudyPlanSubjectBreakdown[];
}

export interface StudyPlanTask {
  date: string;
  subject: string;
  hours: number;
}

export interface StudyPlanSubjectBreakdown {
  subject: string;
  allocatedHours: number;
  percentage: number;
}

export interface StudyPlan {
  planId: string;
  createdAt: string;
  startDate: string;
  examDate: string;
  days: number;
  dailyStudyHours: number;
  totalStudyHours: number;
  tasks: StudyPlanTask[];
  subjectBreakdown: StudyPlanSubjectBreakdown[];
}

function normaliseTasks(rawTasks: RawStudyPlanTask[] | undefined): StudyPlanTask[] {
  if (!Array.isArray(rawTasks)) {
    return [];
  }
  return rawTasks
    .filter((task): task is RawStudyPlanTask => task !== null && typeof task === 'object')
    .map((task) => ({
      date: typeof task.date === 'string' ? task.date : '',
      subject: typeof task.subject === 'string' ? task.subject : 'Untitled',
      hours: typeof task.hours === 'number' ? task.hours : 0,
    }))
    .filter((task) => task.date && task.subject)
    .sort((a, b) => a.date.localeCompare(b.date));
}

function normaliseSubjectBreakdown(
  raw: RawStudyPlanSubjectBreakdown[] | undefined
): StudyPlanSubjectBreakdown[] {
  if (!Array.isArray(raw)) {
    return [];
  }
  return raw
    .filter((item): item is RawStudyPlanSubjectBreakdown => item !== null && typeof item === 'object')
    .map((item) => ({
      subject: typeof item.subject === 'string' ? item.subject : 'Unknown',
      allocatedHours:
        typeof item.allocated_hours === 'number' ? item.allocated_hours : 0,
      percentage: typeof item.percentage === 'number' ? item.percentage : 0,
    }))
    .sort((a, b) => b.allocatedHours - a.allocatedHours);
}

function normalisePlan(raw: RawStudyPlan): StudyPlan {
  return {
    planId: typeof raw.plan_id === 'string' ? raw.plan_id : '',
    createdAt: typeof raw.created_at === 'string' ? raw.created_at : '',
    startDate: typeof raw.start_date === 'string' ? raw.start_date : '',
    examDate: typeof raw.exam_date === 'string' ? raw.exam_date : '',
    days: typeof raw.days === 'number' ? raw.days : 0,
    dailyStudyHours:
      typeof raw.daily_study_hours === 'number' ? raw.daily_study_hours : 0,
    totalStudyHours:
      typeof raw.total_study_hours === 'number' ? raw.total_study_hours : 0,
    tasks: normaliseTasks(raw.tasks),
    subjectBreakdown: normaliseSubjectBreakdown(raw.subject_breakdown),
  };
}

function assertPlan(plan: StudyPlan): StudyPlan {
  if (!plan.planId) {
    throw new Error('Planner API returned a plan without an identifier');
  }
  return plan;
}

export async function fetchStudyPlans(): Promise<StudyPlan[]> {
  const response = await fetch(`${PLANNER_API_BASE_URL}/plans`, {
    headers: {
      Accept: 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error(`Planner request failed with status ${response.status}`);
  }

  const json = (await response.json()) as RawStudyPlan[];
  return json.map(normalisePlan).map(assertPlan);
}

export async function fetchStudyPlan(planId: string): Promise<StudyPlan> {
  const response = await fetch(`${PLANNER_API_BASE_URL}/plans/${planId}`, {
    headers: {
      Accept: 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error(`Planner request failed with status ${response.status}`);
  }

  const json = (await response.json()) as RawStudyPlan;
  return assertPlan(normalisePlan(json));
}

export interface CreateStudyPlanPayload {
  startDate?: string;
  examDate: string;
  dailyStudyHours: number;
  subjectPriorities: { subject: string; priority: number }[];
}

export async function createStudyPlan(payload: CreateStudyPlanPayload): Promise<StudyPlan> {
  const response = await fetch(`${PLANNER_API_BASE_URL}/plans`, {
    method: 'POST',
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      start_date: payload.startDate,
      exam_date: payload.examDate,
      daily_study_hours: payload.dailyStudyHours,
      subject_priorities: payload.subjectPriorities,
    }),
  });

  if (!response.ok) {
    throw new Error(`Planner request failed with status ${response.status}`);
  }

  const json = (await response.json()) as RawStudyPlan;
  return assertPlan(normalisePlan(json));
}
