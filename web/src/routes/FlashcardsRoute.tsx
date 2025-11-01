import { Route, Routes, useParams, useNavigate } from 'react-router-dom';
import { DeckBrowser } from '../components/DeckBrowser';
import { DeckForm } from '../components/DeckForm';
import { DeckManager } from '../components/DeckManager';
import { CardReview } from '../components/CardReview';

export const FlashcardsRoute = () => {
  return (
    <Routes>
      <Route index element={<DeckBrowser />} />
      <Route path="create" element={<DeckForm />} />
      <Route path="deck/:deckId" element={<DeckManager />} />
      <Route path="deck/:deckId/edit" element={<DeckForm />} />
      <Route path="study/:deckId" element={<StudyRoute />} />
    </Routes>
  );
};

// Wrapper component for CardReview to handle route params
function StudyRoute() {
  const { deckId } = useParams<{ deckId: string }>();
  const navigate = useNavigate();

  if (!deckId) {
    return <div>Invalid deck ID</div>;
  }

  return (
    <CardReview
      deckId={parseInt(deckId)}
      onComplete={() => navigate(`/flashcards/deck/${deckId}`)}
    />
  );
}
