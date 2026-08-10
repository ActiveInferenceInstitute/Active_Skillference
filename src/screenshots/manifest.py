"""Canonical manifest of learner-dashboard screenshots used as delivery evidence.

One row per captured view. The rows carry the same chart-contract metadata as the
deterministic figure registry (via :func:`attach_chart_contract`) so a reader —
and the manuscript artifact audit — can hold both families to one standard, while
:mod:`src.screenshots.capture` records separately that these pixels come from a
live browser rather than a pure function.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.figures.registry import (
    CAPTURED_ASSET_ROOT,
    CAPTURED_EVIDENCE,
    attach_chart_contract,
)

SCREENSHOT_DIR_NAME = CAPTURED_ASSET_ROOT
SCREENSHOT_PROVENANCE_FILENAME = "screenshot_provenance.json"
GENERATED_BY = "src.screenshots.capture.capture_screenshots"

#: Fixed capture viewport. Pinning it keeps successive captures comparable and
#: keeps the responsive breakpoints (780px, 480px) out of the evidence set.
VIEWPORT_WIDTH = 1440
VIEWPORT_HEIGHT = 900

_PALETTE_POLICY = (
    "dashboard design-system tokens: blue accent for interactive affordances, "
    "green for validated evidence rows, amber for local-development cautions, "
    "and neutral gray surfaces for everything else"
)
_PALETTE_ROOTS = ("blue", "green", "amber", "gray")


@dataclass(frozen=True)
class ScreenshotView:
    """One captured dashboard view and the manuscript evidence it carries."""

    view_id: str
    label: str
    caption: str
    alt_text: str
    chart_family: str
    question: str
    takeaway: str
    subtitle: str
    data_source: str
    data_grain: str
    encoding: str
    non_color_encoding: str
    static_read: str
    mobile_note: str
    interpretation_boundary: str
    false_certification_risk: str
    accessibility_note: str
    qa_role: str
    setup_js: str
    settle_ms: int = 2500
    data_sources: tuple[str, ...] = ()
    claim_tokens: tuple[str, ...] = field(default_factory=tuple)

    @property
    def filename(self) -> str:
        return f"{self.view_id}.png"

    def registry_row(self) -> dict[str, Any]:
        """Return the registry row for this view with the chart contract attached."""
        row: dict[str, Any] = {
            "filename": self.filename,
            "label": self.label,
            "caption": self.caption,
            "alt_text": self.alt_text,
            "generated_by": GENERATED_BY,
            "chart_family": self.chart_family,
            "question": self.question,
            "takeaway": self.takeaway,
            "subtitle": self.subtitle,
            "data_source": self.data_source,
            "data_sources": list(self.data_sources or (self.data_source,)),
            "data_grain": self.data_grain,
            "encoding": self.encoding,
            "palette_policy": _PALETTE_POLICY,
            "palette_roots": list(_PALETTE_ROOTS),
            "non_color_encoding": self.non_color_encoding,
            "static_read": self.static_read,
            "mobile_note": self.mobile_note,
            "mobile_read": self.mobile_note,
            "interpretation_boundary": self.interpretation_boundary,
            "false_certification_risk": self.false_certification_risk,
            "failure_mode": self.false_certification_risk,
            "accessibility_note": self.accessibility_note,
            "qa_role": self.qa_role,
            "claim_tokens": list(self.claim_tokens),
            "asset_root": CAPTURED_ASSET_ROOT,
            "evidence_kind": CAPTURED_EVIDENCE,
        }
        attach_chart_contract(row)
        return row


_SHARED_BOUNDARY = (
    "The image records the state of one local development stack at capture time; "
    "it evidences delivery of the interface, not learner outcomes or efficacy."
)

_VIEWS: tuple[ScreenshotView, ...] = (
    ScreenshotView(
        view_id="app_operational_snapshot",
        label="fig:app_operational_snapshot",
        caption=(
            "Learner dashboard landing view captured from the running local stack. The metric "
            "row reports exported skills, subjects, quizzes, maximum prerequisite depth, "
            "registered claims, and artifact presence, while the dependency metric shows live "
            "SkillTree parity against the export rather than the exported count alone. The "
            "evidence list below restates those machine-checked conditions in words: export "
            "counts, live graph parity, local auth readiness, course-material coverage, and "
            "figure-contract completeness are surfaced together on one page instead of being "
            "scattered across separate reports. The list continues past the fold; the frame "
            "shows the first ten of its rows. The artifact tally counts this evidence family "
            "among the tracked artifacts, so it is a completeness check on the roster rather "
            "than an independent audit of these images."
        ),
        alt_text=(
            "Screenshot of the learner dashboard header and status grid showing SkillTree "
            "online, exported skill, subject, quiz, depth, claim and artifact counts, a live "
            "dependency parity ratio, and a list of green evidence statements covering "
            "deployment readiness, artifact presence, course material coverage, curriculum "
            "diagnostics, and scholarship source health."
        ),
        chart_family="operational status board",
        question=(
            "Does one local page show the generated export, the live SkillTree graph, and "
            "generated artifact health at the same moment?"
        ),
        takeaway=(
            "Export counts, live dependency parity, and artifact presence read together on the "
            "landing view without navigating away from the learner surface."
        ),
        subtitle=(
            "Source: dashboard /api/status against the pinned local SkillTree stack; metrics "
            "are live reads, not cached report values."
        ),
        data_source=(
            "Dashboard /api/status payload combining the SkillTree export, the live admin "
            "dependency graph, and the generated artifact inventory."
        ),
        data_grain=(
            "One card per tracked runtime metric and one list row per machine-checked "
            "operational condition."
        ),
        encoding=(
            "Large tabular numerals encode counts, an explicit online or offline word encodes "
            "service reachability, and each evidence row is a separate bordered statement."
        ),
        non_color_encoding=(
            "Every status is written as a word or a ratio, so the reading survives without hue "
            "and is available to screen readers through the live regions."
        ),
        static_read=(
            "The still image supports checking which conditions hold at capture time; the "
            "running page adds refresh and drill-down that a static capture cannot show."
        ),
        mobile_note=(
            "Below the 780 pixel breakpoint the status grid and evidence list stack into a "
            "single column, so this wide capture is not representative of narrow layout."
        ),
        interpretation_boundary=_SHARED_BOUNDARY,
        false_certification_risk=(
            "Prevents a claim that the platform surfaces live delivery state from resting on "
            "prose alone when the interface could have shown exported counts only."
        ),
        accessibility_note=(
            "Status words, tabular figures, and per-row borders carry the meaning; the page "
            "itself exposes these as polite live regions rather than color changes."
        ),
        qa_role=(
            "Confirms the operational snapshot reports live parity rather than restating the "
            "exported dependency count back to the reader."
        ),
        setup_js=(
            "(function(){window.scrollTo(0,0);"
            "var t=document.getElementById('tab-official');if(t){t.click();}"
            "return 'ok'})()"
        ),
        settle_ms=1500,
    ),
    ScreenshotView(
        view_id="app_official_learner_view",
        label="fig:app_official_learner_view",
        caption=(
            "The Official Display tab captured while the embedded SkillTree learner client is "
            "mounted against the seeded project. The overview header, overall points, level "
            "and level progress rings, the achieved-skills bar reading zero of the full "
            "exported skill count, the personal rank card, and the point-history panel are "
            "all rendered by SkillTree's own client library inside the project dashboard, "
            "which is the demonstration that the export lands in the platform runtime rather "
            "than in a project reimplementation of it. Every progress value reads zero and "
            "the point-history panel shows its first-point empty state, because the capture "
            "uses a freshly seeded local identity that has completed nothing."
        ),
        alt_text=(
            "Screenshot of the embedded official SkillTree learner display inside the project "
            "dashboard, showing an overview header with the project name, overall points at "
            "zero, a level indicator with empty stars, level progress, achieved skills at "
            "zero out of the full export, a personal rank card reading first of one user, "
            "and a point-history panel displaying its no-progress-yet empty state."
        ),
        chart_family="embedded third-party learner runtime",
        question=(
            "Does the exported curriculum reach SkillTree's own learner runtime instead of a "
            "project-owned imitation of it?"
        ),
        takeaway=(
            "SkillTree's own client renders the seeded project with its native points, levels, "
            "ranking, and progress rings inside the local dashboard shell."
        ),
        subtitle=(
            "Source: the official skills-client-js display authenticated through the local "
            "server-side trusted-client token bridge."
        ),
        data_source=(
            "Live SkillTree service state for the seeded activeInference project, rendered by "
            "the official skills-client-js library."
        ),
        data_grain=(
            "One embedded learner portal for a single local learner identity across every "
            "seeded subject."
        ),
        encoding=(
            "SkillTree's own visual language: ring gauges for point totals, star rows for "
            "level, and ribboned tiles for each subject with progress bars."
        ),
        non_color_encoding=(
            "Numeric point and level totals, explicit out-of totals, and named subject ribbons "
            "carry the reading independently of the tile colors."
        ),
        static_read=(
            "The still image establishes that the official runtime mounts and renders the "
            "seeded project; interaction, quiz taking, and progress accrual are not shown."
        ),
        mobile_note=(
            "The embed is bounded to the viewport and scrolls internally, so a narrow screen "
            "shows the same content through the inner scroll region rather than a reflow."
        ),
        interpretation_boundary=(
            "Zero points reflect a freshly seeded local learner and are evidence of a working "
            "empty state, not evidence about learning or engagement."
        ),
        false_certification_risk=(
            "Prevents the platform-integration claim from resting on export JSON alone when "
            "the official learner client could silently fail to mount."
        ),
        accessibility_note=(
            "Progress values are written as numbers beside every gauge, and the surrounding "
            "panel keeps a text fallback link to the SkillTree login surface."
        ),
        qa_role=(
            "Catches a regression where the embedded learner client is blocked and the panel "
            "renders as an empty frame while every offline gate still passes."
        ),
        setup_js=(
            "(function(){var t=document.getElementById('tab-official');if(t){t.click();}"
            "var f=document.querySelector('.skilltree-frame');"
            "if(f){f.scrollIntoView({block:'start'});window.scrollBy(0,-90);}"
            "return 'ok'})()"
        ),
        settle_ms=9000,
    ),
    ScreenshotView(
        view_id="app_curriculum_learn_material",
        label="fig:app_curriculum_learn_material",
        caption=(
            "The Curriculum tab captured with the generated lesson record for the variational "
            "free energy skill opened through its Learn action. The panel shows the concept "
            "context, prerequisite position, downstream role, assessment summary, and the "
            "commit-pinned external source pointers generated for that skill, alongside the "
            "handoff buttons that return the learner to the official SkillTree subject and "
            "quiz routes. It is the delivery counterpart to the course-material provenance "
            "rule: local lessons link out to pinned upstream sources instead of copying them."
        ),
        alt_text=(
            "Screenshot of the curriculum explorer filtered to a single skill, with an opened "
            "local lesson panel showing headed sections for concept context, prerequisites, "
            "downstream role and assessment summary, a list of external source pointers with "
            "repository paths and commit identifiers, and buttons that open the SkillTree "
            "subject and quiz."
        ),
        chart_family="record detail panel",
        question=(
            "Does a learner reach generated lesson material and its pinned upstream sources "
            "for one individual skill?"
        ),
        takeaway=(
            "Choosing Learn on a skill opens its generated lesson record with pinned external "
            "pointers, while progress and quizzes stay on the official SkillTree routes."
        ),
        subtitle=(
            "Source: the generated course-material index built from the curriculum graph and "
            "the commit-pinned source manifest."
        ),
        data_source=(
            "Generated course-material index records joined to the exported SkillTree project "
            "for subject and quiz routing."
        ),
        data_grain=(
            "One lesson record for one skill, with one row per pinned external source pointer."
        ),
        encoding=(
            "Headed prose sections carry lesson context, a bulleted list carries source "
            "pointers with repository path and commit, and buttons carry platform handoffs."
        ),
        non_color_encoding=(
            "Section headings, monospace identifiers, and button labels carry the structure "
            "with no reliance on hue anywhere in the panel."
        ),
        static_read=(
            "The still image establishes that lesson content and pinned provenance are "
            "present; following the pointers and taking the quiz are live actions."
        ),
        mobile_note=(
            "On a narrow screen the lesson grid collapses to one column and the source list "
            "wraps, so this capture shows the widescreen arrangement only."
        ),
        interpretation_boundary=_SHARED_BOUNDARY,
        false_certification_risk=(
            "Prevents the pinned-source claim from resting on a generated index file that no "
            "learner-facing surface actually renders."
        ),
        accessibility_note=(
            "The panel is a labeled live region that receives focus when opened, and every "
            "pointer is a real link with visible text rather than an icon."
        ),
        qa_role=(
            "Confirms the Learn action opens generated local material rather than navigating "
            "to the upstream skill-detail route that is known to error."
        ),
        setup_js=(
            "(function(){var t=document.getElementById('tab-curriculum');if(t){t.click();}"
            "var s=document.getElementById('curriculum-search');"
            "if(s){s.value='vm_free_energy';"
            "s.dispatchEvent(new Event('input',{bubbles:true}));}"
            "setTimeout(function(){"
            "var b=document.querySelector('[data-material-skill-id=\"vm_free_energy\"]');"
            "if(b){b.click();}"
            "setTimeout(function(){"
            "var d=document.getElementById('material-detail');"
            "if(d){d.scrollIntoView({block:'start'});window.scrollBy(0,-90);}"
            "},1200);},1200);"
            "return 'ok'})()"
        ),
        settle_ms=6000,
    ),
    ScreenshotView(
        view_id="app_dependency_graph",
        label="fig:app_dependency_graph",
        caption=(
            "The accessible prerequisite-flow table in the Graph tab, scrolled past the "
            "subject lane canvas that sits above it in the same panel. Table and canvas are built from the "
            "same server-computed flow summaries, so the prerequisite structure reaches a "
            "keyboard or screen-reader user as captioned rows with real header cells rather "
            "than only as a drawing. Each row is one directed subject-to-subject relation: a "
            "prerequisite subject, the dependent subject that requires it, and how many skill "
            "dependencies run between them, ordered by weight."
        ),
        alt_text=(
            "Screenshot of the dependency graph tab scrolled to a table captioned top "
            "subject-to-subject prerequisite flows, with header cells for prerequisite "
            "subject, dependent subject, and dependencies, and rows pairing named subjects "
            "and their identifiers with the count of skill dependencies between them."
        ),
        chart_family="lane diagram with paired data table",
        question=(
            "Is the prerequisite structure legible in the delivered interface for a reader who "
            "cannot use the drawing?"
        ),
        takeaway=(
            "The subject lanes ship beside a semantic prerequisite-flow table built from the "
            "same server-computed data, so the structure survives without the graphic."
        ),
        subtitle=(
            "Source: server-computed subject layout and flow summaries derived from the "
            "exported prerequisite edges."
        ),
        data_source=(
            "Dashboard graph analysis payload with subject lanes, flow counts, and curriculum "
            "diagnostic rows."
        ),
        data_grain=(
            "One lane per subject, one edge per aggregated prerequisite relation, and one "
            "table row per subject flow summary."
        ),
        encoding=(
            "Horizontal lanes encode subjects, connecting strokes encode aggregated "
            "prerequisite flow, and the paired table restates each lane as counted rows."
        ),
        non_color_encoding=(
            "The captioned table with real header cells reproduces every relationship the "
            "diagram encodes, which is the accessible path through the same data."
        ),
        static_read=(
            "The still image establishes that the non-visual representation exists and is "
            "populated; filtering and focusing individual skills require the running page."
        ),
        mobile_note=(
            "The lane canvas scrolls horizontally on narrow screens while the flow table "
            "remains the primary reading, so this capture overstates available width."
        ),
        interpretation_boundary=_SHARED_BOUNDARY,
        false_certification_risk=(
            "Prevents an accessibility claim from resting on an image-only graph view with no "
            "equivalent non-visual representation of the same edges."
        ),
        accessibility_note=(
            "The flow table uses a caption and header cells, and the graph controls are native "
            "labeled inputs reachable by keyboard."
        ),
        qa_role=(
            "Confirms the accessible flow table is generated alongside the lane diagram rather "
            "than being an aspiration recorded only in documentation."
        ),
        setup_js=(
            "(function(){var t=document.getElementById('tab-graph');if(t){t.click();}"
            "setTimeout(function(){"
            "var f=document.getElementById('dependency-flows');"
            "if(f){f.scrollIntoView({block:'center'});}"
            "},1500);"
            "return 'ok'})()"
        ),
        settle_ms=5000,
    ),
    ScreenshotView(
        view_id="app_runtime_deployment_matrix",
        label="fig:app_runtime_deployment_matrix",
        caption=(
            "The browser-visible runtime payload in the Runtime tab, scrolled past the "
            "deployment-mode matrix to the local development block. The default password "
            "field is an empty string and its availability flag is false, so the page "
            "reports the local username and the recovery commands while withholding the "
            "credential itself; no client secret and no bearer token appear anywhere in the "
            "payload. The same view carries the SkillTree reachability block and the live "
            "dependency parity block reporting complete parity with no missing or extra "
            "edges, which is the auth-boundary evidence in the form the browser actually "
            "receives it."
        ),
        alt_text=(
            "Screenshot of a dark preformatted panel of runtime state JSON in the runtime "
            "tab, showing a local development block whose default password is an empty "
            "string with availability false alongside the local username and reset and "
            "show-credentials commands, followed by a SkillTree reachability block and a "
            "live dependency block reporting complete parity with zero missing and zero "
            "extra dependencies."
        ),
        chart_family="browser-visible state payload",
        question=(
            "Can an operator confirm deployment-mode readiness without any secret reaching the "
            "browser?"
        ),
        takeaway=(
            "The payload the browser receives withholds the password and carries no client "
            "secret or bearer token, while still reporting live dependency parity."
        ),
        subtitle=(
            "Source: the source-owned deployment matrix and the browser-safe runtime slice of "
            "the dashboard status payload."
        ),
        data_source=(
            "SkillTree deployment matrix and the redacted runtime portion of the dashboard "
            "status payload."
        ),
        data_grain=(
            "One runtime state document for the current dashboard process, read as labeled "
            "JSON fields."
        ),
        encoding=(
            "A monospace JSON payload encodes the exact configuration the browser is allowed "
            "to see, with each boundary-relevant field on its own labeled line."
        ),
        non_color_encoding=(
            "The evidence is literal text: field names and values, so the reading does not "
            "depend on hue anywhere in the frame."
        ),
        static_read=(
            "The still image supports auditing exactly which fields the browser receives; "
            "refreshing and following the full payload route need the running page."
        ),
        mobile_note=(
            "The payload becomes a keyboard-scrollable block on narrow screens, so line "
            "wrapping differs from this wide capture."
        ),
        interpretation_boundary=(
            "Readiness describes this local development stack. Deployment hardening, identity "
            "policy, and monitoring remain the operating organization's responsibility."
        ),
        false_certification_risk=(
            "Prevents a secret-boundary claim from being asserted in prose while the browser "
            "payload quietly carries credentials."
        ),
        accessibility_note=(
            "The payload block is focusable and scrollable by keyboard, and every value is "
            "literal text rather than an icon or a color."
        ),
        qa_role=(
            "Confirms the browser-safe payload really withholds the admin password and client "
            "secret while still reporting local auth readiness and live parity."
        ),
        setup_js=(
            "(function(){var t=document.getElementById('tab-runtime');if(t){t.click();}"
            "setTimeout(function(){"
            "var pre=document.getElementById('runtime-json');"
            "if(!pre){return;}"
            "var text=pre.textContent||'';"
            "var idx=text.indexOf('localDevelopment');"
            "var frac=idx>0?idx/text.length:0;"
            "var box=pre.getBoundingClientRect();"
            "var top=window.scrollY+box.top+(box.height*frac)-160;"
            "window.scrollTo(0,Math.max(0,top));"
            "},1200);"
            "return 'ok'})()"
        ),
        settle_ms=4000,
    ),
)


def screenshot_views() -> tuple[ScreenshotView, ...]:
    """Return the canonical captured-view manifest."""
    return _VIEWS


def captured_registry_payload() -> list[dict[str, Any]]:
    """Return the figure-registry rows for every captured view."""
    return [view.registry_row() for view in _VIEWS]
