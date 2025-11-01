import { Navigate, Route, Routes } from 'react-router-dom';
import { HomeRoute } from './routes/HomeRoute.tsx';
import { PracticeRoute } from './routes/PracticeRoute.tsx';
import { AssessmentRoute } from './routes/AssessmentRoute.tsx';
import { LibraryRoute } from './routes/LibraryRoute.tsx';
import { NotebookRoute } from './routes/NotebookRoute.tsx';
import { ContributorRoute } from './routes/ContributorRoute.tsx';

const App = () => {
  return (
    <Routes>
      <Route path="/" element={<HomeRoute />} />
      <Route path="/practice" element={<PracticeRoute />} />
      <Route path="/assessments" element={<AssessmentRoute />} />
      <Route path="/library" element={<LibraryRoute />} />
      <Route path="/notes" element={<NotebookRoute />} />
      <Route path="/contributors" element={<ContributorRoute />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
};

export default App;
