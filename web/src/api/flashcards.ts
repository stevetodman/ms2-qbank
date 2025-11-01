import { apiClient } from './client';

// Types matching backend models
export interface Deck {
  id: number;
  user_id?: number;
  name: string;
  deck_type: 'ready' | 'smart';
  category?: string;
  description?: string;
  created_at: string;
  updated_at: string;
}

export interface Flashcard {
  id: number;
  deck_id: number;
  front: string;
  back: string;
  source_question_id?: string;
  created_at: string;
}

export interface CardReview {
  id: number;
  card_id: number;
  user_id?: number;
  ease_factor: number;
  interval_days: number;
  repetitions: number;
  next_review_date: string;
  last_review_date?: string;
  last_quality?: number;
  streak: number;
  total_reviews: number;
}

export interface DueCard {
  card: Flashcard;
  review: CardReview;
}

export interface DeckStats {
  total_cards: number;
  new_cards: number;
  learning_cards: number;
  mature_cards: number;
  cards_due_today: number;
  accuracy_percentage?: number;
}

export interface DeckCreate {
  name: string;
  deck_type: 'ready' | 'smart';
  category?: string;
  description?: string;
}

export interface DeckUpdate {
  name?: string;
  category?: string;
  description?: string;
}

export interface CardCreate {
  deck_id: number;
  front: string;
  back: string;
  source_question_id?: string;
}

export interface CardUpdate {
  front?: string;
  back?: string;
}

export interface ReviewSubmit {
  card_id: number;
  quality: number;
  user_id?: number;
}

const FLASHCARD_BASE = 'http://localhost:8006';

// Deck operations
export async function createDeck(data: DeckCreate, token: string): Promise<Deck> {
  const response = await apiClient(`${FLASHCARD_BASE}/decks`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify(data),
  });
  return response;
}

export async function listDecks(deckType?: 'ready' | 'smart', token?: string): Promise<Deck[]> {
  const params = deckType ? `?deck_type=${deckType}` : '';
  const headers: Record<string, string> = {};
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  const response = await apiClient(`${FLASHCARD_BASE}/decks${params}`, { headers });
  return response;
}

export async function getDeck(deckId: number, token?: string): Promise<Deck> {
  const headers: Record<string, string> = {};
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  const response = await apiClient(`${FLASHCARD_BASE}/decks/${deckId}`, { headers });
  return response;
}

export async function updateDeck(deckId: number, data: DeckUpdate, token: string): Promise<Deck> {
  const response = await apiClient(`${FLASHCARD_BASE}/decks/${deckId}`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify(data),
  });
  return response;
}

export async function deleteDeck(deckId: number, token: string): Promise<void> {
  await apiClient(`${FLASHCARD_BASE}/decks/${deckId}`, {
    method: 'DELETE',
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });
}

export async function getDeckStats(deckId: number, token?: string): Promise<DeckStats> {
  const headers: Record<string, string> = {};
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  const response = await apiClient(`${FLASHCARD_BASE}/decks/${deckId}/stats`, { headers });
  return response;
}

// Card operations
export async function createCard(data: CardCreate, token: string): Promise<Flashcard> {
  const response = await apiClient(`${FLASHCARD_BASE}/cards`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify(data),
  });
  return response;
}

export async function getCard(cardId: number, token?: string): Promise<Flashcard> {
  const headers: Record<string, string> = {};
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  const response = await apiClient(`${FLASHCARD_BASE}/cards/${cardId}`, { headers });
  return response;
}

export async function updateCard(cardId: number, data: CardUpdate, token: string): Promise<Flashcard> {
  const response = await apiClient(`${FLASHCARD_BASE}/cards/${cardId}`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify(data),
  });
  return response;
}

export async function deleteCard(cardId: number, token: string): Promise<void> {
  await apiClient(`${FLASHCARD_BASE}/cards/${cardId}`, {
    method: 'DELETE',
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });
}

export async function listCardsInDeck(deckId: number, token?: string): Promise<Flashcard[]> {
  const headers: Record<string, string> = {};
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  const response = await apiClient(`${FLASHCARD_BASE}/decks/${deckId}/cards`, { headers });
  return response;
}

// Review operations
export async function getDueCards(deckId: number, limit?: number, token?: string): Promise<DueCard[]> {
  const params = limit ? `?limit=${limit}` : '';
  const headers: Record<string, string> = {};
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  const response = await apiClient(`${FLASHCARD_BASE}/decks/${deckId}/due${params}`, { headers });
  return response;
}

export async function submitReview(data: ReviewSubmit, token?: string): Promise<CardReview> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  const response = await apiClient(`${FLASHCARD_BASE}/reviews`, {
    method: 'POST',
    headers,
    body: JSON.stringify(data),
  });
  return response;
}
