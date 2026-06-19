import streamlit as st
from openai import OpenAI
import json
import re
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Optional
from html import escape

# -------------------------------------------------
# Configuration
# -------------------------------------------------

st.set_page_config(
    page_title="AI Job Application Assistant",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="collapsed",
)

MODEL_NAME = "gpt-5.4-mini"

MAX_JD_CHARS = 12000
MAX_CV_CHARS = 10000


GUEST_DAILY_LIMIT = 18
APP_TIMEZONE = "Asia/Nicosia"

USAGE_DIR = Path(".usage")
USAGE_FILE = USAGE_DIR / "guest_usage.json"


def get_today_key() -> str:
    """Return today's date key in the app timezone."""
    return datetime.now(ZoneInfo(APP_TIMEZONE)).date().isoformat()


def load_guest_usage() -> dict:
    """Load guest usage from a local JSON file.

    This is demo-level quota tracking. It is sufficient for a portfolio demo,
    but not production-grade persistent storage.
    """
    try:
        if not USAGE_FILE.exists():
            return {}
        with USAGE_FILE.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_guest_usage(usage: dict) -> None:
    """Save guest usage to a local JSON file."""
    USAGE_DIR.mkdir(parents=True, exist_ok=True)
    with USAGE_FILE.open("w", encoding="utf-8") as f:
        json.dump(usage, f, indent=2)


def get_guest_usage_today() -> int:
    usage = load_guest_usage()
    return int(usage.get(get_today_key(), 0))


def get_guest_remaining_runs() -> int:
    used = get_guest_usage_today()
    return max(GUEST_DAILY_LIMIT - used, 0)


def increment_guest_usage() -> None:
    usage = load_guest_usage()
    today = get_today_key()
    usage[today] = int(usage.get(today, 0)) + 1
    save_guest_usage(usage)

# -------------------------------------------------
# CSS / beautification helpers
# ------------------------------------------------- 

def inject_custom_css() -> None:
    st.markdown(
        """
<style>
[data-testid="stAppViewContainer"] {
    background: linear-gradient(180deg, #f8fbff 0%, #eef6ff 45%, #ffffff 100%);
}

.block-container {
    max-width: 1120px;
    padding-top: 2rem;
    padding-bottom: 4rem;
}

.hero-card {
    background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 45%, #ffffff 100%);
    border: 1px solid #bfdbfe;
    border-radius: 24px;
    padding: 30px 32px;
    box-shadow: 0 12px 30px rgba(30, 64, 175, 0.08);
    margin-bottom: 22px;
}

.hero-title {
    font-size: 2.25rem;
    font-weight: 800;
    color: #0f172a;
    margin-bottom: 8px;
    letter-spacing: -0.03em;
}

.hero-subtitle {
    font-size: 1.05rem;
    color: #334155;
    line-height: 1.55;
    max-width: 900px;
}

.pill-row {
    margin-top: 18px;
}

.pill {
    display: inline-block;
    background: #ffffff;
    border: 1px solid #bfdbfe;
    color: #1d4ed8;
    border-radius: 999px;
    padding: 7px 12px;
    margin-right: 8px;
    margin-bottom: 8px;
    font-size: 0.88rem;
    font-weight: 600;
}

.info-card {
    background: #ffffff;
    border: 1px solid #dbeafe;
    border-radius: 18px;
    padding: 18px 20px;
    box-shadow: 0 8px 22px rgba(15, 23, 42, 0.04);
    height: 100%;
}

.info-card-title {
    color: #1e3a8a;
    font-weight: 800;
    font-size: 1rem;
    margin-bottom: 6px;
}

.info-card-text {
    color: #475569;
    font-size: 0.92rem;
    line-height: 1.45;
}

.metric-grid {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 12px;
    margin: 18px 0 10px 0;
}

.metric-card {
    background: #ffffff;
    border: 1px solid #dbeafe;
    border-radius: 16px;
    padding: 14px 16px;
    box-shadow: 0 8px 18px rgba(30, 64, 175, 0.06);
}

.metric-label {
    color: #64748b;
    font-size: 0.78rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    margin-bottom: 5px;
}

.metric-value {
    color: #0f172a;
    font-size: 0.98rem;
    font-weight: 800;
    line-height: 1.25;
    overflow-wrap: anywhere;
}

.small-note {
    color: #64748b;
    font-size: 0.88rem;
    line-height: 1.45;
}

div.stButton > button:first-child {
    background: #2563eb;
    color: white;
    border: 1px solid #1d4ed8;
    border-radius: 12px;
    font-weight: 700;
    padding: 0.65rem 1rem;
}

div.stButton > button:first-child:hover {
    background: #1d4ed8;
    color: white;
    border: 1px solid #1e40af;
}

textarea {
    border-radius: 12px !important;
}

[data-testid="stExpander"] {
    border: 1px solid #dbeafe;
    border-radius: 14px;
    background: #ffffff;
[data-testid="stMarkdownContainer"] table {
    display: block;
    overflow-x: auto;
    white-space: normal;
    width: 100%;
    max-width: 100%;
    border-collapse: collapse;
}

[data-testid="stMarkdownContainer"] th,
[data-testid="stMarkdownContainer"] td {
    min-width: 140px;
    vertical-align: top;
}

[data-testid="stMarkdownContainer"] th {
    background: #eff6ff;
}

[data-testid="stMarkdownContainer"] td {
    background: #ffffff;
}

@media (max-width: 900px) {
    .metric-grid {
        grid-template-columns: repeat(2, minmax(0, 1fr));
    }

    .hero-title {
        font-size: 1.8rem;
    }
}

@media (max-width: 560px) {
    .metric-grid {
        grid-template-columns: 1fr;
    }
}
</style>
""",
        unsafe_allow_html=True,
    )


def render_hero() -> None:
    st.markdown(
        """
<div class="hero-card">
    <div class="hero-title">AI Job Application Assistant</div>
    <div class="hero-subtitle">
        Evidence-based role fit, CV review, and application strategy.
        Compare a job description with a CV, separate direct vs adjacent evidence,
        identify risky claims, and generate a truthful application plan.
    </div>
    <div class="pill-row">
        <span class="pill">Role fit scoring</span>
        <span class="pill">CV evidence audit</span>
        <span class="pill">Recruiter message risk check</span>
        <span class="pill">Portfolio artifact roadmap</span>
    </div>
</div>
""",
        unsafe_allow_html=True,
    )


def render_mode_cards() -> None:
    col1, col2 = st.columns(2)

    with col1:
        st.markdown(
            """
<div class="info-card">
    <div class="info-card-title">Demo mode</div>
    <div class="info-card-text">
        Explore pre-generated examples without using API credits. No password required.
    </div>
</div>
""",
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            """
<div class="info-card">
    <div class="info-card-title">Live analysis</div>
    <div class="info-card-text">
        Paste your own CV and job description. Password required. Guest access has a daily limit.
    </div>
</div>
""",
            unsafe_allow_html=True,
        )


# -------------------------------------------------
# Output rendering helpers
# -------------------------------------------------

def normalize_markdown_line(line: str) -> str:
    """Remove common markdown formatting from one line."""
    line = line.strip()
    line = re.sub(r"^#+\s*", "", line)
    line = re.sub(r"^[-*]\s*", "", line)
    line = re.sub(r"^\d+[\).]\s*", "", line)
    line = line.replace("**", "")
    line = line.replace("__", "")
    line = line.replace("`", "")
    return line.strip()


def clean_summary_value(value: str) -> str:
    """Clean extracted summary values."""
    if not value:
        return "—"

    value = normalize_markdown_line(value)
    value = value.strip(" :-–—")

    # If the value itself is written as "Recommendation: No",
    # keep only the part after the colon.
    if ":" in value:
        left, right = value.split(":", 1)
        known_embedded_labels = {
            "score",
            "overall match score",
            "match score",
            "category",
            "role fit",
            "role fit category",
            "recommendation",
            "final recommendation",
            "application effort recommendation",
            "effort",
        }
        if left.strip().lower() in known_embedded_labels:
            value = right.strip()

    return value.strip() or "—"


def find_exact_label_values(markdown_text: str, labels: list[str]) -> list[str]:
    """Find values for exact labels only.

    Supports:
    - Label: value
    - Label - value
    - heading/standalone label followed by value on the next non-empty line

    Avoids false matches like:
    - Recommendation consistency check
    - Score 41 typically points to...
    """
    lines = markdown_text.splitlines()
    normalized_lines = [normalize_markdown_line(line) for line in lines]
    values = []

    for i, clean_line in enumerate(normalized_lines):
        if not clean_line:
            continue

        for label in labels:
            label_pattern = re.escape(label)

            # Case 1: exact "Label: value"
            colon_match = re.match(
                rf"^{label_pattern}\s*:\s*(.+)$",
                clean_line,
                flags=re.IGNORECASE,
            )
            if colon_match:
                values.append(clean_summary_value(colon_match.group(1)))
                continue

            # Case 2: exact "Label - value"
            dash_match = re.match(
                rf"^{label_pattern}\s*[-–—]\s*(.+)$",
                clean_line,
                flags=re.IGNORECASE,
            )
            if dash_match:
                values.append(clean_summary_value(dash_match.group(1)))
                continue

            # Case 3: heading/standalone label, value on next non-empty line
            exact_label_match = re.match(
                rf"^{label_pattern}$",
                clean_line,
                flags=re.IGNORECASE,
            )
            if exact_label_match:
                for next_clean_line in normalized_lines[i + 1:]:
                    if next_clean_line:
                        values.append(clean_summary_value(next_clean_line))
                        break

    return values


def pick_first_value(markdown_text: str, labels: list[str]) -> str:
    values = find_exact_label_values(markdown_text, labels)
    if not values:
        return "—"
    return values[0]


def pick_last_value(markdown_text: str, labels: list[str]) -> str:
    values = find_exact_label_values(markdown_text, labels)
    if not values:
        return "—"
    return values[-1]


def normalize_score(score_raw: str) -> str:
    if not score_raw or score_raw == "—":
        return "—"

    score_match = re.search(r"(\d{1,3})\s*/\s*100", score_raw)
    if score_match:
        return f"{score_match.group(1)}/100"

    score_number = re.search(r"\b(\d{1,3})\b", score_raw)
    if score_number:
        return f"{score_number.group(1)}/100"

    return clean_summary_value(score_raw)


def extract_score_fallback(markdown_text: str) -> str:
    """Fallback for outputs where score is inside a numbered section."""
    patterns = [
        r"Overall match score[^#]*?Score:\s*(\d{1,3}\s*/\s*100)",
        r"Overall match score[^#]*?(\d{1,3}\s*/\s*100)",
        r"Match score[^#]*?(\d{1,3}\s*/\s*100)",
    ]

    for pattern in patterns:
        match = re.search(pattern, markdown_text, flags=re.IGNORECASE | re.DOTALL)
        if match:
            return normalize_score(match.group(1))

    return "—"


def extract_category_fallback(markdown_text: str) -> str:
    """Fallback for outputs where category is inside a numbered section."""
    patterns = [
        r"Role fit category[^#]*?\*\*([^*\n]+)\*\*",
        r"Role fit category[^#]*?\n\s*([^\n#|]+)",
    ]

    for pattern in patterns:
        match = re.search(pattern, markdown_text, flags=re.IGNORECASE | re.DOTALL)
        if match:
            return clean_summary_value(match.group(1))

    return "—"


def extract_output_summary(markdown_text: str) -> dict:
    """Extract score, category, final recommendation, and effort if present."""
    score_raw = pick_first_value(
        markdown_text,
        [
            "Overall match score from 0 to 100",
            "Overall match score",
            "Match score",
            "Score",
        ],
    )

    score = normalize_score(score_raw)

    if score == "—":
        score = extract_score_fallback(markdown_text)

    category = pick_first_value(
        markdown_text,
        [
            "Role fit category",
            "Role fit",
            "Category",
        ],
    )

    category = clean_summary_value(category)

    if category == "—":
        category = extract_category_fallback(markdown_text)

    recommendation = pick_last_value(
        markdown_text,
        [
            "Final recommendation",
            "Recommendation",
            "Should I apply",
        ],
    )

    effort = pick_last_value(
        markdown_text,
        [
            "Application effort recommendation",
            "Effort",
        ],
    )

    return {
        "Score": score,
        "Category": category,
        "Recommendation": clean_summary_value(recommendation),
        "Effort": clean_summary_value(effort),
    }


def get_meaningful_summary_items(summary: dict) -> dict:
    """Return only summary fields that have real values."""
    return {
        key: value
        for key, value in summary.items()
        if value and value != "—"
    }


def render_summary_cards(markdown_text: str) -> None:
    summary = extract_output_summary(markdown_text)
    summary_items = get_meaningful_summary_items(summary)

    if not summary_items:
        return

    st.markdown("## Result summary")

    columns = st.columns(len(summary_items))

    for column, (label, value) in zip(columns, summary_items.items()):
        with column:
            st.markdown(
                f"""
<div class="metric-card">
    <div class="metric-label">{escape(label)}</div>
    <div class="metric-value">{escape(value)}</div>
</div>
""",
                unsafe_allow_html=True,
            )


def split_markdown_sections(markdown_text: str) -> list[tuple[str, str]]:
    """Split markdown by H1 or H2 headings and avoid empty sections.

    We intentionally do not split by H3, because H3 is usually a subsection
    inside a larger analysis section.
    """
    lines = markdown_text.splitlines()
    sections = []
    current_title = None
    current_lines = []

    heading_pattern = r"^#{1,2}\s+"

    for line in lines:
        if re.match(heading_pattern, line.strip()):
            body = "\n".join(current_lines).strip()

            if current_title and body:
                sections.append((current_title, body))
            elif current_title is None and body:
                sections.append(("Introduction", body))

            current_title = re.sub(heading_pattern, "", line.strip()).strip()
            current_lines = []
        else:
            current_lines.append(line)

    body = "\n".join(current_lines).strip()

    if current_title and body:
        sections.append((current_title, body))
    elif current_title is None and body:
        sections.append(("Detailed output", body))

    if not sections:
        return [("Detailed output", markdown_text.strip())]

    return sections


def render_analysis_output(output_text: str) -> None:
    render_summary_cards(output_text)

    st.download_button(
        label="Download analysis as Markdown",
        data=output_text,
        file_name="job_application_analysis.md",
        mime="text/markdown",
    )

    st.markdown("## Detailed output")

    sections = split_markdown_sections(output_text)

    if len(sections) <= 1:
        with st.expander("View detailed output", expanded=True):
            st.markdown(output_text)
    else:
        for index, (title, body) in enumerate(sections):
            expanded = index == 0
            with st.expander(title, expanded=expanded):
                st.markdown(body)


# -------------------------------------------------
# Access control helpers
# -------------------------------------------------


def initialize_session_state() -> None:
    if "access_level" not in st.session_state:
        st.session_state.access_level = None

    if "last_live_output" not in st.session_state:
        st.session_state.last_live_output = None


def render_access_panel() -> Optional[str]:
    """Render password access panel and return access level: owner, guest, or None."""
    initialize_session_state()

    current_access = st.session_state.get("access_level")

    if current_access == "owner":
        st.success("Owner access unlocked. Live analysis is unlimited.")
        return "owner"

    if current_access == "guest":
        used = get_guest_usage_today()
        remaining = get_guest_remaining_runs()
        st.info(f"Guest access unlocked. Daily guest usage: {used} / {GUEST_DAILY_LIMIT}. Remaining today: {remaining}.")
        return "guest"

    st.markdown("### Live access")
    st.caption("Live analysis uses the OpenAI API and requires a password.")

    with st.form("access_form"):
        password = st.text_input("Enter password", type="password")
        submitted = st.form_submit_button("Unlock live analysis")

    if submitted:
        owner_password = st.secrets.get("OWNER_PASSWORD", "")
        guest_password = st.secrets.get("GUEST_PASSWORD", "")

        if password and password == owner_password:
            st.session_state.access_level = "owner"
            st.success("Owner access unlocked.")
            st.rerun()

        elif password and password == guest_password:
            st.session_state.access_level = "guest"
            st.success("Guest access unlocked.")
            st.rerun()

        else:
            st.error("Incorrect password.")

    return None


def check_guest_quota_before_run() -> bool:
    """Return True if guest can run analysis, otherwise show error and return False."""
    remaining = get_guest_remaining_runs()

    if remaining <= 0:
        st.error("Daily guest limit reached. Please contact the app owner for additional access.")
        return False

    return True


# -------------------------------------------------
# Demo cases
# -------------------------------------------------

ALEX_MORGAN_CV = """
Alex Morgan
Product-oriented finance and analytics professional

Profile:
- Finance and analytics background with product-adjacent experience.
- Strong in stakeholder coordination, business cases, market research, and process improvement.
- Interested in product, operations, and strategy roles where structured thinking and evidence-based decision-making matter.

Experience:
- Launched an internal operations tool that reduced processing time by 35%.
- Coordinated cross-functional initiatives across finance, legal, and operations teams.
- Built a no-code web project and tested SEO and paid acquisition channels.
- Conducted market research, competitor analysis, and business case preparation.
- Supported decision-making with financial modelling, business analysis, and stakeholder presentations.

Skills:
Python, SQL, stakeholder management, market research, prioritization, business modelling, AI-assisted workflows
"""

DEMO_CASES = {
    "Strong fit": {
        "label": "Strong fit",
        "job_title": "Product Operations Manager",
        "description": "Alex applies to a role focused on internal tools, process improvement, stakeholder coordination, and operational analytics.",
        "jd": """
Product Operations Manager

We are looking for a Product Operations Manager to improve internal workflows, coordinate cross-functional initiatives, and support product and operations teams with structured analysis.

The role includes:
- Mapping operational pain points and improving internal processes
- Coordinating with finance, legal, operations, and product stakeholders
- Supporting internal tool requirements and rollout
- Tracking process metrics after launch
- Preparing business cases and prioritization recommendations
- Using structured analysis to support decision-making

Requirements:
- Experience with operations, product operations, or internal process improvement
- Strong stakeholder management
- Analytical thinking and business case preparation
- Comfort working with ambiguity
- Ability to communicate clearly across functions
- Basic data literacy
""",
        "cv": ALEX_MORGAN_CV,
        "output": """
# 1. Job Description Analysis

The role is focused on product operations, internal process improvement, stakeholder coordination, business-case thinking, and post-launch tracking. It does not require deep SaaS PM ownership or quota-carrying sales experience.

# 2. Match Against CV

| Requirement | CV evidence | Match level | Comment |
|---|---|---|---|
| Internal process improvement | Launched an internal operations tool that reduced processing time by 35% | Strong | Directly relevant to the role |
| Cross-functional coordination | Coordinated initiatives across finance, legal, and operations | Strong | Strong stakeholder evidence |
| Business case preparation | Conducted business case preparation and financial modelling | Strong | Directly supports prioritization and decision-making |
| Operational analytics | Supported decisions with analysis and presentations | Partial | Relevant, but metrics examples could be stronger |
| Product operations experience | Internal tool and workflow improvement | Partial to strong | Product-adjacent but credible |

# 3. Application Strategy

Overall match score: 84/100

Role fit category: Strong fit

Final recommendation: Yes

Application effort recommendation: Apply seriously

# 4. CV Tailoring Suggestions

Safe edits:
- Move the internal operations tool bullet higher.
- Add more detail on users, workflow pain point, rollout, and post-launch metric tracking.
- Emphasize cross-functional coordination with finance, legal, operations, and product-like stakeholders.
- Strengthen business-case and prioritization language.

Evidence-dependent edits:
- Add exact user count, adoption, or operational KPIs only if true.
- Add product team collaboration only if Alex directly worked with product stakeholders.

Do-not-add:
- Do not claim formal SaaS Product Manager experience.
- Do not claim engineering delivery ownership unless true.
- Do not claim advanced analytics ownership beyond what the CV supports.

# 5. Final Recommendation

This is a strong fit because the role values exactly the kind of evidence Alex already has: internal process improvement, stakeholder coordination, business-case thinking, and product-adjacent operational delivery.
""",
    },
    "Reasonable stretch": {
        "label": "Reasonable stretch",
        "job_title": "Product Manager, International Expansion",
        "description": "Alex applies to a product role with some aligned experience, but missing direct localization and international launch evidence.",
        "jd": """
Product Manager, International Expansion

We are looking for a Product Manager to lead international market launches.
The role includes market prioritization, localization requirements, payment method analysis,
cross-functional coordination with legal, finance, product, and GTM teams, and post-launch tracking.

Requirements:
- Product management experience
- Cross-functional delivery
- Market research and prioritization
- Localization or internationalization experience
- Comfort with ambiguity
- AI fluency
""",
        "cv": ALEX_MORGAN_CV,
        "output": """
# 1. Job Description Analysis

The role is a Product Manager position focused on international market launches, market prioritization, localization requirements, payment-method analysis, cross-functional delivery, and post-launch tracking.

# 2. Match Against CV

| Requirement | CV evidence | Match level | Comment |
|---|---|---|---|
| Cross-functional delivery | Coordinated initiatives across finance, legal, and operations | Strong adjacent | Relevant operating evidence |
| Market research and prioritization | Conducted market research, competitor analysis, and business case preparation | Partial | Good adjacent evidence |
| Product management experience | Internal operations tool and no-code web project | Partial | Product-adjacent, not classic PM |
| Localization / internationalization | No direct evidence | Missing | Main role-specific gap |
| Payment method analysis | No direct evidence | Missing | Important domain gap |
| AI fluency | AI-assisted workflows listed in skills | Weak | Needs concrete examples |

# 3. Application Strategy

Overall match score: 58/100

Role fit category: Reasonable stretch

Final recommendation: Maybe

Application effort recommendation: Apply with tailored CV

# 4. CV Tailoring Suggestions

Safe edits:
- Emphasize cross-functional delivery across finance, legal, and operations.
- Strengthen the internal tool launch bullet with problem, users, action, and outcome.
- Make market research, competitor analysis, and business-case preparation more visible.
- Add the no-code project as product-adjacent launch evidence.

Evidence-dependent edits:
- Add localization, payment-method, or international launch examples only if true.
- Add concrete AI workflow examples only if Alex can explain what was built or used.

Do-not-add:
- Do not claim direct international expansion experience.
- Do not claim payment-method expertise.
- Do not present AI-assisted workflows as strong evidence without examples.
- Do not imply classic SaaS PM ownership if the evidence is product-adjacent.

# 5. Final Recommendation

This is a reasonable stretch. Alex has credible adjacent evidence in market research, business cases, stakeholder coordination, and product-adjacent launch work, but the CV does not yet prove direct international expansion, localization, or payment-method experience.
""",
    },
    "Poor fit": {
        "label": "Poor fit",
        "job_title": "Account Executive, B2B SaaS",
        "description": "Alex applies to a quota-carrying SaaS sales role where the core hard requirements are missing.",
        "jd": """
Account Executive, B2B SaaS

We are looking for an Account Executive to own new business sales for a B2B SaaS product.
The role includes prospecting, pipeline generation, product demos, negotiation,
procurement processes, and closing new customers.

Requirements:
- 3+ years of B2B SaaS sales experience
- Full-cycle new business sales ownership
- Quota ownership
- Experience closing six-figure annual contracts
- Ability to run product demos and discovery calls
- CRM discipline and pipeline forecasting
- Strong negotiation skills
""",
        "cv": ALEX_MORGAN_CV,
        "output": """
# 1. Job Description Analysis

The role is a specialist Account Executive position focused on quota-carrying B2B SaaS sales. The hard requirements are full-cycle sales ownership, pipeline generation, demos, negotiation, and closing new customers.

# 2. Match Against CV

| Requirement | CV evidence | Match level | Comment |
|---|---|---|---|
| B2B SaaS sales | No direct evidence | Missing | Core requirement is absent |
| Quota ownership | No direct evidence | Missing | Major screening gap |
| Full-cycle new business sales | No direct evidence | Missing | Banking/client work is not the same |
| Product demos | No direct evidence | Missing | Cannot be inferred |
| Negotiation | Stakeholder and client-facing finance work | Weak adjacent | Relevant soft skill, not AE evidence |
| Commercial thinking | Finance, business cases, stakeholder presentations | Strong adjacent | Useful but not enough |

# 3. Application Strategy

Overall match score: 31/100

Role fit category: Weak fit / borderline stretch

Final recommendation: No

Application effort recommendation: Do not apply; use as market research

# 4. CV Tailoring Suggestions

Safe edits:
- Emphasize commercial analysis and client-facing stakeholder work only as adjacent evidence.
- Keep business-case and presentation experience visible.
- Use this JD to understand what sales roles require.

Do-not-add:
- Do not claim B2B SaaS sales experience.
- Do not claim quota ownership.
- Do not claim full-cycle AE experience.
- Do not claim product demo or pipeline ownership.
- Do not convert banking deal execution into SaaS sales closing.

# 5. Final Recommendation

This is not a good target role for Alex based on the current CV. The job belongs to a different job family, and the core hard requirements are missing. It is useful as market research, not as a priority application.
""",
    },
}


def render_demo_page() -> None:
    st.markdown("## Public demo")
    st.markdown(
        '<div class="small-note">Demo mode uses pre-generated examples and does not call the OpenAI API.</div>',
        unsafe_allow_html=True,
    )

    demo_name = st.selectbox("Choose demo case", list(DEMO_CASES.keys()))
    demo = DEMO_CASES[demo_name]

    st.markdown(
        f"""
<div class="info-card">
    <div class="info-card-title">{escape(demo["label"])}: {escape(demo["job_title"])}</div>
    <div class="info-card-text">{escape(demo["description"])}</div>
</div>
""",
        unsafe_allow_html=True,
    )

    with st.expander("Sample job description", expanded=False):
        st.markdown(demo["jd"])

    with st.expander("Sample CV", expanded=False):
        st.markdown(demo["cv"])

    render_analysis_output(demo["output"])

# -------------------------------------------------
# Analysis type descriptions
# -------------------------------------------------

ANALYSIS_TYPE_DESCRIPTIONS = {
    "Full analysis": "Complete workflow: role fit + CV quality + recruiter message + artifact roadmap + final application recommendation.",
    "Role fit only": "Score, category, gaps, job-family fit, direct vs adjacent evidence, and recommendation.",
    "CV quality only": "Truthful CV improvements with safe edits, evidence-dependent edits, do-not-add items, and skills audit.",
    "Artifacts roadmap only": "Portfolio/project artifacts that could close evidence gaps, prioritized by impact and effort.",
    "Recruiter message only": "A cautious outreach message with risk check and safer version when needed.",
}


def render_analysis_type_description(analysis_type: str) -> None:
    description = ANALYSIS_TYPE_DESCRIPTIONS.get(analysis_type)
    if description:
        st.caption(description)


# -------------------------------------------------
# OpenAI client
# -------------------------------------------------

@st.cache_resource
def get_openai_client() -> OpenAI:
    return OpenAI(api_key=st.secrets["OPENAI_API_KEY"])


client = get_openai_client()


# -------------------------------------------------
# Prompt builder
# -------------------------------------------------

def build_prompt(jd_text: str, cv_text: str, analysis_type: str) -> str:
    base_rules = """
You are my AI-assisted job application analyst.

Your task is to analyze a job description against my CV and help me prepare a tailored application.

Your goal is not to make me look like a perfect candidate.
Your goal is to help me make a realistic, evidence-based application decision and generate truthful positioning drafts that I will manually review and edit.

# Important Rules

- Do not invent experience.
- Do not exaggerate my background.
- Do not turn adjacent or transferable experience into direct experience.
- Do not describe me as having experience in a domain unless it is explicitly supported by my CV.
- Separate evidence-based matches from assumptions.
- Be critical, specific, and realistic.
- If something is missing from my CV, mark it as a gap or risk.
- Write suggestions as drafts that I can manually review and edit.
- Do not write final application materials as if they are ready to send without human review.
- Do not optimize only for “sounding impressive.” Optimize for truthful, relevant, evidence-based positioning.

# Evidence and Hallucination Control Rules

For every claimed match, recommendation, or positioning suggestion:

- Cite the exact CV evidence used.
- If there is no direct CV evidence, write: “No direct evidence in CV.”
- Separate direct evidence from adjacent or transferable evidence.

Definitions:

- Direct evidence = my CV clearly shows that I have done this exact thing.
- Adjacent evidence = my CV shows that I have done something similar or transferable, but not the same.
- No evidence = the claim is not supported by my CV.

Be especially strict with role-critical experience areas.

Before matching my CV to the job description, identify the domains, responsibilities, tools, seniority signals, and operating contexts that are central to this specific role.

For each role-critical area:
- Do not infer direct experience from adjacent experience.
- Do not convert keywords into proof of experience.
- If my CV does not show direct evidence, mark it as Partial, Weak, or Missing.
- If the area defines the role, treat missing evidence as a serious screening risk.

Examples of role-critical areas may include, depending on the job:
- Product management
- SaaS
- Internationalization / localization
- GTM collaboration
- Payments / processing
- Payroll / equity administration
- Compliance / audit readiness
- Data analytics / experimentation
- AI workflows
- People management
- Startup or scale-up experience
- Specific tools or systems mentioned in the JD

Do not treat this example list as fixed. Build the strictness list from the actual job description.

For each match and recommendation, include a confidence level:

- High = clearly supported by direct CV evidence.
- Medium = supported by adjacent or transferable evidence.
- Low = weakly supported or mostly inferred.
- No evidence = not supported by the CV.

If a requirement is important for the role but not clearly supported by my CV, do not hide it.
Mark it as a risk and suggest how to address it honestly.

# Decision Rules

Use strict decision logic for the final recommendation.

Recommendation options:

- Yes = strong or reasonable evidence-based fit. The CV shows direct evidence for most core requirements.
- Maybe = there are meaningful direct or adjacent matches, and the gaps are not central to the role or can be honestly bridged.
- No = the candidate is missing several core hard requirements, especially if those requirements define the role itself.

Do not use “Maybe” as a polite replacement for “No”.

Use these thresholds:

- If overall match score is below 40/100, default recommendation should be “No”.
- If overall match score is 40–59/100, recommendation can be “Maybe” only if the candidate has strong adjacent evidence for the core responsibilities.
- If overall match score is 60–74/100, recommendation can be “Maybe” or “Yes, if tailored”, depending on the gaps.
- If overall match score is 75+/100, recommendation can be “Yes” if there are no severe core gaps.

Core requirement rule:

If the candidate is missing 2 or more core hard requirements that define the role, the recommendation should be “No” unless there is unusually strong adjacent evidence.

Specialist-role rule:

If the role is a specialist role and the candidate has no direct evidence in that specialty, the recommendation should usually be “No” or “No, unless intentionally exploring a career pivot.”

For “No” recommendations, still provide:
- what could be learned from the analysis
- whether the role is useful as market research
- what artifacts or skills could improve fit for similar future roles

If a skill is only listed in the Skills section but is not supported by experience bullets, projects, outcomes, metrics, or concrete examples, mark it as “Mentioned but weakly evidenced.” Do not treat it as strong evidence.

For final application recommendations, include an “Application effort recommendation”:
- Apply seriously
- Apply only with light tailoring
- Do not apply; use as market research
- Do not apply; irrelevant role

# Scoring and Estimation Rules

When assigning numeric scores, use realistic judgment based on:
- the job description requirements
- the strength of CV evidence
- how visible the artifact would be to recruiters
- whether the artifact creates proof, not just knowledge
- likely effort, time, and cost
- whether the artifact helps only this role or a broader set of target roles

Do not inflate scores to make recommendations look attractive.

For resume artifacts:

Reach:
- 1–3 = useful only for a narrow niche or one specific role
- 4–6 = useful for several adjacent roles
- 7–10 = useful across many target roles

Impact:
- 1–3 = minor improvement to CV positioning
- 4–6 = moderate improvement or useful supporting signal
- 7–8 = strong visible proof for an important gap
- 9–10 = major proof for a role-critical gap

Confidence:
- 0.1–0.3 = speculative; unclear whether it will help
- 0.4–0.6 = plausible but uncertain
- 0.7–0.8 = likely to help based on JD/CV fit
- 0.9–1.0 = very likely to help and clearly relevant

Effort:
- Use estimated effort in days.
- Minimum effort = 0.5 days.
- Penalize artifacts that take too long or produce weak visible proof.

RICE score:
RICE = (Reach × Impact × Confidence) / Effort

Always sort RICE outputs from highest to lowest score.

# Job-Family and Recommendation Calibration Rules

JD interpretation discipline:
- Do not infer a higher seniority level, title, or scope than the job description explicitly supports.
- If the job description says “Product Manager,” do not upgrade it to “Senior Product Manager,” “Head of Product,” “Principal PM,” or equivalent unless those exact words or clearly equivalent scope are explicitly present in the JD.
- If the JD says “Senior Product Manager,” apply senior-role caution, but do not upgrade it further to Head of Product / Principal PM unless explicitly supported.
- Hidden evaluation criteria may be inferred, but they must stay close to the JD wording and must not change the role type.
- Do not invent requirements such as TAM ownership, Head of Product scope, Principal PM scope, years-long strategy ownership, or management consulting background unless they are explicitly present or strongly implied by the JD text.
- If you infer a hidden criterion, label it as inferred and keep it secondary to explicit requirements.
- The core role definition must be based on the JD’s actual wording, not on assumptions about what a similar role might require.


Before assigning the final score, category, and recommendation, assess job-family fit.

Identify:
- Target job family from the job description
- Candidate's current job family based on CV evidence
- Whether the fit is: Same / Adjacent / Different
- Whether the role is specialist, senior, or generalist
- Whether the candidate is missing role-defining hard requirements

Examples of job families:
- Product management
- Product operations / program management
- Product analytics
- Business / strategy / operations
- Finance / banking / investment / valuation
- Software engineering
- Data science / machine learning
- IT support / sysadmin / infrastructure
- HR / payroll / people operations
- Sales / customer success / GTM
- Design / UX research

Same or adjacent job-family stretch rule:
- If the role belongs to the same or adjacent job family as the CV, and the CV shows strong evidence for several core operating capabilities, do not default to “No” solely because one or two domain-specific requirements are missing.
- For product roles, do not treat candidates with credible product-adjacent work as a different job family if the CV shows evidence such as product-like initiatives, business-case ownership, stakeholder delivery, prioritization, user/customer research, launches, internal tools, process improvement, or market/competitor analysis.
- For finance / business / analytics / strategy profiles applying to product roles, classify the fit as “Adjacent” rather than “Different” if there is credible product-like operating evidence.
- For adjacent product/business/finance → product roles, do not push the score below 45 solely because the candidate lacks a formal PM title, if the CV shows credible evidence of launches, prioritization, stakeholder alignment, business cases, user/customer research, or product-adjacent ownership.
- For same or adjacent job-family roles, 45–59 usually means “Maybe / apply only with tailored CV,” unless the missing requirement is an absolute legal, technical, certification, scale, seniority, or domain screen.
- For same or adjacent job-family roles, 60–74 usually means “Reasonable stretch / apply with tailored CV.”
- “Do not apply; use as market research” should be reserved for roles where the candidate lacks the target job family, lacks most role-defining hard requirements, or where the seniority/domain gap is too large.
- This stretch rule does not apply when the role is a specialist senior product role requiring direct evidence of high-scale revenue surface ownership, deep SaaS PM experience, technical specifications, engineering delivery pipelines, or other role-defining experience that the CV clearly lacks.

Role fit category calibration:
- 0–29: Not a fit / clear mismatch
- 30–44: Weak fit / borderline stretch
- 45–59: Reasonable stretch if the role is same or adjacent job family and several core operating capabilities are evidenced
- 60–74: Good stretch / apply with tailored CV
- 75+: Strong fit

For adjacent product/business/finance → product roles:
- If the CV shows credible product-like evidence, commercial reasoning, stakeholder delivery, prioritization, launches, or business-case ownership, avoid scoring below 45 unless the JD requires senior/specialist product experience that is clearly missing.
- If the role is senior/specialist and several role-defining senior requirements are missing, 30–44 may be appropriate.
Do not use “Reasonable stretch” if the candidate is missing several role-defining hard requirements, even if some adjacent evidence exists.

Recommendation consistency:
The final recommendation must be consistent with the score and role fit category.

Typical mapping:
- 0–29: No / do not apply; use as market research
- 30–44: Usually No, or low-priority Maybe only if there is a specific strategic reason
- 45–59: Maybe / apply with tailored CV if same or adjacent job family
- 60–74: Reasonable stretch / apply with tailored CV
- 75+: Yes / apply seriously

For same or adjacent product roles:
- 45–59 should usually produce “Maybe,” not “No,” unless the JD has senior/specialist requirements that the CV clearly lacks.
- If the score is 45–59 and the recommendation is “No,” explicitly explain which role-defining requirement makes the application not worth pursuing.

If the final recommendation differs from this mapping, explicitly explain why.

If final recommendation is “No,” avoid labeling the role as “Reasonable stretch” unless there is a specific strategic reason to apply anyway.

Skills-only evidence rule:
- If a skill is only listed in the Skills section but is not supported by experience bullets, projects, outcomes, metrics, or concrete examples, mark it as “Mentioned but weakly evidenced.”
- Do not treat skills-only evidence as a strong direct match.
- Do not use skills-only evidence as a major claim in profile summaries, recruiter messages, or final positioning unless clearly qualified.
- For example, if “AI-assisted workflows” appears only in Skills, do not write that the candidate has strong practical AI workflow experience. Instead say: “AI is mentioned, but concrete examples should be added.”

CV editing evidence rules:
- Separate CV improvement advice into three categories:
  1. Safe edits: changes that can be made using evidence already present in the CV.
  2. Evidence-dependent edits: changes that should only be made if the candidate can truthfully support them with real examples.
  3. Do-not-add items: requirements from the JD that should not be added or implied because the CV does not support them.
- Do not suggest adding claims that would misrepresent the candidate’s experience.
- Do not turn adjacent evidence into direct evidence.
- Do not convert finance, analysis, consulting, or project coordination experience into formal product management experience unless the CV directly supports that.
- Do not suggest adding GTM, technical specifications, engineering delivery, people management, startup employment, SaaS PM, or AI workflow expertise unless there is concrete CV evidence or the recommendation is explicitly marked as evidence-dependent.
- When suggesting CV bullets, label whether each suggestion is:
  - Safe based on current CV
  - Evidence-dependent
  - Not safe unless additional proof exists
- If a skill appears only in the skills section, recommend either adding concrete evidence, moving it lower, or removing/softening it.
- End CV-related sections with a short list of maximum 5 minimum viable CV changes before applying.

Senior-role caution:
- For senior roles, be stricter about direct evidence of senior-level ownership, product scope, scale, people management, technical depth, or domain depth.
- If a senior role requires direct experience that the CV lacks, the recommendation should be conservative.
- Recruiter messages for senior roles should avoid presenting the candidate as a direct fit unless the CV strongly supports the senior-level requirements.

No follow-up offers:
- Do not end the response with offers such as “If you want, I can…”, “I can next…”, “Would you like me to…”, or similar.
- The output must be complete as a standalone analysis.
- Do not suggest that the assistant can continue the task in a later message.
- If additional work would be useful, include it as a concrete recommendation inside the current output, not as a conversational follow-up offer.
- Do not include meta-conversational endings.

"""

    inputs = f"""
# Inputs

## Job Description

{jd_text}

## My CV

{cv_text}
"""

    if analysis_type == "Role fit only":
        task = """
# Task: Role Fit Analysis Only

Analyze the job description against my CV.

Important:
Base the role interpretation strictly on the actual JD wording.
Do not upgrade the role to a higher title, seniority, or scope than the JD states.
If the JD says Product Manager, do not call it Senior PM, Head of Product, or Principal PM unless the JD explicitly says so.

Output:

1. Job description hard requirements
2. Job description soft requirements
3. Keywords and domain signals
4. Role-critical strictness areas

For role-critical strictness areas, identify 5–10 areas where the model must be especially strict because exaggerating them would create a misleading application.

Output this table:

| Strictness area | Why it is role-critical | What counts as direct evidence | What counts only as adjacent evidence |

5. Match table with these columns:

| Requirement / responsibility | Direct CV evidence | Adjacent / transferable CV evidence | Match level: Strong / Partial / Weak / Missing | Confidence: High / Medium / Low / No evidence | Comment | Risk if not addressed |

6. Strongest direct matches
7. Strongest adjacent matches
8. Biggest gaps

9. Job-family fit assessment

Output:

| Item | Assessment |
|---|---|
| Target job family | ... |
| Candidate's current job family based on CV | ... |
| Same / Adjacent / Different | ... |
| Specialist / seniority notes | ... |
| Role-defining hard requirements missing | ... |
| Score penalty applied | ... |

10. Overall match score from 0 to 100

When assigning the score, apply:
- Job-family penalty
- Same or adjacent job-family stretch rule
- Senior-role caution
- Skills-only evidence rule
- Recommendation consistency rules

11. Role fit category

Use this calibration:

- 0–29: Not a fit / clear mismatch
- 30–44: Weak fit / borderline stretch
- 45–59: Reasonable stretch if the role is same or adjacent job family and several core operating capabilities are evidenced
- 60–74: Good stretch / apply with tailored CV
- 75+: Strong fit

For adjacent product/business/finance → product roles:
- If the CV shows credible product-like evidence, commercial reasoning, stakeholder delivery, prioritization, launches, or business-case ownership, avoid scoring below 45 unless the JD requires senior/specialist product experience that is clearly missing.
- If the role is senior/specialist and several role-defining senior requirements are missing, 30–44 may be appropriate.

Do not use “Reasonable stretch” if the candidate is missing several role-defining hard requirements, even if some adjacent evidence exists.
But do not downgrade a same/adjacent product role to “No / market research only” solely because the candidate lacks a formal PM title, if there is credible product-adjacent operating evidence.

12. Final recommendation

Output:
- Recommendation: Yes / Maybe / No
- Application effort recommendation:
  - Apply seriously
  - Apply with tailored CV
  - Apply only with light tailoring
  - Low-priority stretch application
  - Do not apply; use as market research
  - Do not apply; irrelevant role
- Explain why the recommendation is consistent with the score and role fit category.
- If the recommendation differs from the normal score mapping, explain why.
- State what can be learned from the role if the recommendation is No.
- State what artifacts or skills could improve fit for similar future roles.

Be strict but fair.
Do not use Maybe as a polite replacement for No.
Do not use No if the role is a same/adjacent job-family reasonable stretch with credible operating evidence, unless the missing requirements are role-defining.
"""

    elif analysis_type == "CV quality only":
        task = """
# Task: CV Quality Review Only

Review my CV against the job description.

Do not assess whether I should apply in detail. Focus on CV quality, truthfulness, positioning, ATS clarity, and evidence strength.

Output:

1. Overall CV positioning

Explain:
- What job family the CV currently signals
- What job family the JD is targeting
- Whether the CV positioning is aligned, adjacent, or mismatched
- Whether the CV risks looking over-positioned or under-positioned for this role

2. Strongest CV evidence for this JD

Output a table:

| Evidence from CV | What it supports in the JD | Evidence type: Direct / Adjacent / Skills-only | Strength: Strong / Partial / Weak | How to use it safely |

3. Weak or missing evidence

Output a table:

| JD requirement | Current CV evidence | Problem | Risk | Safe action |

4. Skills audit table

Review the Skills section critically.

Output a table:

| Skill | Keep / Remove / Move lower / Support with evidence | Evidence in CV | Risk if left unsupported | Recommended action |

Be especially strict with:
- AI-assisted workflows
- Roadmapping
- A/B tests
- Funnel / cohort analysis
- UX & Design
- Wireframing / Prototyping
- Agile / Scrum
- GTM
- Technical specifications
- Engineering delivery
- People management
- SaaS / fintech PM
- Startup experience

5. Safe edits

List CV edits that can be made using evidence already present in the CV.

For each edit, output:
- Current issue
- Suggested change
- Why it is safe
- Example wording

6. Evidence-dependent edits

List edits that may improve the CV but should only be added if true.

For each edit, output:
- Potential improvement
- What real evidence is needed
- Why it matters for the JD
- Example wording if true
- Warning if not true

7. Do-not-add items

List JD-related claims that should NOT be added or implied unless the candidate has real evidence.

Output a table:

| Do not add / imply | Why it would be misleading | What can be said instead, if anything |

8. Bullet rewrite suggestions

Suggest 5–8 improved CV bullets.

For each bullet:
- Original area / role
- Suggested bullet
- Evidence status: Safe / Evidence-dependent / Not safe without proof
- Why it improves the CV
- Risk / caution

Use truthful, non-inflated language.
Do not make the candidate sound like they have direct experience they do not have.

9. Professional summary review

Output:
- Problems with current summary
- Conservative rewritten summary
- Stronger rewritten summary
- Which one to use and why
- What not to say in the summary

10. ATS and readability review

Cover:
- Structure
- Keywords
- Missing explicit requirements
- Overloaded skills
- Ambiguous titles
- Metrics clarity
- Formatting risks

11. Minimum viable CV changes before applying

Give maximum 5 changes.

Each item should be concrete and actionable.
Separate:
- Must do before applying
- Nice to have if time allows

12. Final CV quality verdict

Answer:
- Is the CV safe to use as-is?
- Is light tailoring enough?
- Is substantial tailoring needed?
- Is the CV at risk of overclaiming?
- What is the single highest-leverage improvement?
"""

    elif analysis_type == "Artifacts roadmap only":
        task = """
# Task: Resume Artifact Roadmap Only

Formatting rule:
Avoid extremely wide tables when possible. If a table would need more than 6 columns, split it into two smaller tables or use compact bullets. The output should remain readable in a web app.

Based on the job description, my CV, and the identified gaps, suggest practical resume-strengthening artifacts that could improve my positioning for this role or similar roles.

Artifacts can include:

- Small portfolio projects
- AI-assisted workflows
- Streamlit apps
- Case studies
- Product teardown documents
- Market research documents
- Analytics dashboards
- SQL / Python projects
- No-code prototypes
- Courses or certificates
- Tool-specific learning
- Domain-specific learning
- Writing samples
- Public GitHub projects
- Portfolio website pages
- LinkedIn posts or articles
- Interview preparation assets

Important rules:

- Prioritize practical artifacts over passive learning.
- Do not suggest large projects that would take months unless the expected impact is very high.
- Prefer artifacts that can be completed in 1–7 days.
- Prefer artifacts that produce visible proof: GitHub repo, README, screenshot, demo, dashboard, case study, or portfolio page.
- Do not recommend generic courses unless they clearly address a role-critical gap.
- Do not suggest learning for the sake of learning.
- Be realistic about effort and impact.
- If a gap cannot realistically be closed quickly, say so.
- Separate “quick credibility boosters” from “longer-term development.”
- Do not suggest artifacts that would be misleading, unethical, or likely to result in exaggerated claims.

## 1. Gap-to-Artifact Mapping

Output:

| Gap / weak area | Suggested artifact | Artifact type | What it would prove | Time estimate | Effort level: Low / Medium / High | Money cost estimate | Resume impact: 1–10 | Confidence: High / Medium / Low |

## 2. RICE Prioritization for Resume Artifacts

Assign numeric values using the Scoring and Estimation Rules.

Use:

- Reach: 1–10
- Impact: 1–10
- Confidence: 0.1–1.0
- Effort: estimated effort in days, minimum 0.5

Calculate:

RICE score = (Reach × Impact × Confidence) / Effort

Output:

| Artifact | Reach | Impact | Confidence | Effort days | RICE score | Priority: High / Medium / Low | Reasoning |

Sort artifacts by RICE score from highest to lowest.

## 3. Top 3 Recommended Artifacts

For each, include:

- What to build or complete
- Why it is relevant to this role
- Which CV gap it addresses
- Expected output / proof
- How to describe it in CV
- Estimated time
- Estimated money cost
- Expected resume impact: 1–10
- Risk of over-investing
- Minimum viable version

## 4. Skills / Tools / Competencies to Acquire

Output:

| Skill / tool / competency | Why it matters for this role | Best way to learn it | Time estimate | Money cost | Resume impact: 1–10 | Priority |

Include only skills that are relevant to the job description and my current gaps.

## 5. What Not to Do

Output:

| Not worth doing | Why | Better alternative |

## 6. Recommended 7-Day Action Plan

Output:

| Day | Action | Output | Time box |

## 7. Final Artifact Recommendation

End with:

1. Best quick-win artifact
2. Best medium-effort artifact
3. Best long-term skill investment
4. What I should add to CV after completing the artifact
5. What I can mention in an interview
6. What would be overkill
"""

    elif analysis_type == "Recruiter message only":
        task = """
# Task: Recruiter Message Only

Write a concise recruiter outreach message based strictly on the job description and CV evidence.

Before writing the message, silently assess:
- Whether the role is a strong fit, reasonable stretch, weak fit, or mismatch
- Whether the role is senior or specialist
- Whether the CV lacks several role-defining hard requirements
- Whether the message should position the candidate as a direct fit, adjacent fit, or exploratory candidate

Output:

1. Recruiter message, 80–130 words

The message must:
- Be honest and non-misleading
- Use only claims supported by the CV
- Do not use evidence-dependent claims unless the CV already clearly supports them
- Do not use skills-only claims as major selling points
- Avoid overstating direct experience
- Avoid implying formal experience that is not evidenced
- Avoid turning adjacent experience into direct experience
- Be appropriately cautious for senior or specialist roles
- If the role is senior and the CV lacks core hard requirements, explicitly avoid presenting the candidate as a direct fit
- If useful, frame the message as interest in this or adjacent roles
- If a skill is only listed in Skills and not supported by experience/project bullets, do not use it as a major claim

2. Message Risk Check

Output:
- Any claim that may be too strong
- Any missing evidence
- Any phrase that should be softened
- Whether the message is safe to send as-is or needs manual editing

3. Optional safer version

If the first message is potentially too strong, provide a safer version.
"""

    else:
        task = """
# Task: Full Job Application Analysis

Run the full job application analysis.

Important:
Base the role interpretation strictly on the actual JD wording.
Do not upgrade the role to a higher title, seniority, or scope than the JD states.
If the JD says Product Manager, do not call it Senior PM, Head of Product, or Principal PM unless the JD explicitly says so.
Hidden evaluation criteria may be inferred, but they must stay close to the JD wording and must not change the role type.

Include:

1. Job Description Analysis
   - Hard requirements
   - Soft requirements
   - Core responsibilities
   - Keywords and phrases
   - Domain signals
   - Hidden evaluation criteria
   - Role-critical strictness areas

For role-critical strictness areas, identify 5–10 areas where the model must be especially strict because exaggerating them would create a misleading application.

Output this table:

| Strictness area | Why it is role-critical | What counts as direct evidence | What counts only as adjacent evidence |

2. Match Against My CV
   Create a table:
   | Requirement / responsibility | Direct CV evidence | Adjacent / transferable CV evidence | Match level: Strong / Partial / Weak / Missing | Confidence | Comment | Risk if not addressed |

3. Application Strategy
   - Job-family fit assessment:
     - Target job family
     - Candidate's current job family based on CV evidence
     - Same / Adjacent / Different
     - Specialist / seniority / domain-gap notes
     - Score penalty applied, if any
   - Overall match score
   - Role fit category
   - Check whether score, category, final recommendation, and application effort are consistent
   - Strongest 5 matches
   - Most important gaps or risks
   - Positioning strategy

4. CV Tailoring Suggestions

Provide CV tailoring advice with strict evidence discipline.

Include:

A. Safe edits
- Changes that can be made using evidence already present in the CV
- For each: current issue, suggested change, why it is safe, example wording

B. Evidence-dependent edits
- Changes that may improve fit but should only be added if the candidate can truthfully support them
- For each: what evidence is needed, why it matters, example wording if true, warning if not true

C. Do-not-add items
- JD-related claims that should not be added or implied because the CV does not support them

Output this table:

| Do not add / imply | Why it would be misleading | What can be said instead, if anything |

D. 5–8 specific bullet rewrite suggestions

For each bullet:
- Original area / role
- Suggested bullet
- Evidence status: Safe / Evidence-dependent / Not safe without proof
- Why it improves the CV
- Risk / caution

E. What to add, remove, or de-emphasize
- What to add if true
- What to remove or soften
- What to move lower

5. CV Quality and ATS Review

Cover:

A. Structure and readability
- Is the CV readable?
- Does the structure support the target role?
- Are role titles clear and not misleading?

B. ATS and formatting risks
- Missing explicit requirements from the JD
- Ambiguous titles
- Unsupported keywords
- Overloaded skills section
- Formatting or section-order risks

C. Skills audit table

Output:

| Skill | Keep / Remove / Move lower / Support with evidence | Evidence in CV | Risk if left unsupported | Recommended action |

D. Professional summary review
- Problems with the current summary
- Conservative rewritten summary
- Stronger rewritten summary
- Which version to use and why
- What not to say

E. Experience bullet quality review using XYZ logic
- Which bullets are already strong
- Which bullets need clearer action / method / outcome
- Which bullets risk overclaiming
- Which bullets should be more product/business/role-specific

F. Keyword and skills alignment
- Strong keywords supported by evidence
- Weak keywords that are skills-only
- Missing keywords that can be added only if true
- Keywords that should not be added

G. Company context check
- Whether company/role context supports the target role
- Whether personal projects are being framed transparently
- Whether large-company, startup, SaaS, fintech, or product-company experience is supported or only adjacent

H. Minimum viable CV changes before applying
Give maximum 5 changes.
Separate:
- Must do before applying
- Nice to have if time allows

I. Final CV quality verdict
- Safe to use as-is?
- Light tailoring enough?
- Substantial tailoring needed?
- Risk of overclaiming?
- Highest-leverage improvement

6. Tailored Profile Summary
   - Conservative version
   - Stronger positioning version
   - Recommendation on which version to use

7. Recruiter Message
   - 80–120 word message
   - Message risk check

8. Interview Talking Points
   Generate 5–7 talking points:
   | Talking point | What I should say | CV evidence | Evidence type | Confidence | What question this could answer | Risk / caution |

9. Final Application Recommendation
   - Should I apply?
   - Final recommendation: Yes / Maybe / No
   - Application effort recommendation:
     - Apply seriously
     - Apply with tailored CV
     - Apply only with light tailoring
     - Low-priority stretch application
     - Do not apply; use as market research
     - Do not apply; irrelevant role
   - Explain why the final recommendation is consistent with the score and role fit category
   - If the recommendation differs from the normal score mapping, explain why
   - Why?
   - Should I tailor my CV before applying?
   - Top 3 changes before applying
   - What to emphasize in recruiter message
   - What to prepare for in interview
   - What not to claim
   - Biggest screening risk
   - Most honest and strongest positioning angle

10. Resume Artifact Roadmap
   - Gap-to-artifact mapping
   - Numeric RICE prioritization using Reach, Impact, Confidence, Effort days, and RICE score, sorted from highest to lowest
   - Top 3 recommended artifacts
   - Skills/tools/competencies to acquire
   - What not to do
   - Recommended 7-day action plan
   - Final artifact recommendation
"""

    return base_rules + inputs + task


# -------------------------------------------------
# OpenAI API call
# -------------------------------------------------

def analyze_application(jd_text: str, cv_text: str, analysis_type: str) -> str:
    """Run the live OpenAI analysis and return markdown output."""
    prompt = build_prompt(jd_text, cv_text, analysis_type)

    response = client.responses.create(
        model=MODEL_NAME,
        input=prompt,
    )

    output_text = getattr(response, "output_text", None)

    if not output_text:
        raise ValueError("OpenAI returned an empty response.")

    return output_text

# -------------------------------------------------
# Streamlit UI
# -------------------------------------------------

inject_custom_css()
initialize_session_state()

render_hero()
render_mode_cards()

app_mode = st.radio(
    "Choose mode",
    ["Demo mode", "Live analysis"],
    horizontal=True,
)

if app_mode == "Demo mode":
    render_demo_page()

else:
    access_level = render_access_panel()

    if access_level is None:
        st.stop()

    # Stop guest users early if the daily quota is already exhausted.
    # We also check again before the API call as a safety check.
    if access_level == "guest" and get_guest_remaining_runs() <= 0:
        st.error("Daily guest limit reached. Please contact the app owner for additional access.")
        st.stop()

    st.markdown("## Live analysis")
    st.caption("Paste a job description and CV. Live analysis uses the OpenAI API.")

    analysis_type = st.selectbox(
        "Analysis type",
        [
            "Full analysis",
            "Role fit only",
            "CV quality only",
            "Artifacts roadmap only",
            "Recruiter message only",
        ],
    )

    render_analysis_type_description(analysis_type)

    col1, col2 = st.columns(2)

    with col1:
        jd_text = st.text_area(
            "Job description",
            height=400,
            placeholder="Paste the job description here...",
        )

    with col2:
        cv_text = st.text_area(
            "CV",
            height=400,
            placeholder="Paste the CV here...",
        )

    run_button = st.button("Run live analysis")

    if run_button:
        if not jd_text.strip() or not cv_text.strip():
            st.warning("Please paste both the job description and the CV before running the analysis.")
            st.stop()

        if len(jd_text) > MAX_JD_CHARS:
            st.error(
                f"Job description is too long for this demo. "
                f"Limit: {MAX_JD_CHARS} characters."
            )
            st.stop()

        if len(cv_text) > MAX_CV_CHARS:
            st.error(
                f"CV is too long for this demo. "
                f"Limit: {MAX_CV_CHARS} characters."
            )
            st.stop()

        # Safety check immediately before the API call.
        if access_level == "guest" and not check_guest_quota_before_run():
            st.stop()

        try:
            with st.spinner("Running evidence-based analysis..."):
                output_text = analyze_application(jd_text, cv_text, analysis_type)

            # Increment guest usage only after a successful API response.
            if access_level == "guest":
                increment_guest_usage()

            st.session_state.last_live_output = output_text
            render_analysis_output(output_text)

        except Exception as e:
            st.error("Something went wrong while calling the OpenAI API.")
            st.exception(e)

    elif st.session_state.last_live_output:
        render_analysis_output(st.session_state.last_live_output)
