import { act, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { AssessmentDelivery } from '../components/AssessmentDelivery.tsx';

const QUESTIONS = [
  {
    id: 'q1',
    stem: 'First question?',
    choices: [
      { label: 'A', text: 'Option A' },
      { label: 'B', text: 'Option B' },
    ],
  },
  {
    id: 'q2',
    stem: 'Second question?',
    choices: [
      { label: 'A', text: 'Choice A' },
      { label: 'B', text: 'Choice B' },
    ],
  },
];

describe('AssessmentDelivery', () => {
  it('submits mapped responses when the learner completes the exam', async () => {
    const user = userEvent.setup();
    const onSubmit = jest.fn().mockResolvedValue(undefined);

    render(
      <AssessmentDelivery questions={QUESTIONS} timeLimitSeconds={null} onSubmit={onSubmit} onTimeout={jest.fn()} />
    );

    await user.click(screen.getByLabelText(/A\. Option A/));
    await user.click(screen.getByRole('button', { name: /next/i }));
    await user.click(screen.getByLabelText(/B\. Choice B/));

    await user.click(screen.getByRole('button', { name: /submit assessment/i }));

    expect(onSubmit).toHaveBeenCalledTimes(1);
    expect(onSubmit).toHaveBeenCalledWith([
      { questionId: 'q1', answer: 'A' },
      { questionId: 'q2', answer: 'B' },
    ]);
  });

  it('invokes timeout handler and submits automatically when time expires', async () => {
    jest.useFakeTimers();
    const onSubmit = jest.fn().mockResolvedValue(undefined);
    const onTimeout = jest.fn();

    render(
      <AssessmentDelivery questions={QUESTIONS} timeLimitSeconds={1} onSubmit={onSubmit} onTimeout={onTimeout} />
    );

    await act(async () => {
      jest.advanceTimersByTime(1000);
    });

    expect(onTimeout).toHaveBeenCalledTimes(1);
    expect(onSubmit).toHaveBeenCalledTimes(1);
    expect(onSubmit.mock.calls[0][0]).toEqual([
      { questionId: 'q1', answer: null },
      { questionId: 'q2', answer: null },
    ]);

    jest.useRealTimers();
  });
});
