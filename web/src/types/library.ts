export interface Article {
  id: string;
  title: string;
  summary: string;
  body: string;
  tags: string[];
  bookmarked: boolean;
}

export interface NotebookEntry {
  id: string;
  title: string;
  body: string;
  tags: string[];
  article_ids: string[];
  question_ids: string[];
  bookmarked: boolean;
}

export interface ArticleFilterParams {
  query?: string;
  tag?: string;
}

export interface NoteFilterParams {
  query?: string;
  tag?: string;
  article_id?: string;
  question_id?: string;
}

export interface CreateNotePayload {
  title: string;
  body: string;
  tags?: string[];
  article_ids?: string[];
  question_ids?: string[];
}

export interface UpdateNotePayload {
  title?: string;
  body?: string;
  tags?: string[];
  article_ids?: string[];
  question_ids?: string[];
}

export interface BookmarkResponse {
  id: string;
  bookmarked: boolean;
}
