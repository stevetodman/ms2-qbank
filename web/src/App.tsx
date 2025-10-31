import { Navigate, Route, Routes } from 'react-router-dom';
import { HomeRoute } from './routes/HomeRoute.tsx';
import { PracticeRoute } from './routes/PracticeRoute.tsx';

const App = () => {
  return (
    <Routes>
      <Route path="/" element={<HomeRoute />} />
      <Route path="/practice" element={<PracticeRoute />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
};

export default App;
