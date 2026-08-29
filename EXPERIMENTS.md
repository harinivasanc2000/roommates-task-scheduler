# Homeflow experiments

Experimental work lives on a separate branch until it has been tried and accepted. Production history remains in `CHANGELOG.md` only after an experiment is merged.

## My Next Task

- Branch: `experiment/my-next-task`
- Status: ready to try (superseded by helpful-features which includes it)
- Hypothesis: showing the nearest incomplete personal task immediately after login will reduce scrolling and make the mobile flow feel obvious.
- What changes: a focused card shows the task, scheduled date, remaining count, note, one-tap completion, and rescheduling.
- Keep it if: housemates can find and act on their next task without opening the weekly calendar first.
- Rework or remove it if: the card feels repetitive, promotes the wrong task, or distracts from the rota overview.

## Helpful features pack

- Branch: `experiment/helpful-features`
- Status: ready to try
- Builds on: `experiment/my-next-task`
- Hypothesis: a small set of accountability and convenience tools (overdue awareness, skip, personal streaks, fairness board, activity feed, vacation mode) will make the rota fairer and easier to keep current without adding admin friction.
- What changes:
  - Next-task card prioritises overdue work and adds a “Not today” skip (nudges to tomorrow when still inside the week).
  - Personal stats strip: this-week progress, completion streak, lifetime celebrations.
  - Household fairness board (completions over the last 4 weeks).
  - Recent activity feed (completions and notes).
  - Vacation / away mode: set `away_until` so the rotation skips that person until the date.
  - Visual overdue styling on calendar tasks.
- Keep it if: housemates use skip/away/fairness without confusion and the dashboard still feels calm.
- Rework or remove pieces if: the extra panels feel noisy on mobile, skip is overused, or fairness creates tension instead of clarity.
