import { FormEvent, useCallback, useEffect, useState } from 'react';
import {
  createNote,
  fetchNoteTags,
  fetchNotes,
  linkNoteToQuestion,
  setNoteBookmark,
} from '../api/library';
import type { NotebookEntry } from '../types/library';

interface NotebookWorkspaceProps {
  initialQuestionId?: string;
  initialArticleId?: string;
}

interface NoteFormState {
  title: string;
  body: string;
  tags: string;
  articles: string;
}

const DEFAULT_FORM: NoteFormState = {
  title: '',
  body: '',
  tags: '',
  articles: '',
};

export const NotebookWorkspace = ({ initialQuestionId, initialArticleId }: NotebookWorkspaceProps) => {
  const [notes, setNotes] = useState<NotebookEntry[]>([]);
  const [tags, setTags] = useState<string[]>([]);
  const [query, setQuery] = useState('');
  const [activeTag, setActiveTag] = useState<string | undefined>();
  const [filterQuestionId, setFilterQuestionId] = useState(initialQuestionId ?? '');
  const [filterArticleId, setFilterArticleId] = useState(initialArticleId ?? '');
  const [linkQuestionId, setLinkQuestionId] = useState(initialQuestionId ?? '');
  const [formState, setFormState] = useState<NoteFormState>(DEFAULT_FORM);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const loadNotes = useCallback(async () => {
    setLoading(true);
    setError(null);
    setSuccessMessage(null);
    try {
      const payload = await fetchNotes({
        query: query.trim() || undefined,
        tag: activeTag,
        article_id: filterArticleId.trim() || undefined,
        question_id: filterQuestionId.trim() || undefined,
      });
      setNotes(payload);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Unable to load notes';
      setError(message);
      setSuccessMessage(null);
    } finally {
      setLoading(false);
    }
  }, [query, activeTag, filterArticleId, filterQuestionId]);

  useEffect(() => {
    void loadNotes();
  }, [loadNotes]);

  useEffect(() => {
    void (async () => {
      try {
        const loaded = await fetchNoteTags();
        setTags(loaded);
      } catch (err) {
        console.warn('Failed to load note tags', err);
      }
    })();
  }, []);

  const handleBookmark = useCallback(async (note: NotebookEntry) => {
    try {
      const result = await setNoteBookmark(note.id, !note.bookmarked);
      setNotes((current) =>
        current.map((item) => (item.id === result.id ? { ...item, bookmarked: result.bookmarked } : item)),
      );
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to update bookmark';
      setError(message);
      setSuccessMessage(null);
    }
  }, []);

  const handleCreateNote = useCallback(
    async (event: FormEvent<HTMLFormElement>) => {
      event.preventDefault();
      try {
        const tagsToSend = formState.tags
          .split(',')
          .map((tag) => tag.trim())
          .filter(Boolean);
        const articleIds = formState.articles
          .split(',')
          .map((id) => id.trim())
          .filter(Boolean);
        const created = await createNote({
          title: formState.title.trim(),
          body: formState.body.trim(),
          tags: tagsToSend.length > 0 ? tagsToSend : undefined,
          article_ids: articleIds.length > 0 ? articleIds : undefined,
          question_ids: linkQuestionId ? [linkQuestionId] : undefined,
        });
        setFormState(DEFAULT_FORM);
        setSuccessMessage('Note captured successfully.');
        setNotes((current) => [created, ...current]);
        void loadNotes();
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to create note';
        setError(message);
        setSuccessMessage(null);
      }
    },
    [formState, linkQuestionId, loadNotes],
  );

  const handleLinkToQuestion = useCallback(
    async (note: NotebookEntry) => {
      if (!linkQuestionId.trim()) {
        setError('Enter a question ID before linking notes.');
        return;
      }
      try {
        const updated = await linkNoteToQuestion(note.id, linkQuestionId.trim());
        setNotes((current) => current.map((item) => (item.id === updated.id ? updated : item)));
        setSuccessMessage(`Linked note to ${linkQuestionId.trim()}.`);
        void loadNotes();
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to link note to question';
        setError(message);
        setSuccessMessage(null);
      }
    },
    [linkQuestionId, loadNotes],
  );

  return (
    <section className="stack">
      <header className="card stack">
        <h1>Learner Notebook</h1>
        <p>
          Capture teaching points while you practise. Notes stay linked to reference articles and
          can be attached to question reviews for fast follow-up.
        </p>
        <div className="toolbar" style={{ gap: '1rem', flexWrap: 'wrap' }}>
          <input
            type="search"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Search notes"
          />
          <select
            value={activeTag ?? ''}
            onChange={(event) => setActiveTag(event.target.value || undefined)}
            aria-label="Filter notes by tag"
          >
            <option value="">All tags</option>
            {tags.map((tag) => (
              <option key={tag} value={tag}>
                {tag}
              </option>
            ))}
          </select>
          <input
            type="text"
            value={filterArticleId}
            onChange={(event) => setFilterArticleId(event.target.value)}
            placeholder="Filter by article ID"
            aria-label="Filter notes by article ID"
          />
          <input
            type="text"
            value={filterQuestionId}
            onChange={(event) => setFilterQuestionId(event.target.value)}
            placeholder="Filter by question ID"
            aria-label="Filter notes by question ID"
          />
          <button type="button" className="secondary-button" onClick={() => void loadNotes()}>
            Refresh
          </button>
        </div>
      </header>

      <section className="card stack">
        <h2>New note</h2>
        <form className="stack" onSubmit={(event) => void handleCreateNote(event)}>
          <label className="stack">
            <span>Title</span>
            <input
              required
              value={formState.title}
              onChange={(event) => setFormState((state) => ({ ...state, title: event.target.value }))}
            />
          </label>
          <label className="stack">
            <span>Body</span>
            <textarea
              required
              rows={4}
              value={formState.body}
              onChange={(event) => setFormState((state) => ({ ...state, body: event.target.value }))}
            />
          </label>
          <div className="toolbar" style={{ gap: '1rem', flexWrap: 'wrap' }}>
            <label className="stack" style={{ flex: 1 }}>
              <span>Tags (comma separated)</span>
              <input
                value={formState.tags}
                onChange={(event) => setFormState((state) => ({ ...state, tags: event.target.value }))}
              />
            </label>
            <label className="stack" style={{ flex: 1 }}>
              <span>Related article IDs</span>
              <input
                value={formState.articles}
                onChange={(event) =>
                  setFormState((state) => ({ ...state, articles: event.target.value }))
                }
              />
            </label>
          </div>
          <label className="stack">
            <span>Link to question ID (optional)</span>
            <input
              value={linkQuestionId}
              onChange={(event) => setLinkQuestionId(event.target.value)}
              placeholder="question-204"
            />
          </label>
          <button type="submit" className="primary-button">
            Save note
          </button>
        </form>
      </section>

      <section className="stack">
        {loading && <p>Loading notes…</p>}
        {error && (
          <p role="alert" className="error">
            {error}
          </p>
        )}
        {successMessage && !error && (
          <p role="status" style={{ color: '#15803d', fontWeight: 600 }}>
            {successMessage}
          </p>
        )}
        {!loading && !error && notes.length === 0 && <p className="card">No notes to display.</p>}
        <div className="stack">
          {notes.map((note) => (
            <article key={note.id} className="card stack">
              <header className="toolbar" style={{ justifyContent: 'space-between', alignItems: 'start' }}>
                <div className="stack" style={{ margin: 0 }}>
                  <h3>{note.title}</h3>
                  <p>{note.body}</p>
                </div>
                <button
                  type="button"
                  className={note.bookmarked ? 'secondary-button' : 'primary-button'}
                  onClick={() => {
                    void handleBookmark(note);
                  }}
                >
                  {note.bookmarked ? 'Bookmarked' : 'Bookmark'}
                </button>
              </header>
              {note.tags.length > 0 && (
                <div className="toolbar" style={{ flexWrap: 'wrap', gap: '0.5rem' }}>
                  {note.tags.map((tag) => (
                    <span key={tag} className="badge">
                      {tag}
                    </span>
                  ))}
                </div>
              )}
              <div className="stack" style={{ marginTop: '0.5rem' }}>
                {note.article_ids.length > 0 && (
                  <p>
                    Articles: <code>{note.article_ids.join(', ')}</code>
                  </p>
                )}
                {note.question_ids.length > 0 && (
                  <p>
                    Linked reviews: <code>{note.question_ids.join(', ')}</code>
                  </p>
                )}
              </div>
              <footer className="toolbar" style={{ gap: '1rem', flexWrap: 'wrap' }}>
                <button
                  type="button"
                  className="secondary-button"
                  onClick={() => {
                    void handleLinkToQuestion(note);
                  }}
                >
                  Link to review
                </button>
              </footer>
            </article>
          ))}
        </div>
      </section>
    </section>
  );
};
