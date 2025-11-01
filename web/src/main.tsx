import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import App from './App.tsx';
import { PracticeSessionProvider } from './context/PracticeSessionContext.tsx';
import './styles/global.css';

const container = document.getElementById('root');

if (!container) {
  throw new Error('Root element not found');
}

const root = createRoot(container);
root.render(
  <StrictMode>
    <BrowserRouter>
      <PracticeSessionProvider>
        <App />
      </PracticeSessionProvider>
    </BrowserRouter>
  </StrictMode>
);
