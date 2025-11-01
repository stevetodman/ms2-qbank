import React, { useState } from 'react';
import { createNote } from '../api/library';
import '../styles/quicknote.css';

interface QuickNoteProps {
  videoId?: string;
  questionId?: string;
  articleId?: string;
  timestamp?: number; // For video notes
  onSuccess?: () => void;
  compact?: boolean;
}

export function QuickNote({
  videoId,
  questionId,
  articleId,
  timestamp,
  onSuccess,
  compact = false,
}: QuickNoteProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [title, setTitle] = useState('');
  const [body, setBody] = useState('');
  const [tags, setTags] = useState('');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError(null);
    setSuccess(false);

    try {
      const tagArray = tags
        .split(',')
        .map((t) => t.trim())
        .filter(Boolean);

      const noteData: any = {
        title: title.trim(),
        body: body.trim(),
        tags: tagArray.length > 0 ? tagArray : undefined,
      };

      // Add resource links
      if (questionId) {
        noteData.question_ids = [questionId];
      }
      if (articleId) {
        noteData.article_ids = [articleId];
      }
      if (videoId) {
        noteData.video_ids = [videoId];
        // Include timestamp in the note body if provided
        if (timestamp !== undefined) {
          const minutes = Math.floor(timestamp / 60);
          const seconds = Math.floor(timestamp % 60);
          noteData.body = `[${minutes}:${seconds.toString().padStart(2, '0')}] ${noteData.body}`;
        }
      }

      await createNote(noteData);

      setSuccess(true);
      setTitle('');
      setBody('');
      setTags('');

      setTimeout(() => {
        setIsOpen(false);
        setSuccess(false);
        if (onSuccess) onSuccess();
      }, 1500);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save note');
    } finally {
      setSaving(false);
    }
  };

  if (compact && !isOpen) {
    return (
      <button
        className="quick-note-toggle compact"
        onClick={() => setIsOpen(true)}
        title="Take a note"
      >
        📝 Note
      </button>
    );
  }

  if (!isOpen) {
    return (
      <button className="quick-note-toggle" onClick={() => setIsOpen(true)}>
        📝 Take a Note
      </button>
    );
  }

  return (
    <div className="quick-note-container">
      <div className="quick-note-header">
        <h3>Quick Note</h3>
        <button className="quick-note-close" onClick={() => setIsOpen(false)}>
          ✕
        </button>
      </div>

      {error && <div className="quick-note-error">{error}</div>}
      {success && <div className="quick-note-success">Note saved!</div>}

      <form className="quick-note-form" onSubmit={handleSubmit}>
        <div className="quick-note-field">
          <label htmlFor="note-title">Title</label>
          <input
            id="note-title"
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Note title"
            required
            disabled={saving}
          />
        </div>

        <div className="quick-note-field">
          <label htmlFor="note-body">Content</label>
          <textarea
            id="note-body"
            value={body}
            onChange={(e) => setBody(e.target.value)}
            placeholder="What did you learn?"
            rows={4}
            required
            disabled={saving}
          />
        </div>

        <div className="quick-note-field">
          <label htmlFor="note-tags">Tags (comma-separated)</label>
          <input
            id="note-tags"
            type="text"
            value={tags}
            onChange={(e) => setTags(e.target.value)}
            placeholder="cardiology, important, review"
            disabled={saving}
          />
        </div>

        <div className="quick-note-meta">
          {videoId && <span className="quick-note-badge">📹 Video linked</span>}
          {questionId && <span className="quick-note-badge">❓ Question linked</span>}
          {articleId && <span className="quick-note-badge">📄 Article linked</span>}
          {timestamp !== undefined && (
            <span className="quick-note-badge">
              ⏱️ {Math.floor(timestamp / 60)}:{Math.floor(timestamp % 60)
                .toString()
                .padStart(2, '0')}
            </span>
          )}
        </div>

        <div className="quick-note-actions">
          <button type="button" onClick={() => setIsOpen(false)} disabled={saving}>
            Cancel
          </button>
          <button type="submit" className="btn-primary" disabled={saving}>
            {saving ? 'Saving...' : 'Save Note'}
          </button>
        </div>
      </form>
    </div>
  );
}
