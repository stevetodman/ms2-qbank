import { Navigate, Route, Routes } from 'react-router-dom';
import { ProtectedRoute } from './components/ProtectedRoute';
import { AppLayout } from './components/layout/AppLayout';
import { DashboardRoute } from './routes/Dashboard';
import { QBankRoute } from './routes/QBankRoute';
import { SelfAssessmentRoute } from './routes/SelfAssessmentRoute';
import { FlashcardsRoute } from './routes/FlashcardsRoute';
import { LibraryRoute } from './routes/LibraryRoute';
import { StudyPlannerRoute } from './routes/StudyPlannerRoute';
import { NotebookRoute } from './routes/NotebookRoute';
import { PerformanceRoute } from './routes/PerformanceRoute';
import { VideosRoute } from './routes/VideosRoute';
import { HelpRoute } from './routes/HelpRoute';
import { AccountRoute } from './routes/AccountRoute';
import { LoginRoute } from './routes/LoginRoute';
import { SignupRoute } from './routes/SignupRoute';

const App = () => {
  return (
    <Routes>
      {/* Public routes */}
      <Route path="/login" element={<LoginRoute />} />
      <Route path="/signup" element={<SignupRoute />} />

      {/* Protected routes */}
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <AppLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<DashboardRoute />} />
        <Route path="qbank" element={<QBankRoute />} />
        <Route path="self-assessment" element={<SelfAssessmentRoute />} />
        <Route path="flashcards/*" element={<FlashcardsRoute />} />
        <Route path="library" element={<LibraryRoute />} />
        <Route path="study-planner" element={<StudyPlannerRoute />} />
        <Route path="notebook" element={<NotebookRoute />} />
        <Route path="performance" element={<PerformanceRoute />} />
        <Route path="videos/*" element={<VideosRoute />} />
        <Route path="help" element={<HelpRoute />} />
        <Route path="account" element={<AccountRoute />} />
      </Route>

      {/* Fallback */}
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
};

export default App;
