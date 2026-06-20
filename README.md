# AI Job Application Assistant

AI-assisted workflow for evidence-based job application analysis.

## Live Demo

Live app: https://ai-job-application-assistant.streamlit.app/

The public demo mode is available without a password and does not use the OpenAI API.

Live analysis is password-protected to control API usage.

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

The app has three access levels:

- Public demo mode: no password, no API calls, no API cost.
- Guest live mode: password-protected, limited by daily guest quota.
- Owner live mode: password-protected, unlimited live runs.

The guest quota uses local JSON storage and is intended as demo-level cost control, not production-grade abuse prevention.

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

## Deployment

The app is intended to be deployed with Streamlit Community Cloud.

Secrets should be configured in the Streamlit Cloud secrets interface, not committed to GitHub.

## Notes

This tool is decision support, not an automated hiring or career decision system. All outputs should be reviewed manually before use.
