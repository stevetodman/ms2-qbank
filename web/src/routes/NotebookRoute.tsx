import { useSearchParams } from 'react-router-dom';
import { NotebookWorkspace } from '../components/NotebookWorkspace.tsx';

export const NotebookRoute = () => {
  const [params] = useSearchParams();
  const questionId = params.get('questionId') ?? undefined;
  const articleId = params.get('articleId') ?? undefined;

  return (
    <div className="stack" data-page="notebook">
      <NotebookWorkspace initialQuestionId={questionId} initialArticleId={articleId} />
    </div>
  );
};
