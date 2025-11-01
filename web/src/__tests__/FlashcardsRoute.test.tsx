import { act, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { FlashcardsRoute } from '../routes/FlashcardsRoute.tsx';

describe('FlashcardsRoute', () => {
  afterEach(() => {
    jest.restoreAllMocks();
  });

  it('surfaces ReadyDeck and SmartCard study flows', async () => {
    const fetchSpy = jest.spyOn(global, 'fetch').mockImplementation((input: RequestInfo | URL) => {
      const url = typeof input === 'string' ? input : input.toString();
      if (url === '/api/flashcards/decks') {
        return Promise.resolve(
          new Response(
            JSON.stringify([
              {
                id: 1,
                name: 'Cardiology Mastery',
                description: 'High-yield hemodynamics deck',
                deck_type: 'ready',
                card_count: 2,
                created_at: '2024-07-01T00:00:00Z',
                updated_at: '2024-07-01T00:00:00Z',
              },
              {
                id: 2,
                name: 'Personal Path Pearls',
                description: 'Custom SmartCards',
                deck_type: 'smart',
                card_count: 1,
                created_at: '2024-07-01T00:00:00Z',
                updated_at: '2024-07-01T00:00:00Z',
              },
            ]),
            { status: 200, headers: { 'Content-Type': 'application/json' } },
          ),
        );
      }
      if (url === '/api/flashcards/decks/1') {
        return Promise.resolve(
          new Response(
            JSON.stringify({
              id: 1,
              name: 'Cardiology Mastery',
              description: 'High-yield hemodynamics deck',
              deck_type: 'ready',
              card_count: 2,
              created_at: '2024-07-01T00:00:00Z',
              updated_at: '2024-07-01T00:00:00Z',
              cards: [
                {
                  id: 10,
                  deck_id: 1,
                  prompt: 'Outline the conduction system of the heart.',
                  answer: 'SA node → AV node → bundle of His → bundle branches → Purkinje fibres.',
                  tags: ['cardiology'],
                  explanation: 'Electrical activity initiates in the SA node and propagates through specialised conduction tissue.',
                  created_at: '2024-07-01T00:00:00Z',
                  updated_at: '2024-07-01T00:00:00Z',
                },
                {
                  id: 11,
                  deck_id: 1,
                  prompt: 'Which murmur is heard with aortic stenosis?',
                  answer: 'Crescendo-decrescendo systolic murmur best at the right upper sternal border.',
                  tags: ['cardiology'],
                  explanation: null,
                  created_at: '2024-07-01T00:00:00Z',
                  updated_at: '2024-07-01T00:00:00Z',
                },
              ],
            }),
            { status: 200, headers: { 'Content-Type': 'application/json' } },
          ),
        );
      }
      if (url === '/api/flashcards/decks/2') {
        return Promise.resolve(
          new Response(
            JSON.stringify({
              id: 2,
              name: 'Personal Path Pearls',
              description: 'Custom SmartCards',
              deck_type: 'smart',
              card_count: 1,
              created_at: '2024-07-01T00:00:00Z',
              updated_at: '2024-07-01T00:00:00Z',
              cards: [
                {
                  id: 20,
                  deck_id: 2,
                  prompt: 'Identify two tumour suppressors mutated in pancreatic adenocarcinoma.',
                  answer: 'Common alterations include CDKN2A (p16) and SMAD4.',
                  tags: ['oncology'],
                  explanation: 'Loss of these suppressors drives unchecked cell cycle progression and TGF-β signalling disruption.',
                  created_at: '2024-07-01T00:00:00Z',
                  updated_at: '2024-07-01T00:00:00Z',
                },
              ],
            }),
            { status: 200, headers: { 'Content-Type': 'application/json' } },
          ),
        );
      }
      return Promise.reject(new Error(`Unexpected fetch for URL ${url}`));
    });

    const user = userEvent.setup();

    render(
      <MemoryRouter>
        <FlashcardsRoute />
      </MemoryRouter>,
    );

    await waitFor(() => expect(fetchSpy).toHaveBeenCalledWith('/api/flashcards/decks', expect.anything()));
    await waitFor(() => expect(fetchSpy).toHaveBeenCalledWith('/api/flashcards/decks/1', expect.anything()));

    expect(await screen.findByText(/Outline the conduction system/i)).toBeInTheDocument();

    await act(async () => {
      await user.click(screen.getByRole('button', { name: /Reveal answer/i }));
    });
    expect(await screen.findByText(/bundle of His/i)).toBeInTheDocument();

    await act(async () => {
      await user.click(screen.getByRole('button', { name: /Next card/i }));
    });
    expect(await screen.findByText(/Which murmur is heard/i)).toBeInTheDocument();

    await act(async () => {
      await user.click(screen.getByRole('button', { name: /SmartCards/i }));
    });

    await waitFor(() => expect(fetchSpy).toHaveBeenCalledWith('/api/flashcards/decks/2', expect.anything()));
    expect(await screen.findByText(/tumour suppressors mutated/i)).toBeInTheDocument();
  });
});
