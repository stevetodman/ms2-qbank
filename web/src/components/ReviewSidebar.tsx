import { FormEvent, useEffect, useMemo, useState } from 'react';
import {
  bookmarkQuestion,
  escalateForReview,
  getReviewSummary,
  submitReviewAction,
  tagQuestion,
  type ReviewSummary,
} from '../api/reviews.ts';
import type { PracticeMode } from '../types/practice.ts';

const REVIEWER_ID = 'demo.learner';

interface ReviewSidebarProps {
  questionId: string;
  mode: PracticeMode;
}

export const ReviewSidebar = ({ questionId, mode }: ReviewSidebarProps) => {
  const [summary, setSummary] = useState<ReviewSummary | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [tagValue, setTagValue] = useState('');
  const [comment, setComment] = useState('');

  const allowedActions = useMemo(() => new Set(summary?.allowed_actions ?? []), [summary]);
  const canComment = allowedActions.has('comment');
  const canApprove = allowedActions.has('approve');
  const canReject = allowedActions.has('reject');

  useEffect(() => {
    let isActive = true;
    async function loadSummary() {
      setIsLoading(true);
      try {
        const data = await getReviewSummary(questionId);
        if (isActive) {
          setSummary(data);
          setError(null);
        }
      } catch (err) {
        if (isActive) {
          const message = err instanceof Error ? err.message : 'Unable to load review history';
          setError(message);
        }
      } finally {
        if (isActive) {
          setIsLoading(false);
        }
      }
    }
    void loadSummary();
    return () => {
      isActive = false;
    };
  }, [questionId]);

  const handleUpdate = async (action: () => Promise<ReviewSummary>) => {
    setIsLoading(true);
    try {
      const updated = await action();
      setSummary(updated);
      setError(null);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Review action failed';
      setError(message);
    } finally {
      setIsLoading(false);
    }
  };

  const ensureAllowed = (action: 'comment' | 'approve' | 'reject') => {
    if (!allowedActions.has(action)) {
      setError('You do not have permission to perform this action.');
      return false;
    }
    return true;
  };

  const handleBookmark = () => {
    if (!ensureAllowed('comment')) {
      return;
    }
    void handleUpdate(() => bookmarkQuestion(questionId, REVIEWER_ID));
  };

  const handleTagSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!tagValue.trim()) {
      return;
    }
    if (!ensureAllowed('comment')) {
      return;
    }
    void handleUpdate(() => tagQuestion(questionId, REVIEWER_ID, tagValue.trim())).then(() => {
      setTagValue('');
    });
  };

  const handleEscalate = () => {
    if (!ensureAllowed('comment')) {
      return;
    }
    void handleUpdate(() => escalateForReview(questionId, REVIEWER_ID, mode, comment));
  };

  const handleApprove = () => {
    if (!ensureAllowed('approve')) {
      return;
    }
    void handleUpdate(() =>
      submitReviewAction(questionId, {
        reviewer: REVIEWER_ID,
        action: 'approve',
        role: 'editor',
        comment: comment || undefined,
      })
    );
  };

  const handleReject = () => {
    if (!ensureAllowed('reject')) {
      return;
    }
    void handleUpdate(() =>
      submitReviewAction(questionId, {
        reviewer: REVIEWER_ID,
        action: 'reject',
        role: 'editor',
        comment: comment || undefined,
      })
    );
  };

  return (
    <aside className="stack" style={{ minWidth: '280px' }}>
      <div className="stack">
        <h2>Review controls</h2>
        <div className="toolbar">
          <button type="button" onClick={handleBookmark} disabled={isLoading || !canComment}>
            Bookmark
          </button>
          <button type="button" onClick={handleEscalate} disabled={isLoading || !canComment}>
            Flag for follow-up
          </button>
        </div>
        <form className="stack" onSubmit={handleTagSubmit}>
          <label htmlFor="tagValue">Add tag</label>
          <input
            id="tagValue"
            value={tagValue}
            onChange={(event) => setTagValue(event.target.value)}
            placeholder="high-yield, lab-values, …"
            disabled={!canComment}
          />
          <button type="submit" disabled={isLoading || !tagValue.trim() || !canComment}>
            Apply tag
          </button>
        </form>
        <label htmlFor="commentBox">Comment</label>
        <textarea
          id="commentBox"
          rows={3}
          value={comment}
          onChange={(event) => setComment(event.target.value)}
          placeholder="Notes for editors or personal reminders"
          disabled={!canComment && !canApprove && !canReject}
        />
        <div className="toolbar">
          <button type="button" onClick={handleApprove} disabled={isLoading || !canApprove}>
            Approve
          </button>
          <button type="button" onClick={handleReject} disabled={isLoading || !canReject}>
            Reject
          </button>
        </div>
        {error && <p style={{ color: '#dc2626' }}>{error}</p>}
        {!isLoading && summary && summary.allowed_actions.length === 0 && (
          <p style={{ color: '#6b7280' }}>You do not have permissions to perform review actions.</p>
        )}
      </div>
      <section className="card review-history">
        <h3>History</h3>
        {isLoading && <p>Loading…</p>}
        {!isLoading && summary && (
          <>
            <p className="badge">Current status: {summary.current_status}</p>
            {summary.history.length === 0 ? (
              <p style={{ color: '#6b7280' }}>No review activity recorded yet.</p>
            ) : (
              <ul>
                {summary.history.map((event) => (
                  <li key={`${event.timestamp}-${event.reviewer}-${event.action}`}>
                    <strong>{event.action.toUpperCase()}</strong> by {event.reviewer} ({event.role})<br />
                    <small>{new Date(event.timestamp).toLocaleString()}</small>
                    {event.comment && <p style={{ margin: '0.25rem 0 0' }}>{event.comment}</p>}
                  </li>
                ))}
              </ul>
            )}
          </>
        )}
      </section>
    </aside>
  );
};
