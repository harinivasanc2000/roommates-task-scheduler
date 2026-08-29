# Changelog

This file is an append-only history of Homeflow. Do not delete, rewrite, reorder, or squash existing entries. Add each future release at the bottom with its date, version, related commit, and a concise list of changes.

## 0.1.0 — 2026-08-29 — `fc9a364`

- Created the Django roommate rota application and starter household chores.
- Added deterministic alphabetical weekly rotation.
- Added a five-week calendar, task completion, progress tracking, shared notes, and rescheduling.
- Added personal identity selection, roommate characters, greetings, and personal ICS exports.
- Added public roommate and chore management without requiring Django admin.
- Added themes and visual customisation.
- Added automated tests and initial database migrations.

## 0.2.0 — 2026-08-29 — `fd4f3d7`

- Reworked the interface for phones with swipeable days and larger touch controls.
- Added sticky mobile navigation and bottom-sheet dialogs.
- Added PostgreSQL, Gunicorn, WhiteNoise, and environment-based production configuration.
- Added a production build script and deployment guide.
- Isolated the project as its own Git repository and published it to GitHub.

## 0.3.0 — 2026-08-29 — `907febb`

- Added an editable rota starting Monday and starting roommate.
- Configured Monday 31 August 2026 to begin Huanlin's week, making the preceding week Hari's.
- Added desktop and mobile controls for changing the rota anchor.
- Added a Render Blueprint for creating the web service and PostgreSQL database.
- Added automatic Render hostname and CSRF configuration.
- Expanded rotation coverage to six automated tests.

## 0.3.1 — 2026-08-29 — `bfb73fc`

- Added a production data migration that safely creates Hari, Huanlin, Jaclyn, and Tanith on a fresh PostgreSQL database.
- Restored the intended rotation with Hari owning 24–30 August and Huanlin starting Monday 31 August 2026.
- Added an always-visible close button to the identity picker.
- Added options to continue without choosing or open household management directly.
- Added regression coverage for the identity-popup escape path.

## 0.4.0 — 2026-08-29 — `9c34b5c`

- Enforced task ownership on the server so roommates can only complete, move, or annotate their own assigned tasks.
- Added hashed 4-digit roommate PINs to protect identity switching.
- Added persistent whole-week swap requests with recipient notifications.
- Added recipient-only accept and decline actions; rotas change only after acceptance.
- Added requester-facing pending, accepted, and declined swap statuses.
- Made the selected roommate's next rota and progress the dashboard focus.
- Increased the visual emphasis of personal weeks and dimmed other weeks into read-only context.
- Isolated completion progress by owner and week and added regression coverage for the previous carry-over issue.
- Expanded the automated test suite to ten tests.

## 0.4.1 — 2026-08-29 — `154b45e`

- Removed roommate PINs and restored frictionless one-tap identity selection.
- Kept server-side task ownership checks tied to the selected browser session.
- Collapsed other roommates' weeks so their tasks and progress do not distract from the current person.
- Removed other roommates' completion percentages from the current person's dashboard.
- Made the selected roommate's next rota the primary overview and strengthened its calendar highlight.
- Added animated, character-specific completion celebrations for Hari, Huanlin, Jaclyn, and Tanith.
- Added regression assertions for separate progress and private task overviews.
