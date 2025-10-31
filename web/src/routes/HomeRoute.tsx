import { Link } from 'react-router-dom';

export const HomeRoute = () => {
  return (
    <main>
      <section className="card stack">
        <header>
          <h1>MS2 QBank Learner Experience</h1>
          <p>
            Build focused practice sessions, take questions in timed or tutor mode, and log review
            actions without leaving the browser. This early web client connects to the FastAPI search
            and review services shipped in the backend to provide an end-to-end learner workflow.
          </p>
        </header>
        <div className="stack">
          <h2>What can you do today?</h2>
          <ul>
            <li>Create a personalised practice block with rich filters and delivery modes.</li>
            <li>Answer questions with immediate or deferred explanations based on your mode.</li>
            <li>Bookmark, tag, and request editorial review directly from the question surface.</li>
            <li>Review the audit history for every question to understand outstanding actions.</li>
          </ul>
        </div>
        <footer>
          <Link className="primary-button" to="/practice">
            Launch Practice Workspace
          </Link>
        </footer>
      </section>
    </main>
  );
};
