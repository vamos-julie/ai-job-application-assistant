# AI Job Application Assistant

AI-assisted workflow for evidence-based job application analysis.

## Live Demo

Live app: https://ai-job-application-assistant.streamlit.app/

The public demo mode is available without a password and does not use the OpenAI API.

Public Live analysis is available without a password, with 5 successful analyses per day shared across all visitors. Optional passwords unlock guest or owner access.

This Streamlit app compares a job description with a CV and helps structure an application decision. It separates direct evidence from adjacent evidence, identifies gaps and risky claims, and generates tailored application materials for manual review.

## What the app does

The app supports five analysis modes:

- Full analysis: complete workflow with role fit, CV quality review, recruiter message, interview talking points, artifact roadmap, and final recommendation.
- Role fit only: score, category, gaps, job-family fit, direct vs adjacent evidence, and recommendation.
- CV quality only: evidence-safe CV improvements, skills audit, safe edits, evidence-dependent edits, and do-not-add items.
- Artifacts roadmap only: portfolio or project artifacts that could help close evidence gaps.
- Recruiter message only: cautious recruiter outreach message with risk check and safer version if needed.

## Key principles

The app is designed to avoid inflated application positioning.

It uses rules such as:

- distinguishing direct evidence from adjacent evidence;
- penalizing job-family mismatches;
- avoiding treating skills-only claims as strong evidence;
- separating safe CV edits from evidence-dependent edits;
- flagging claims that should not be added or implied;
- calibrating recommendations to score and role fit category.

## Access model

The app has four access modes:

- Public demo mode: no password, no API calls, no API cost.
- Public live mode: no password, 5 successful analyses per day shared across all visitors.
- Guest live mode: `GUEST_PASSWORD`, 18 successful analyses per day shared across guests.
- Owner live mode: `OWNER_PASSWORD`, no application-level daily limit.

Public and guest counters are independent and stored in `.usage/public_usage.json` and `.usage/guest_usage.json`. Daily allowances reset using `Asia/Nicosia`. Only successful, non-empty responses count; owner requests consume neither pool. Password access remains available when a quota is exhausted.

These local JSON files are ephemeral on Streamlit Community Cloud and may reset after restarts. Concurrent requests can race and exceed the allowance. This portfolio MVP quota is not a guaranteed hard spending limit.

Please remove confidential or sensitive personal information before submitting. Live text is processed using the OpenAI API.

## Tech stack

- Python
- Streamlit
- OpenAI API
- Markdown-based output rendering
- Local JSON usage tracking for demo quota

## Local setup

Install dependencies:

    pip install -r requirements.txt

Create a local Streamlit secrets file:

    mkdir -p .streamlit
    touch .streamlit/secrets.toml

Add your secrets to .streamlit/secrets.toml:

    OPENAI_API_KEY = "your_openai_api_key"
    OWNER_PASSWORD = "your_owner_password"
    GUEST_PASSWORD = "your_guest_password"

Run the app:

    streamlit run app.py

## Offline validation (no OpenAI credits)

From the project directory, with dependencies installed, run:

    python -m py_compile app.py tests/test_public_live.py
    python -m unittest discover -s tests -v

The tests run the real Streamlit UI with `AppTest`, replace the OpenAI client with mocked responses before loading the app, inject fake secrets, and redirect both usage files to a temporary directory. They never read or change your secrets file, modify real usage counters, or call the OpenAI API. Do not click Run live analysis in the normal app when testing without credits; that uses the real API.

Tests cover Demo mode, all five public analysis types, shared public usage, independent quotas, exhaustion with password upgrades, guest/owner session persistence across mode switches, input validation, empty responses, API errors, day resets, unknown access handling, and Markdown download availability after exhaustion.

## Deployment

The app is intended to be deployed with Streamlit Community Cloud.

Secrets should be configured in the Streamlit Cloud secrets interface, not committed to GitHub.

## Notes

This tool is decision support, not an automated hiring or career decision system. All outputs should be reviewed manually before use.
