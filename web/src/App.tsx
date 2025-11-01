import { Navigate, Route, Routes } from 'react-router-dom';
import { AppLayout } from './components/layout/AppLayout.tsx';
import { DashboardRoute } from './routes/DashboardRoute.tsx';
import { QBankRoute } from './routes/QBankRoute.tsx';
import { SelfAssessmentRoute } from './routes/SelfAssessmentRoute.tsx';
import { FlashcardsRoute } from './routes/FlashcardsRoute.tsx';
import { LibraryRoute } from './routes/LibraryRoute.tsx';
import { StudyPlannerRoute } from './routes/StudyPlannerRoute.tsx';
import { NotebookRoute } from './routes/NotebookRoute.tsx';
import { PerformanceRoute } from './routes/PerformanceRoute.tsx';
import { VideosRoute } from './routes/VideosRoute.tsx';
import { HelpRoute } from './routes/HelpRoute.tsx';
import { AccountRoute } from './routes/AccountRoute.tsx';

const App = () => {
  return (
    <Routes>
      <Route path="/" element={<AppLayout />}>
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<DashboardRoute />} />
        <Route path="qbank" element={<QBankRoute />} />
        <Route path="self-assessment" element={<SelfAssessmentRoute />} />
        <Route path="flashcards" element={<FlashcardsRoute />} />
        <Route path="library" element={<LibraryRoute />} />
        <Route path="study-planner" element={<StudyPlannerRoute />} />
        <Route path="notebook" element={<NotebookRoute />} />
        <Route path="performance" element={<PerformanceRoute />} />
        <Route path="videos" element={<VideosRoute />} />
        <Route path="help" element={<HelpRoute />} />
        <Route path="account" element={<AccountRoute />} />
      </Route>
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
};

export default App;
