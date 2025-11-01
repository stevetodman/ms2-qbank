export type FlashcardDeckType = 'ready' | 'smart';

export interface FlashcardCard {
  id: number;
  deckId: number;
  prompt: string;
  answer: string;
  tags: string[];
  explanation: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface FlashcardDeckSummary {
  id: number;
  name: string;
  description: string | null;
  deckType: FlashcardDeckType;
  cardCount: number;
  createdAt: string;
  updatedAt: string;
}

export interface FlashcardDeckDetail extends FlashcardDeckSummary {
  cards: FlashcardCard[];
}
