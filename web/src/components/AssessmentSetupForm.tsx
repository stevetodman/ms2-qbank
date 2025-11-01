import { FormEvent, useMemo, useState } from 'react';
import type { AssessmentBlueprint } from '../api/assessments.ts';

interface AssessmentSetupFormProps {
  onSubmit: (blueprint: AssessmentBlueprint) => Promise<void> | void;
  busy?: boolean;
}

const DEFAULT_TIME_LIMIT = 280;

function normaliseTags(raw: string): string[] {
  return raw
    .split(',')
    .map((tag) => tag.trim())
    .filter((tag) => tag.length > 0);
}

export function AssessmentSetupForm({ onSubmit, busy = false }: AssessmentSetupFormProps) {
  const [candidateId, setCandidateId] = useState('');
  const [subject, setSubject] = useState('');
  const [system, setSystem] = useState('');
  const [difficulty, setDifficulty] = useState('');
  const [tags, setTags] = useState('');
  const [timeLimit, setTimeLimit] = useState(DEFAULT_TIME_LIMIT);

  const submitDisabled = useMemo(() => candidateId.trim().length === 0 || busy, [candidateId, busy]);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const blueprint: AssessmentBlueprint = {
      candidateId: candidateId.trim(),
      subject: subject.trim() || null,
      system: system.trim() || null,
      difficulty: difficulty.trim() || null,
      tags: normaliseTags(tags),
      timeLimitMinutes: Number.isNaN(timeLimit) ? DEFAULT_TIME_LIMIT : timeLimit,
    };
    await onSubmit(blueprint);
  };

  return (
    <form onSubmit={handleSubmit} aria-label="Assessment setup form">
      <fieldset disabled={busy}>
        <legend>Start a self-assessment</legend>
        <label>
          Candidate identifier
          <input
            type="text"
            value={candidateId}
            onChange={(event) => setCandidateId(event.target.value)}
            required
          />
        </label>
        <label>
          Subject focus (optional)
          <input type="text" value={subject} onChange={(event) => setSubject(event.target.value)} />
        </label>
        <label>
          System focus (optional)
          <input type="text" value={system} onChange={(event) => setSystem(event.target.value)} />
        </label>
        <label>
          Difficulty target (optional)
          <input type="text" value={difficulty} onChange={(event) => setDifficulty(event.target.value)} />
        </label>
        <label>
          Tags (comma separated)
          <input type="text" value={tags} onChange={(event) => setTags(event.target.value)} />
        </label>
        <label>
          Time limit (minutes)
          <input
            type="number"
            min={30}
            max={600}
            value={timeLimit}
            onChange={(event) => setTimeLimit(Number(event.target.value))}
          />
        </label>
        <button type="submit" disabled={submitDisabled}>
          {busy ? 'Preparing assessment…' : 'Begin assessment'}
        </button>
      </fieldset>
    </form>
  );
}
