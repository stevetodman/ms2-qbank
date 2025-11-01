import { useSearchParams } from 'react-router-dom';
import { NotebookWorkspace } from '../components/NotebookWorkspace.tsx';

export const NotebookRoute = () => {
  const [params] = useSearchParams();
  const questionId = params.get('questionId') ?? undefined;
  const articleId = params.get('articleId') ?? undefined;

  return (
    <main className="stack">
      <NotebookWorkspace initialQuestionId={questionId} initialArticleId={articleId} />
    </main>
  );
};
