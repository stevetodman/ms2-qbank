import { Navigate, Route, Routes } from 'react-router-dom';
import { HomeRoute } from './routes/HomeRoute.tsx';
import { PracticeRoute } from './routes/PracticeRoute.tsx';
import { AssessmentRoute } from './routes/AssessmentRoute.tsx';
import { FlashcardsRoute } from './routes/FlashcardsRoute.tsx';

const App = () => {
  return (
    <Routes>
      <Route path="/" element={<HomeRoute />} />
      <Route path="/practice" element={<PracticeRoute />} />
      <Route path="/assessments" element={<AssessmentRoute />} />
      <Route path="/flashcards" element={<FlashcardsRoute />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
};

export default App;
