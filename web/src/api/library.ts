import type {
  Article,
  ArticleFilterParams,
  BookmarkResponse,
  CreateNotePayload,
  NoteFilterParams,
  NotebookEntry,
  UpdateNotePayload,
} from '../types/library.ts';
import { resolveEnv } from '../utils/env.ts';
import { apiClient } from './client';

const LIBRARY_API_BASE_URL = resolveEnv('VITE_LIBRARY_API_BASE_URL', 'http://localhost:8004');

async function handleResponse<T>(response: Response, message: string): Promise<T> {
  if (!response.ok) {
    throw new Error(`${message} (status ${response.status})`);
  }
  return (await response.json()) as T;
}

export async function fetchArticles(params: ArticleFilterParams = {}): Promise<Article[]> {
  const searchParams = new URLSearchParams();
  if (params.query) {
    searchParams.set('query', params.query);
  }
  if (params.tag) {
    searchParams.set('tag', params.tag);
  }
  const query = searchParams.toString();
  const response = await fetch(
    query ? `${LIBRARY_API_BASE_URL}/articles?${query}` : `${LIBRARY_API_BASE_URL}/articles`,
  );
  return handleResponse<Article[]>(response, 'Failed to load articles');
}

export async function fetchArticleTags(): Promise<string[]> {
  const response = await fetch(`${LIBRARY_API_BASE_URL}/articles/tags`);
  return handleResponse<string[]>(response, 'Failed to load article tags');
}

export async function setArticleBookmark(articleId: string, bookmarked: boolean): Promise<BookmarkResponse> {
  const response = await fetch(`${LIBRARY_API_BASE_URL}/articles/${articleId}/bookmark`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ bookmarked }),
  });
  return handleResponse<BookmarkResponse>(response, 'Failed to update article bookmark');
}

export async function fetchNotes(params: NoteFilterParams = {}): Promise<NotebookEntry[]> {
  const searchParams = new URLSearchParams();
  if (params.query) {
    searchParams.set('query', params.query);
  }
  if (params.tag) {
    searchParams.set('tag', params.tag);
  }
  if (params.article_id) {
    searchParams.set('article_id', params.article_id);
  }
  if (params.question_id) {
    searchParams.set('question_id', params.question_id);
  }
  const query = searchParams.toString();
  const response = await fetch(
    query ? `${LIBRARY_API_BASE_URL}/notes?${query}` : `${LIBRARY_API_BASE_URL}/notes`,
  );
  return handleResponse<NotebookEntry[]>(response, 'Failed to load notes');
}

export async function fetchNoteTags(): Promise<string[]> {
  const response = await fetch(`${LIBRARY_API_BASE_URL}/notes/tags`);
  return handleResponse<string[]>(response, 'Failed to load note tags');
}

export async function createNote(payload: CreateNotePayload): Promise<NotebookEntry> {
  const response = await fetch(`${LIBRARY_API_BASE_URL}/notes`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  return handleResponse<NotebookEntry>(response, 'Failed to create note');
}

export async function updateNote(noteId: string, payload: UpdateNotePayload): Promise<NotebookEntry> {
  const response = await fetch(`${LIBRARY_API_BASE_URL}/notes/${noteId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  return handleResponse<NotebookEntry>(response, 'Failed to update note');
}

export async function setNoteBookmark(noteId: string, bookmarked: boolean): Promise<BookmarkResponse> {
  const response = await fetch(`${LIBRARY_API_BASE_URL}/notes/${noteId}/bookmark`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ bookmarked }),
  });
  return handleResponse<BookmarkResponse>(response, 'Failed to update note bookmark');
}

export async function linkNoteToQuestion(noteId: string, questionId: string): Promise<NotebookEntry> {
  const response = await fetch(`${LIBRARY_API_BASE_URL}/notes/${noteId}/link-review`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question_id: questionId }),
  });
  return handleResponse<NotebookEntry>(response, 'Failed to link note to question');
}
