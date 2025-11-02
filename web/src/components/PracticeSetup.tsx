import { FormEvent, useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { usePracticeSession } from '../context/PracticeSessionContext';
import type { PracticeFilters, PracticeMode } from '../types/practice';

const DEFAULT_FILTERS: PracticeFilters = {
  query: '',
  tags: [],
  subject: undefined,
  system: undefined,
  status: undefined,
  difficulty: undefined,
  questionCount: 20,
  randomizeOrder: true,
  timePerQuestionSeconds: 105,
  showExplanationOnSubmit: true,
};

const MODE_HELP: Record<PracticeMode, string> = {
  timed: 'Simulates exam pacing with a continuous timer and deferred explanations.',
  tutor: 'Shows explanations immediately after each answer to reinforce learning.',
  custom: 'Tune timers and reveal behaviour to match your personal study plan.',
};

export const PracticeSetup = () => {
  const navigate = useNavigate();
  const {
    filterOptions,
    filtersLoading,
    startSession,
    isLoading,
    error,
    preview,
    previewTotal,
    previewLoading,
    previewError,
    canLoadMorePreview,
    loadPreview,
    loadMorePreview,
  } = usePracticeSession();
  const [mode, setMode] = useState<PracticeMode>('tutor');
  const [filters, setFilters] = useState<PracticeFilters>(DEFAULT_FILTERS);
  const [selectedTags, setSelectedTags] = useState<string[]>([]);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const cleanedFilters: PracticeFilters = {
      ...filters,
      tags: selectedTags,
      query: filters.query?.trim() ? filters.query.trim() : undefined,
      subject: filters.subject || undefined,
      system: filters.system || undefined,
      status: filters.status || undefined,
      difficulty: filters.difficulty || undefined,
    };
    await startSession(mode, cleanedFilters);
    navigate('#workspace');
  };

  const modeDescription = useMemo(() => MODE_HELP[mode], [mode]);

  const previewFilters = useMemo<PracticeFilters>(
    () => ({
      ...filters,
      tags: selectedTags,
    }),
    [filters, selectedTags]
  );

  useEffect(() => {
    if (filtersLoading) {
      return;
    }
    const handle = window.setTimeout(() => {
      void loadPreview(previewFilters);
    }, 250);
    return () => window.clearTimeout(handle);
  }, [filtersLoading, loadPreview, previewFilters]);

  const toggleTag = (tag: string) => {
    setSelectedTags((current) => {
      if (current.includes(tag)) {
        return current.filter((item) => item !== tag);
      }
      return [...current, tag];
    });
  };

  const quickSelect = (count: number) => {
    setFilters((current) => ({ ...current, questionCount: count }));
  };

  const resetFilters = () => {
    setFilters({ ...DEFAULT_FILTERS });
    setSelectedTags([]);
  };

  const summariseStem = (stem: string) => {
    const trimmed = stem.trim();
    if (trimmed.length <= 160) {
      return trimmed;
    }
    return `${trimmed.slice(0, 157)}…`;
  };

  return (
    <form className="card stack" onSubmit={handleSubmit} aria-label="Practice configuration">
      <fieldset>
        <legend>Step 1 · Choose your delivery mode</legend>
        <div className="stack">
          {(['timed', 'tutor', 'custom'] as PracticeMode[]).map((value) => (
            <label key={value} style={{ fontWeight: 500 }}>
              <input
                type="radio"
                name="mode"
                value={value}
                checked={mode === value}
                onChange={() => setMode(value)}
              />{' '}
              <strong style={{ textTransform: 'capitalize' }}>{value}</strong>
              <br />
              <span style={{ fontWeight: 400, color: '#475569' }}>{MODE_HELP[value]}</span>
            </label>
          ))}
        </div>
        <p style={{ marginTop: '0.5rem', color: '#4338ca' }}>{modeDescription}</p>
        {mode === 'custom' && (
          <div className="stack" style={{ marginTop: '1rem' }}>
            <label htmlFor="timePerQuestion">Time per question (seconds)</label>
            <input
              id="timePerQuestion"
              type="number"
              min={30}
              max={600}
              value={filters.timePerQuestionSeconds ?? 105}
              onChange={(event) =>
                setFilters((current) => ({
                  ...current,
                  timePerQuestionSeconds: Number(event.target.value),
                }))
              }
            />
            <label htmlFor="revealOnSubmit" style={{ display: 'inline-flex', alignItems: 'center', gap: '0.5rem' }}>
              <input
                id="revealOnSubmit"
                type="checkbox"
                checked={Boolean(filters.showExplanationOnSubmit)}
                onChange={(event) =>
                  setFilters((current) => ({
                    ...current,
                    showExplanationOnSubmit: event.target.checked,
                  }))
                }
              />
              Reveal explanations immediately after answering
            </label>
          </div>
        )}
      </fieldset>

      <fieldset>
        <legend>Step 2 · Focus your content</legend>
        {filtersLoading ? (
          <p>Loading available filters…</p>
        ) : (
          <div className="stack">
            <div>
              <label htmlFor="query">Keyword search</label>
              <input
                id="query"
                name="query"
                placeholder="renal physiology, autonomic drugs, …"
                value={filters.query ?? ''}
                onChange={(event) => setFilters((current) => ({ ...current, query: event.target.value }))}
              />
            </div>
            <div className="stack" style={{ gap: '0.5rem' }}>
              <label htmlFor="subject">Subject</label>
              <select
                id="subject"
                value={filters.subject ?? ''}
                onChange={(event) => setFilters((current) => ({ ...current, subject: event.target.value || undefined }))}
              >
                <option value="">Any subject</option>
                {filterOptions.subjects.map((subject) => (
                  <option key={subject} value={subject}>
                    {subject}
                  </option>
                ))}
              </select>
            </div>
            <div className="stack" style={{ gap: '0.5rem' }}>
              <label htmlFor="system">System</label>
              <select
                id="system"
                value={filters.system ?? ''}
                onChange={(event) => setFilters((current) => ({ ...current, system: event.target.value || undefined }))}
              >
                <option value="">Any system</option>
                {filterOptions.systems.map((system) => (
                  <option key={system} value={system}>
                    {system}
                  </option>
                ))}
              </select>
            </div>
            <div className="stack" style={{ gap: '0.5rem' }}>
              <label htmlFor="status">Status</label>
              <select
                id="status"
                value={filters.status ?? ''}
                onChange={(event) => setFilters((current) => ({ ...current, status: event.target.value || undefined }))}
              >
                <option value="">Any status</option>
                {filterOptions.statuses.map((status) => (
                  <option key={status} value={status}>
                    {status}
                  </option>
                ))}
              </select>
            </div>
            <div className="stack" style={{ gap: '0.5rem' }}>
              <label htmlFor="difficulty">Difficulty</label>
              <select
                id="difficulty"
                value={filters.difficulty ?? ''}
                onChange={(event) =>
                  setFilters((current) => ({ ...current, difficulty: event.target.value || undefined }))
                }
              >
                <option value="">Any difficulty</option>
                {filterOptions.difficulties.map((difficulty) => (
                  <option key={difficulty} value={difficulty}>
                    {difficulty}
                  </option>
                ))}
              </select>
            </div>
            {filterOptions.tags.length > 0 && (
              <div className="stack">
                <span>Tags</span>
                <div className="toolbar">
                  {filterOptions.tags.map((tag) => {
                    const active = selectedTags.includes(tag);
                    return (
                      <button
                        type="button"
                        key={tag}
                        onClick={() => toggleTag(tag)}
                        className={active ? 'primary-button' : undefined}
                      >
                        #{tag}
                      </button>
                    );
                  })}
                </div>
                {selectedTags.length > 0 && (
                  <p className="badge">Selected: {selectedTags.join(', ')}</p>
                )}
              </div>
            )}
            <div className="stack" style={{ marginTop: '0.75rem' }}>
              <strong>Matching questions</strong>
              {previewLoading && <p>Loading preview…</p>}
              {!previewLoading && previewTotal === 0 && !previewError && <p>No questions match the current filters.</p>}
              {previewError && <p style={{ color: '#dc2626' }}>{previewError}</p>}
              {preview.length > 0 && (
                <ul className="stack" style={{ listStyle: 'disc', paddingLeft: '1.25rem', gap: '0.5rem' }}>
                  {preview.map((question) => (
                    <li key={question.id}>
                      <span>
                        <strong>{question.metadata?.subject ?? 'General'}</strong> · {summariseStem(question.stem)}
                      </span>
                    </li>
                  ))}
                </ul>
              )}
              {previewTotal > 0 && !previewLoading && !previewError && (
                <p style={{ fontSize: '0.9rem', color: '#475569' }}>
                  Showing {preview.length} of {previewTotal} matching question{previewTotal === 1 ? '' : 's'}.
                </p>
              )}
              {canLoadMorePreview && (
                <button
                  type="button"
                  className="secondary-button"
                  onClick={() => void loadMorePreview()}
                  disabled={previewLoading}
                >
                  {previewLoading ? 'Loading…' : 'Load more examples'}
                </button>
              )}
            </div>
          </div>
        )}
      </fieldset>

      <fieldset>
        <legend>Step 3 · How big should this block be?</legend>
        <div className="stack">
          <label htmlFor="questionCount">Number of questions</label>
          <input
            id="questionCount"
            type="number"
            min={1}
            max={80}
            value={filters.questionCount}
            onChange={(event) =>
              setFilters((current) => ({
                ...current,
                questionCount: Number(event.target.value),
              }))
            }
          />
          <div className="toolbar">
            {[10, 20, 40].map((count) => (
              <button type="button" key={count} onClick={() => quickSelect(count)}>
                {count}
              </button>
            ))}
            <button type="button" onClick={() => quickSelect(60)}>
              60 (exam block)
            </button>
          </div>
          <label style={{ display: 'inline-flex', alignItems: 'center', gap: '0.5rem' }}>
            <input
              type="checkbox"
              checked={filters.randomizeOrder}
              onChange={(event) =>
                setFilters((current) => ({
                  ...current,
                  randomizeOrder: event.target.checked,
                }))
              }
            />
            Randomise question order
          </label>
        </div>
      </fieldset>

      {error && <p style={{ color: '#dc2626' }}>{error}</p>}
      <div className="toolbar">
        <button type="submit" className="primary-button" disabled={isLoading}>
          {isLoading ? 'Building block…' : 'Create test'}
        </button>
        <button type="button" className="secondary-button" onClick={resetFilters}>
          Reset
        </button>
      </div>
    </form>
  );
};
