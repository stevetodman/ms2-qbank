import { test, expect } from '@playwright/test';

test('learner can build and run a tutor mode block', async ({ page }) => {
  const question = {
    id: 'q-demo',
    stem: 'A learner wants to know which answer is correct?',
    choices: [
      { label: 'A', text: 'The correct option' },
      { label: 'B', text: 'A distractor' },
      { label: 'C', text: 'Another distractor' },
      { label: 'D', text: 'Yet another distractor' },
    ],
    answer: 'A',
    explanation: {
      summary: 'The first option matches the stem.',
      rationales: [
        { choice: 'A', text: 'This is the right choice.' },
        { choice: 'B', text: 'Does not match the stem.' },
      ],
    },
    metadata: {
      subject: 'Pathology',
      difficulty: 'Medium',
      status: 'Unused',
    },
    tags: ['demo'],
  };

  const reviewHistory: Array<{ reviewer: string; action: string; timestamp: string; role: string; comment?: string }> = [];

  await page.route('**/api/search/search', async (route) => {
    const request = route.request();
    const body = (await request.postDataJSON()) as { limit?: number; offset?: number };
    const response = {
      data: [question],
      pagination: {
        total: 1,
        limit: body.limit ?? 1,
        offset: body.offset ?? 0,
        returned: 1,
      },
    };
    await route.fulfill({ json: response });
  });

  await page.route('**/api/reviews/questions/**', async (route) => {
    const request = route.request();
    if (request.method() === 'GET') {
      await route.fulfill({
        json: {
          question_id: question.id,
          current_status: 'draft',
          history: reviewHistory,
        },
      });
      return;
    }

    const payload = (await request.postDataJSON()) as { action: string; comment?: string; reviewer: string; role: string };
    reviewHistory.push({
      reviewer: payload.reviewer,
      action: payload.action,
      role: payload.role,
      timestamp: new Date().toISOString(),
      comment: payload.comment,
    });
    await route.fulfill({
      json: {
        question_id: question.id,
        current_status: payload.action,
        history: reviewHistory,
      },
    });
  });

  await page.goto('/');
  await page.getByRole('link', { name: 'Launch Practice Workspace' }).click();
  await page.getByRole('button', { name: 'Create test' }).click();
  await expect(page.getByRole('heading', { name: question.stem })).toBeVisible();

  await page.getByRole('button', { name: 'A. The correct option' }).click();
  await expect(page.getByText(question.explanation.summary)).toBeVisible();

  await page.getByRole('button', { name: 'Bookmark' }).click();
  await expect(page.getByText('#bookmark')).toBeVisible();
});
