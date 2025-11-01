import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { AssessmentSetupForm } from '../components/AssessmentSetupForm.tsx';

describe('AssessmentSetupForm', () => {
  it('submits normalised blueprint data', async () => {
    const user = userEvent.setup();
    const onSubmit = jest.fn().mockResolvedValue(undefined);

    render(<AssessmentSetupForm onSubmit={onSubmit} />);

    await user.type(screen.getByLabelText(/candidate identifier/i), ' Candidate-001 ');
    await user.type(screen.getByLabelText(/subject focus/i), 'Pathology');
    await user.type(screen.getByLabelText(/system focus/i), 'Cardiovascular');
    await user.type(screen.getByLabelText(/difficulty target/i), 'Hard');
    await user.type(screen.getByLabelText(/tags/i), ' timed , intensive ');
    await user.clear(screen.getByLabelText(/time limit/i));
    await user.type(screen.getByLabelText(/time limit/i), '90');

    await user.click(screen.getByRole('button', { name: /begin assessment/i }));

    expect(onSubmit).toHaveBeenCalledTimes(1);
    expect(onSubmit).toHaveBeenCalledWith({
      candidateId: 'Candidate-001',
      subject: 'Pathology',
      system: 'Cardiovascular',
      difficulty: 'Hard',
      tags: ['timed', 'intensive'],
      timeLimitMinutes: 90,
    });
  });

  it('disables submit button when busy', async () => {
    const user = userEvent.setup();
    const onSubmit = jest.fn();
    render(<AssessmentSetupForm onSubmit={onSubmit} busy />);

    const button = screen.getByRole('button', { name: /preparing assessment/i });
    expect(button).toBeDisabled();
    await user.type(screen.getByLabelText(/candidate identifier/i), 'candidate');
    expect(onSubmit).not.toHaveBeenCalled();
  });
});
