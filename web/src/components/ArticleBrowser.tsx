import { useCallback, useEffect, useState } from 'react';
import { fetchArticleTags, fetchArticles, setArticleBookmark } from '../api/library';
import type { Article } from '../types/library';

export const ArticleBrowser = () => {
  const [articles, setArticles] = useState<Article[]>([]);
  const [tags, setTags] = useState<string[]>([]);
  const [query, setQuery] = useState('');
  const [activeTag, setActiveTag] = useState<string | undefined>();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadArticles = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const results = await fetchArticles({
        query: query.trim() || undefined,
        tag: activeTag,
      });
      setArticles(results);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Unable to load articles';
      setError(message);
    } finally {
      setLoading(false);
    }
  }, [query, activeTag]);

  useEffect(() => {
    void loadArticles();
  }, [loadArticles]);

  useEffect(() => {
    void (async () => {
      try {
        const loaded = await fetchArticleTags();
        setTags(loaded);
      } catch (err) {
        console.warn('Failed to load article tags', err);
      }
    })();
  }, []);

  const toggleBookmark = useCallback(
    async (article: Article) => {
      try {
        const updated = await setArticleBookmark(article.id, !article.bookmarked);
        setArticles((current) =>
          current.map((item) => (item.id === updated.id ? { ...item, bookmarked: updated.bookmarked } : item)),
        );
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to update bookmark';
        setError(message);
      }
    },
    [],
  );

  return (
    <section className="stack">
      <header className="card stack">
        <h1>Medical Library</h1>
        <p>
          Browse curated reference articles to reinforce question explanations. Use search and tag
          filters to find rapid refreshers while reviewing practice blocks.
        </p>
        <div className="toolbar" style={{ gap: '1rem', flexWrap: 'wrap' }}>
          <input
            type="search"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Search articles"
            aria-label="Search articles"
          />
          <select
            value={activeTag ?? ''}
            onChange={(event) =>
              setActiveTag(event.target.value ? event.target.value : undefined)
            }
            aria-label="Filter by tag"
          >
            <option value="">All tags</option>
            {tags.map((tag) => (
              <option key={tag} value={tag}>
                {tag}
              </option>
            ))}
          </select>
          <button type="button" className="secondary-button" onClick={() => void loadArticles()}>
            Refresh
          </button>
        </div>
      </header>

      <section className="stack">
        {loading && <p>Loading articles…</p>}
        {error && (
          <p role="alert" className="error">
            {error}
          </p>
        )}
        {!loading && !error && articles.length === 0 && (
          <p className="card">No articles matched your filters.</p>
        )}
        <div className="stack">
          {articles.map((article) => (
            <article key={article.id} className="card stack">
              <header className="toolbar" style={{ justifyContent: 'space-between', alignItems: 'start' }}>
                <div className="stack" style={{ margin: 0 }}>
                  <h2>{article.title}</h2>
                  <p>{article.summary}</p>
                </div>
                <button
                  type="button"
                  className={article.bookmarked ? 'secondary-button' : 'primary-button'}
                  onClick={() => {
                    void toggleBookmark(article);
                  }}
                >
                  {article.bookmarked ? 'Bookmarked' : 'Bookmark'}
                </button>
              </header>
              <p>{article.body}</p>
              {article.tags.length > 0 && (
                <footer className="toolbar" style={{ flexWrap: 'wrap', gap: '0.5rem' }}>
                  {article.tags.map((tag) => (
                    <span key={tag} className="badge">
                      {tag}
                    </span>
                  ))}
                </footer>
              )}
            </article>
          ))}
        </div>
      </section>
    </section>
  );
};
