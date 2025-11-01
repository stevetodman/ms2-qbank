import { resolveEnv } from '../utils/env.ts';
import type {
  FlashcardCard,
  FlashcardDeckDetail,
  FlashcardDeckSummary,
  FlashcardDeckType,
} from '../types/flashcards.ts';

const FLASHCARDS_API_BASE_URL = resolveEnv('VITE_FLASHCARDS_API_BASE_URL', '/api/flashcards');

type RawDeckType = 'ready' | 'smart';

interface RawDeckSummary {
  id?: number;
  name?: string;
  description?: string | null;
  deck_type?: RawDeckType;
  card_count?: number;
  created_at?: string;
  updated_at?: string;
}

interface RawCard {
  id?: number;
  deck_id?: number;
  prompt?: string;
  answer?: string;
  tags?: unknown;
  explanation?: string | null;
  created_at?: string;
  updated_at?: string;
}

interface RawDeckDetail extends RawDeckSummary {
  cards?: RawCard[];
}

function normaliseDeckType(value: unknown): FlashcardDeckType {
  if (value === 'smart') {
    return 'smart';
  }
  return 'ready';
}

function normaliseTags(value: unknown): string[] {
  if (!Array.isArray(value)) {
    return [];
  }
  return value.filter((item): item is string => typeof item === 'string');
}

function normaliseCard(raw: RawCard): FlashcardCard {
  return {
    id: typeof raw.id === 'number' ? raw.id : 0,
    deckId: typeof raw.deck_id === 'number' ? raw.deck_id : 0,
    prompt: typeof raw.prompt === 'string' ? raw.prompt : '',
    answer: typeof raw.answer === 'string' ? raw.answer : '',
    tags: normaliseTags(raw.tags),
    explanation: typeof raw.explanation === 'string' ? raw.explanation : raw.explanation ?? null,
    createdAt: typeof raw.created_at === 'string' ? raw.created_at : '',
    updatedAt: typeof raw.updated_at === 'string' ? raw.updated_at : '',
  };
}

function normaliseDeckSummary(raw: RawDeckSummary): FlashcardDeckSummary {
  return {
    id: typeof raw.id === 'number' ? raw.id : 0,
    name: typeof raw.name === 'string' ? raw.name : '',
    description: typeof raw.description === 'string' ? raw.description : null,
    deckType: normaliseDeckType(raw.deck_type),
    cardCount: typeof raw.card_count === 'number' ? raw.card_count : 0,
    createdAt: typeof raw.created_at === 'string' ? raw.created_at : '',
    updatedAt: typeof raw.updated_at === 'string' ? raw.updated_at : '',
  };
}

function normaliseDeckDetail(raw: RawDeckDetail): FlashcardDeckDetail {
  const summary = normaliseDeckSummary(raw);
  const cards = Array.isArray(raw.cards) ? raw.cards.map(normaliseCard) : [];
  return { ...summary, cards };
}

export async function listDecks(deckType?: FlashcardDeckType): Promise<FlashcardDeckSummary[]> {
  const query = deckType ? `?deck_type=${deckType}` : '';
  const response = await fetch(`${FLASHCARDS_API_BASE_URL}/decks${query}`, {
    headers: { Accept: 'application/json' },
  });

  if (!response.ok) {
    throw new Error(`Failed to load decks (status ${response.status})`);
  }

  const json = (await response.json()) as RawDeckSummary[];
  return json.map(normaliseDeckSummary);
}

export async function fetchDeckDetail(deckId: number): Promise<FlashcardDeckDetail> {
  const response = await fetch(`${FLASHCARDS_API_BASE_URL}/decks/${deckId}`, {
    headers: { Accept: 'application/json' },
  });

  if (!response.ok) {
    throw new Error(`Failed to load deck ${deckId} (status ${response.status})`);
  }

  const json = (await response.json()) as RawDeckDetail;
  return normaliseDeckDetail(json);
}

export type { FlashcardDeckSummary, FlashcardDeckDetail, FlashcardDeckType, FlashcardCard };
