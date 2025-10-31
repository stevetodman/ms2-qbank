import { PracticeSetup } from '../components/PracticeSetup.tsx';
import { PracticeWorkspace } from '../components/PracticeWorkspace.tsx';
import { usePracticeSession } from '../context/PracticeSessionContext.tsx';

export const PracticeRoute = () => {
  const { session } = usePracticeSession();

  return (
    <main className="stack">
      <header className="card stack">
        <h1>Practice Workspace</h1>
        <p>
          Configure a practice block, focus on a curated set of questions, and capture review
          activity for follow-up. Modes mirror the PRD: timed blocks simulate exam pacing, tutor mode
          unlocks explanations after each response, and custom mode lets you tailor the timer and
          reveal behaviour.
        </p>
      </header>
      <PracticeSetup />
      {session && session.questions.length > 0 ? (
        <PracticeWorkspace />
      ) : (
        <section className="card">
          <p>Choose your mode and filters above to generate a practice block.</p>
        </section>
      )}
    </main>
  );
};
