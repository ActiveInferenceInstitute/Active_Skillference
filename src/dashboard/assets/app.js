const state = {
  status: null,
  materials: null,
  recommendations: null,
  filter: "",
  selectedMaterialSkillId: "",
  dependencyMap: new Map(),
  graphSkillFilter: "",
  graphSubjectFilter: "",
  graphDepthFilter: 0,
  graphBottleneckOnly: false,
};

const el = (id) => document.getElementById(id);

async function getJson(url) {
  const response = await fetch(url, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`${url} returned HTTP ${response.status}`);
  }
  return response.json();
}

function setText(id, value) {
  const node = el(id);
  if (node) {
    node.textContent = value;
  }
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function safeHttpUrl(value, fallback = "http://localhost:8080") {
  if (!value && !fallback) {
    return "";
  }
  try {
    const url = new URL(String(value || fallback), window.location.origin);
    if (url.protocol === "http:" || url.protocol === "https:") {
      return url.toString();
    }
  } catch {
    return fallback;
  }
  return fallback;
}

function isDashboardAssetModule(value) {
  try {
    const url = new URL(String(value || ""), window.location.origin);
    return url.origin === window.location.origin && url.pathname.startsWith("/assets/");
  } catch {
    return false;
  }
}

function renderRichText(value) {
  return escapeHtml(value)
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
    .replace(/\*([^*]+)\*/g, "<em>$1</em>");
}

function truncateText(value, maxLength = 32) {
  const text = String(value ?? "");
  return text.length <= maxLength ? text : `${text.slice(0, maxLength - 3)}...`;
}

function typesetMath(root) {
  if (window.dashboardMathJaxFailed) {
    console.warn("MathJax failed to load; raw math text remains visible.");
    return;
  }
  if (window.MathJax && typeof window.MathJax.typesetPromise === "function") {
    window.MathJax.typesetPromise([root]).catch((error) => {
      console.warn("MathJax typesetting failed", error);
    });
  }
}

function buildDependencyMap(project) {
  const map = new Map();
  for (const dependency of project.dependencies || []) {
    const skillId = dependency.skillId;
    const dependsOn = dependency.dependsOnSkillId;
    if (!skillId || !dependsOn) {
      continue;
    }
    const current = map.get(skillId) || [];
    current.push(dependsOn);
    map.set(skillId, current);
  }
  return map;
}

function skilltreeUrl(...segments) {
  const encoded = segments
    .filter((segment) => segment !== undefined && segment !== null && segment !== "")
    .map((segment) => encodeURIComponent(String(segment)));
  return skilltreeUrlFromRoute(`/${encoded.join("/")}`);
}

function skilltreeUrlFromRoute(route) {
  const dashboard = state.status?.config?.dashboard?.url || window.location.origin;
  const base = dashboard || "";
  if (!base) {
    return "#";
  }
  const url = new URL(base.replace(/\/$/, "/"));
  url.searchParams.set("skillsClientDisplayPath", route);
  return url.toString();
}

function artifactCounts(artifacts) {
  const total = artifacts.length;
  const present = artifacts.filter((artifact) => artifact.exists).length;
  return { present, total };
}

const requiredFigureContractFields = [
  "question",
  "takeaway",
  "data_sources",
  "data_grain",
  "encoding",
  "palette_policy",
  "palette_roots",
  "non_color_encoding",
  "static_read",
  "mobile_read",
  "failure_mode",
];

function hasFigureContractField(figure, field) {
  const value = figure?.[field];
  if (Array.isArray(value)) {
    return value.length > 0;
  }
  return typeof value === "string" && value.trim().length > 0;
}

function figureContractHealth(artifacts) {
  const figures = artifacts
    .map((artifact) => artifact.figure)
    .filter((figure) => figure && typeof figure === "object");
  const complete = figures.filter((figure) => (
    requiredFigureContractFields.every((field) => hasFigureContractField(figure, field))
  )).length;
  return { complete, total: figures.length };
}

function compareCounts(payload) {
  const projectCounts = payload.project.counts || {};
  const stats = payload.curriculum.stats || {};
  const comparisons = [
    ["skills", projectCounts.skills, stats.skills],
    ["subjects", projectCounts.subjects, stats.subjects],
    ["dependencies", projectCounts.dependencies, stats.prerequisite_edges],
  ];
  return comparisons.filter(([, exported, built]) => {
    return Number.isFinite(exported) && Number.isFinite(built) && exported !== built;
  });
}

function dependencyParityText(payload) {
  const exported = payload.project?.counts?.dependencies || 0;
  const live = payload.liveSkilltree || {};
  if (live.checked) {
    const liveCount = live.matchedDependencies ?? live.liveDependencies ?? 0;
    return `${liveCount}/${exported}`;
  }
  if (live.deferred) {
    return `${exported} exported · checking live`;
  }
  return `${exported} exported`;
}

function updateHeaderLinks(config) {
  const dashboard = config.skilltree.links.skilltreeLogin || config.skilltree.links.dashboard;
  const projectJson = "/artifacts/skilltree_project";
  const manuscript = "/artifacts/manuscript_pdf";
  el("skilltree-dashboard-link").href = dashboard;
  el("skilltree-dashboard-link").textContent = "SkillTree login/admin";
  el("official-fallback-link").href = dashboard;
  el("official-fallback-link").textContent = "Open SkillTree login";
  el("project-json-link").href = projectJson;
  el("manuscript-link").href = manuscript;
}

function renderMetrics(payload) {
  const available = Boolean(payload.skilltree.available);
  setText("service-state", available ? "online" : "offline");
  el("service-state").className = available ? "online" : "offline";
  const counts = payload.project.counts || {};
  const stats = payload.curriculum.stats || {};
  const artifactHealth = artifactCounts(payload.artifacts || []);
  setText("skill-count", String(counts.skills || 0));
  setText("subject-count", String(counts.subjects || 0));
  setText("dependency-count", dependencyParityText(payload));
  setText("quiz-count", String(counts.quizzes || 0));
  setText("max-depth", String(stats.max_depth || 0));
  setText("claim-count", String(payload.claims.count || 0));
  setText("artifact-health", `${artifactHealth.present}/${artifactHealth.total}`);
}

function renderSummary(payload) {
  const counts = payload.project.counts || {};
  const stats = payload.curriculum.stats || {};
  const health = artifactCounts(payload.artifacts || []);
  const figureHealth = figureContractHealth(payload.artifacts || []);
  const mismatches = compareCounts(payload);
  const statements = [];
  statements.push(payload.project.available
    ? `${counts.skills || 0} exported skills across ${counts.subjects || 0} subjects.`
    : `SkillTree export unavailable: ${payload.project.error || "missing project artifact"}.`);
  if (payload.skilltree.available && payload.config?.skilltree?.authenticatorConfigured) {
    statements.push(
      "SkillTree service is reachable; the official learner display is using the configured authenticator.",
    );
  } else if (payload.skilltree.available) {
    statements.push(
      "SkillTree service is reachable; the official learner display can mount when auth is configured.",
    );
  } else {
    statements.push("SkillTree service is offline; artifact inspection remains available.");
  }
  const deployment = payload.skilltreeDeployment?.summary || {};
  if (deployment.modes) {
    statements.push(
      `SkillTree deployment modes ready: ${deployment.readyModes || 0}/${deployment.modes}; browser-safe payload=${deployment.browserSafe === true ? "yes" : "review"}.`,
    );
  }
  const liveSkilltree = payload.liveSkilltree || {};
  if (liveSkilltree.checked) {
    const expected = liveSkilltree.expectedDependencies || counts.dependencies || 0;
    const matched = liveSkilltree.matchedDependencies ?? liveSkilltree.liveDependencies ?? 0;
    if (liveSkilltree.complete) {
      statements.push(`Live SkillTree dependency graph matches the export: ${matched}/${expected}.`);
    } else {
      statements.push(
        `Live SkillTree dependency graph is partial: ${matched}/${expected} matched, missing=${liveSkilltree.missingDependencies || 0}, extra=${liveSkilltree.extraDependencies || 0}.`,
      );
    }
  } else if (liveSkilltree.deferred) {
    statements.push(
      "Live SkillTree dependency parity is still being checked; this panel updates when the live graph read returns.",
    );
  } else {
    statements.push(
      `Live SkillTree dependency parity is not checked in this dashboard payload: ${liveSkilltree.reason || "local admin graph access unavailable"}.`,
    );
  }
  const localAuth = payload.config?.skilltree?.localAuth || {};
  if (localAuth.ready) {
    statements.push("Local SkillTree auth state is ready for the trusted-client token bridge.");
  } else if (localAuth.enabled) {
    statements.push(`Local SkillTree auth is not ready: ${localAuth.message || "bootstrap state missing"}.`);
  }
  statements.push(`${health.present} of ${health.total} tracked artifacts are present.`);
  if (payload.courseMaterials?.available) {
    const materialSummary = payload.courseMaterials.summary || {};
    const materialRecords = materialSummary.materialRecords || 0;
    const externalPointers = materialSummary.externalPointers || 0;
    statements.push(
      `${materialRecords} local modular lesson records are available for Learn actions.`,
    );
    statements.push(
      materialRecords === counts.skills && externalPointers >= counts.skills
        ? "Course-material records and external pointers cover the exported skill count."
        : `Course-material parity needs review: records=${materialRecords}, pointers=${externalPointers}, skills=${counts.skills || 0}.`,
    );
  } else {
    statements.push(
      `Local course material index unavailable: ${payload.courseMaterials?.error || "missing generated artifact"}.`,
    );
  }
  statements.push(
    `${figureHealth.complete} of ${figureHealth.total} dashboard figure cards expose the structured chart-contract fields.`,
  );
  const diagnostics = payload.curriculumDiagnostics?.summary || {};
  if (payload.curriculumDiagnostics?.available) {
    statements.push(
      `Curriculum diagnostics track ${diagnostics.bottleneckCount || 0} bottlenecks, ${diagnostics.longPathCount || 0} long-chain rows, and ${diagnostics.remediationCandidates || 0} remediation candidates.`,
    );
  }
  const sourceNetwork = payload.scholarshipHealthNetwork?.summary || {};
  if (payload.scholarshipHealthNetwork?.available) {
    statements.push(
      `Scholarship health separates dead links=${sourceNetwork.deadLinks || 0}, bot blocks=${sourceNetwork.botBlocks || 0}, role gaps=${sourceNetwork.roleGaps || 0}, and uncited drift=${sourceNetwork.uncitedDrift || 0}.`,
    );
  }
  statements.push(
    "Browser-console proof is external to the dashboard payload; the strict full-app validator checks it with chrome-devtools-axi.",
  );
  if (mismatches.length) {
    statements.push(`Count mismatch: ${mismatches.map(([name, exported, built]) => `${name} export=${exported}, build=${built}`).join("; ")}.`);
  } else if (payload.project.available && payload.curriculum.available) {
    statements.push("Build stats and SkillTree export counts agree.");
  }
  setText("summary-text", statements[0]);
  el("summary-list").innerHTML = statements.slice(1).map((statement) => (
    `<li>${escapeHtml(statement)}</li>`
  )).join("");
}

function renderLocalLogin(config) {
  const skilltree = config.skilltree || {};
  const links = skilltree.links || {};
  const localDevelopment = skilltree.localDevelopment || {};
  const localAuth = skilltree.localAuth || {};
  const loginUrl = links.skilltreeLogin || links.dashboard || "http://localhost:8080";
  const resetCommand = localDevelopment.resetCommand
    || "uv run python scripts/reset_local_skilltree.py --confirm-local-reset";
  const showCommand = localDevelopment.showCredentialsCommand
    || "uv run python scripts/bootstrap_local_skilltree.py --show-local-credentials";
  const loginLink = el("local-login-link");
  if (loginLink) {
    loginLink.href = loginUrl;
    loginLink.textContent = loginUrl.replace("/skills-login?redirect=/progress-and-rankings", "");
  }
  setText("local-login-username", localDevelopment.defaultUsername || "active-skillference-admin@localhost.invalid");
  setText(
    "local-login-password",
    localDevelopment.defaultPassword || `Run: ${showCommand}`,
  );
  setText("local-login-reset", resetCommand);

  let note = localDevelopment.warning
    || "These credentials are local-development defaults only.";
  if (localAuth.browserLoginCompatible === false) {
    note = `Current ignored local state uses a legacy non-email username, so raw browser login can fail even while the token bridge works. Run ${resetCommand} to recreate the local volume with the defaults below, or inspect current state with ${showCommand}.`;
  } else if (localAuth.ready) {
    note = `The local learner token bridge is ready. Use the defaults below for a freshly reset local SkillTree login; if state was overridden, inspect it with ${showCommand}.`;
  } else if (localAuth.enabled) {
    note = `Local auth is enabled but not ready: ${localAuth.message || "bootstrap state missing"}. Run ${resetCommand} to reset and restart the local stack with the defaults below.`;
  }
  setText("local-login-note", note);
}

function matchesFilter(text) {
  return text.toLowerCase().includes(state.filter.toLowerCase());
}

function renderCurriculum(project) {
  const root = el("curriculum-list");
  if (!project.available) {
    root.innerHTML = `<p class="empty">${escapeHtml(project.error || "SkillTree export not found")}</p>`;
    return;
  }
  const subjects = project.subjects || [];
  const rows = [];
  state.dependencyMap = buildDependencyMap(project);
  for (const subject of subjects) {
    const skills = subject.skills || [];
    const visibleSkills = skills.filter((skill) => {
      const deps = state.dependencyMap.get(skill.skillId) || [];
      const text = `${subject.subjectId} ${subject.name} ${subject.description} ${skill.skillId} ${skill.name} ${skill.description} ${skill.quizId || ""} ${deps.join(" ")}`;
      return matchesFilter(text);
    });
    if (state.filter && visibleSkills.length === 0 && !matchesFilter(subject.name)) {
      continue;
    }
    rows.push(`
      <article class="subject">
        <header>
          <div>
            <span class="subject-id">${escapeHtml(subject.subjectId)}</span>
            <h3>${escapeHtml(subject.name)}</h3>
          </div>
          <span class="pill">${visibleSkills.length}/${skills.length} skills</span>
        </header>
        <p class="rich-text">${renderRichText(subject.description || "")}</p>
        <div class="skill-grid">
          ${visibleSkills.map((skill) => renderSkill(skill, subject)).join("")}
        </div>
      </article>
    `);
  }
  root.innerHTML = rows.join("") || '<p class="empty">No matching skills.</p>';
  typesetMath(root);
  if (state.selectedMaterialSkillId) {
    renderMaterialDetail(state.selectedMaterialSkillId);
  }
}

function renderSkill(skill, subject) {
  const prerequisites = state.dependencyMap.get(skill.skillId) || [];
  const prereqText = prerequisites.length ? prerequisites.join(", ") : "root skill";
  const subjectUrl = skilltreeUrl("subjects", subject.subjectId);
  const quizUrl = skill.quizId
    ? skilltreeUrl("subjects", subject.subjectId, "skills", skill.skillId, "quizzes", skill.quizId)
    : "";
  const quizAction = quizUrl
    ? `<a class="button small primary" href="${escapeHtml(quizUrl)}" target="_blank" rel="noreferrer" aria-label="Open ${escapeHtml(skill.name)} quiz in SkillTree">
          Quiz
        </a>`
    : "";
  return `
    <details class="skill">
      <summary>
        <span>${escapeHtml(skill.name)}</span>
        <code>${escapeHtml(skill.skillId)}</code>
      </summary>
      <p class="rich-text">${renderRichText(skill.description || "")}</p>
      <dl>
        <dt>Completion</dt>
        <dd>${escapeHtml(skill.selfReportingType)}</dd>
        <dt>Points</dt>
        <dd>${escapeHtml(skill.pointIncrement)}</dd>
        <dt>Quiz</dt>
        <dd>${escapeHtml(skill.quizId || "none")}</dd>
        <dt>Prerequisites</dt>
        <dd>${escapeHtml(prereqText)}</dd>
      </dl>
      <div class="skill-actions">
        <button type="button" class="button small primary" data-material-skill-id="${escapeHtml(skill.skillId)}" aria-controls="material-detail" aria-label="Open local modular material for ${escapeHtml(skill.name)}">
          Learn
        </button>
        <a class="button small" href="${escapeHtml(subjectUrl)}" target="_blank" rel="noreferrer" aria-label="Open ${escapeHtml(subject.name)} subject in SkillTree">
          Open Subject
        </a>
        ${quizAction}
      </div>
    </details>
  `;
}

function renderMaterialSummary() {
  const root = el("material-detail");
  if (!root) {
    return;
  }
  const materials = state.materials;
  if (!materials?.available) {
    root.hidden = false;
    root.innerHTML = `
      <div>
        <p class="eyebrow">Local Learn Material</p>
        <h3>Generated Course Material Unavailable</h3>
        <p>${escapeHtml(materials?.error || "Run scripts/build_course_materials.py to generate the local lesson index.")}</p>
      </div>
    `;
    return;
  }
  const summary = materials.summary || {};
  root.hidden = false;
  root.innerHTML = `
    <div>
      <p class="eyebrow">Local Learn Material</p>
      <h3>${escapeHtml(summary.skills || 0)} modular lesson records</h3>
      <p>Use Learn on a skill to open its local lesson. Official SkillTree state remains in Open Subject and Quiz.</p>
    </div>
  `;
}

function renderRecommendations(recommendations) {
  const root = el("path-recommendations");
  if (!root) {
    return;
  }
  if (!recommendations?.available) {
    root.innerHTML = `
      <div class="path-recommendation-header">
        <div>
          <p class="eyebrow">Path Prototype</p>
          <h3>Recommendations unavailable</h3>
          <p>${escapeHtml(recommendations?.error || "Build the SkillTree export to inspect graph candidates.")}</p>
        </div>
      </div>
    `;
    return;
  }
  const signalText = recommendations.personalized
    ? "Based on SkillTree-owned progress signals."
    : "No progress signal was supplied; these are foundation-start candidates, not personalized advice.";
  const rows = (recommendations.recommendations || []).map((item) => {
    const routes = item.officialSkillTree || {};
    const subjectUrl = routes.subjectRoute ? safeHttpUrl(skilltreeUrlFromRoute(routes.subjectRoute), "") : "";
    const quizUrl = routes.quizRoute ? safeHttpUrl(skilltreeUrlFromRoute(routes.quizRoute), "") : "";
    return `
      <article class="path-recommendation">
        <div>
          <p class="eyebrow">${escapeHtml(item.subjectName)} · depth ${escapeHtml(item.depth)}</p>
          <h4>${escapeHtml(item.name)}</h4>
          <p>${escapeHtml(item.reason)}</p>
          <small>${escapeHtml(item.assessmentQuestionCount)} assessment questions · concepts: ${escapeHtml((item.concepts || []).join(", ") || "graph only")}</small>
        </div>
        <div class="skill-actions">
          ${subjectUrl ? `<a class="button small" href="${escapeHtml(subjectUrl)}" target="_blank" rel="noreferrer">Open Subject</a>` : ""}
          ${quizUrl ? `<a class="button small primary" href="${escapeHtml(quizUrl)}" target="_blank" rel="noreferrer">Open Quiz</a>` : ""}
        </div>
      </article>
    `;
  }).join("");
  root.innerHTML = `
    <div class="path-recommendation-header">
      <div>
        <p class="eyebrow">Path Prototype</p>
        <h3>Explainable next-skill candidates</h3>
        <p>${escapeHtml(signalText)} ${escapeHtml(recommendations.boundary || "")}</p>
      </div>
      <span class="pill">${escapeHtml(recommendations.recommendations?.length || 0)} candidates</span>
    </div>
    <div class="path-recommendation-list">
      ${rows || '<p class="empty">No available candidates in the exported graph.</p>'}
    </div>
  `;
}

function renderMaterialDetail(skillId, { focus = false } = {}) {
  const root = el("material-detail");
  if (!root) {
    return;
  }
  const materials = state.materials;
  if (!materials?.available) {
    renderMaterialSummary();
    return;
  }
  const record = materials.skills?.[skillId];
  if (!record) {
    root.hidden = false;
    root.innerHTML = `
      <div>
        <p class="eyebrow">Local Learn Material</p>
        <h3>Material Record Missing</h3>
        <p>No local material record was generated for <code>${escapeHtml(skillId)}</code>.</p>
      </div>
    `;
    return;
  }
  state.selectedMaterialSkillId = skillId;
  const official = record.officialSkillTree || {};
  const subjectUrl = official.subjectRoute ? skilltreeUrlFromRoute(official.subjectRoute) : "";
  const quizUrl = official.quizRoute ? skilltreeUrlFromRoute(official.quizRoute) : "";
  const sections = (record.sections || []).map((section) => `
    <section class="material-section">
      <h4>${escapeHtml(section.heading)}</h4>
      <p class="rich-text">${renderRichText(section.body || "")}</p>
    </section>
  `).join("");
  const pointerRows = (record.externalPointers || []).map((pointer) => {
    const scopes = Array.isArray(pointer.matchScopes) && pointer.matchScopes.length
      ? pointer.matchScopes.join("+")
      : "source";
    const terms = Array.isArray(pointer.matchTerms) && pointer.matchTerms.length
      ? ` · matched ${pointer.matchTerms.slice(0, 4).join(", ")}`
      : "";
    const pointerUrl = safeHttpUrl(pointer.url, "");
    const pointerTitle = escapeHtml(pointer.title);
    const pointerLink = pointerUrl
      ? `<a href="${escapeHtml(pointerUrl)}" target="_blank" rel="noreferrer">${pointerTitle}</a>`
      : `<span>${pointerTitle}</span>`;
    return `
      <li>
        ${pointerLink}
        <span>${escapeHtml(pointer.sourceTitle)} · ${escapeHtml(pointer.role)} · ${escapeHtml(scopes)}${escapeHtml(terms)} · ${escapeHtml(pointer.commit)}</span>
        <code>${escapeHtml(pointer.path)}</code>
      </li>
    `;
  }).join("");
  const relatedRows = (record.relatedSkills || []).map((item) => `
    <li>
      <button type="button" class="link-button" data-material-skill-id="${escapeHtml(item.skillId)}">
        ${escapeHtml(item.name)}
      </button>
      <code>${escapeHtml(item.skillId)}</code>
    </li>
  `).join("");
  root.hidden = false;
  root.innerHTML = `
    <div class="material-title">
      <div>
        <p class="eyebrow">Local Learn Material</p>
        <h3>${escapeHtml(record.name)}</h3>
        <p>${escapeHtml(record.subjectName)} · <code>${escapeHtml(record.skillId)}</code> · depth ${escapeHtml(record.depth)}</p>
      </div>
      <div class="material-actions">
        ${subjectUrl ? `<a class="button small" href="${escapeHtml(subjectUrl)}" target="_blank" rel="noreferrer">Open Subject</a>` : ""}
        ${quizUrl ? `<a class="button small primary" href="${escapeHtml(quizUrl)}" target="_blank" rel="noreferrer">Quiz</a>` : ""}
      </div>
    </div>
    <div class="material-grid">
      ${sections}
    </div>
    <section class="material-section">
      <h4>External Source Pointers</h4>
      <ul class="source-list">${pointerRows}</ul>
    </section>
    <section class="material-section">
      <h4>Related Local Skills</h4>
      <ul class="related-list">${relatedRows || "<li>No explicit related skills beyond the prerequisite chain.</li>"}</ul>
    </section>
  `;
  typesetMath(root);
  if (focus) {
    root.focus();
    root.scrollIntoView({ block: "start", behavior: "smooth" });
  }
}

function subjectForSkill(project) {
  const map = new Map();
  for (const subject of project.subjects || []) {
    for (const skill of subject.skills || []) {
      map.set(skill.skillId, subject);
    }
  }
  return map;
}

function renderDependencyGraph(project, analysis) {
  const summary = el("graph-summary");
  const root = el("dependency-graph");
  if (!project.available) {
    summary.innerHTML = "";
    root.innerHTML = `<p class="empty">${escapeHtml(project.error || "SkillTree export not found")}</p>`;
    return;
  }

  const subjects = project.subjects || [];
  const dependencies = project.dependencies || [];
  const layout = (analysis?.subjectLayout || []).length
    ? analysis.subjectLayout
    : subjects.map((subject, index) => ({
      incomingSubjectCount: 0,
      incomingFlowCount: 0,
      lane: Math.floor(index / Math.max(1, Math.ceil(subjects.length / 8))),
      name: subject.name,
      order: index,
      outgoingSubjectCount: 0,
      outgoingFlowCount: 0,
      position: index % Math.max(1, Math.ceil(subjects.length / 8)),
      skillCount: (subject.skills || []).length,
      subjectId: subject.subjectId,
      topIncomingFlow: null,
      topOutgoingFlow: null,
    }));
  const subjectById = new Map(subjects.map((subject) => [subject.subjectId, subject]));
  const laneCount = Math.max(1, ...layout.map((item) => Number(item.lane || 0) + 1));
  const laneWidth = 255;
  const rowHeight = 92;
  const nodeWidth = 208;
  const nodeHeight = 68;
  const width = laneCount * laneWidth + 48;
  const laneDepths = new Map();
  for (const item of layout) {
    const lane = Number(item.lane || 0);
    laneDepths.set(lane, Math.max(laneDepths.get(lane) || 0, Number(item.position || 0) + 1));
  }
  const rows = Math.max(1, ...laneDepths.values());
  const height = Math.max(320, rows * rowHeight + 86);
  const positions = new Map();
  for (const item of layout) {
    const lane = Number(item.lane || 0);
    const row = Number(item.position || 0);
    positions.set(item.subjectId, {
      x: 24 + lane * laneWidth,
      y: 58 + row * rowHeight,
    });
  }
  const topEdges = (analysis?.subjectFlows || [])
    .slice(0, 96)
    .map((flow) => ({
      count: Number(flow.count || 0),
      source: subjectById.get(flow.sourceSubjectId) || {
        name: flow.sourceSubjectName,
        subjectId: flow.sourceSubjectId,
      },
      target: subjectById.get(flow.targetSubjectId) || {
        name: flow.targetSubjectName,
        subjectId: flow.targetSubjectId,
      },
    }));

  const edgeMarkup = topEdges.map((edge) => {
    const source = positions.get(edge.source.subjectId);
    const target = positions.get(edge.target.subjectId);
    if (!source || !target) {
      return "";
    }
    const x1 = source.x + nodeWidth;
    const y1 = source.y + nodeHeight / 2;
    const x2 = target.x;
    const y2 = target.y + nodeHeight / 2;
    const widthValue = Math.min(4, 0.75 + edge.count * 0.2);
    const opacity = Math.min(0.65, 0.16 + edge.count * 0.035);
    return `<path d="M ${x1} ${y1} C ${(x1 + x2) / 2} ${y1}, ${(x1 + x2) / 2} ${y2}, ${x2} ${y2}" stroke-width="${widthValue.toFixed(2)}" opacity="${opacity.toFixed(2)}"><title>${escapeHtml(edge.source.name)} to ${escapeHtml(edge.target.name)}: ${edge.count} dependencies</title></path>`;
  }).join("");

  const laneMarkup = Array.from({ length: laneCount }, (_, lane) => {
    const x = 14 + lane * laneWidth;
    const laneSubjects = layout.filter((item) => Number(item.lane || 0) === lane);
    const totalSkills = laneSubjects.reduce((sum, item) => sum + Number(item.skillCount || 0), 0);
    const totalFlow = laneSubjects.reduce((sum, item) => (
      sum + Number(item.incomingFlowCount || 0) + Number(item.outgoingFlowCount || 0)
    ), 0);
    return `
      <g class="graph-lane" transform="translate(${x}, 18)">
        <rect width="${laneWidth - 16}" height="${height - 36}" rx="8"></rect>
        <text x="10" y="18">Lane ${lane + 1}</text>
        <text x="10" y="36">${laneSubjects.length} subjects · ${totalSkills} skills · ${totalFlow} flow refs</text>
      </g>
    `;
  }).join("");

  const nodeMarkup = layout.map((item) => {
    const pos = positions.get(item.subjectId);
    const skillCount = Number(item.skillCount || 0);
    const incoming = Number(item.incomingFlowCount || 0);
    const outgoing = Number(item.outgoingFlowCount || 0);
    const incomingSubjects = Number(item.incomingSubjectCount || 0);
    const outgoingSubjects = Number(item.outgoingSubjectCount || 0);
    const topOutgoing = item.topOutgoingFlow;
    const topIncoming = item.topIncomingFlow;
    const topFlow = topOutgoing
      ? `top out: ${truncateText(topOutgoing.subjectName || topOutgoing.subjectId, 18)} (${Number(topOutgoing.count || 0)})`
      : (topIncoming
        ? `top in: ${truncateText(topIncoming.subjectName || topIncoming.subjectId, 18)} (${Number(topIncoming.count || 0)})`
        : "no cross-subject flow");
    const titleFlow = [
      topIncoming ? `top incoming from ${topIncoming.subjectName || topIncoming.subjectId}: ${Number(topIncoming.count || 0)}` : "",
      topOutgoing ? `top outgoing to ${topOutgoing.subjectName || topOutgoing.subjectId}: ${Number(topOutgoing.count || 0)}` : "",
    ].filter(Boolean).join("; ");
    const label = truncateText(item.name, 28);
    return `
      <g class="graph-node" transform="translate(${pos.x}, ${pos.y})">
        <rect width="${nodeWidth}" height="${nodeHeight}" rx="6"></rect>
        <text x="10" y="20">${escapeHtml(label)}</text>
        <text x="10" y="39">${escapeHtml(item.subjectId)} · ${skillCount} skills · ${incomingSubjects} in-subj / ${outgoingSubjects} out-subj</text>
        <text x="10" y="56">${escapeHtml(topFlow)}</text>
        <title>${escapeHtml(item.name)} (${escapeHtml(item.subjectId)}), ${skillCount} skills, ${incoming} incoming and ${outgoing} outgoing cross-subject dependencies${titleFlow ? `; ${escapeHtml(titleFlow)}` : ""}</title>
      </g>
    `;
  }).join("");

  summary.innerHTML = `
    <span class="graph-pill">${subjects.length} subjects</span>
    <span class="graph-pill">${dependencies.length} skill dependencies</span>
    <span class="graph-pill">${analysis?.summary?.subjectFlows || topEdges.length} subject-to-subject flows</span>
    <span class="graph-pill">${laneCount} ordered lanes</span>
  `;
  root.innerHTML = `
    <svg viewBox="0 0 ${width} ${height}" role="img" aria-label="Ordered subject-lane dependency graph">
      <g>${laneMarkup}</g>
      <g class="graph-edges">${edgeMarkup}</g>
      <g>${nodeMarkup}</g>
    </svg>
  `;
}

function populateGraphSubjectFilter(project) {
  const select = el("graph-subject-filter");
  if (!select || select.options.length > 1) {
    return;
  }
  for (const subject of project.subjects || []) {
    const option = document.createElement("option");
    option.value = subject.subjectId;
    option.textContent = subject.name;
    select.appendChild(option);
  }
}

function renderGraphDiagnostics(analysis) {
  const root = el("graph-diagnostics");
  if (!analysis?.available) {
    root.innerHTML = '<p class="empty">Graph diagnostics require an exported SkillTree project.</p>';
    return;
  }
  const depthControl = el("graph-depth-filter");
  const maxDepth = analysis.summary?.maxDepth || 0;
  if (depthControl.max !== String(maxDepth)) {
    depthControl.max = String(maxDepth);
    depthControl.value = String(Math.min(Number(depthControl.value || 0), maxDepth));
    state.graphDepthFilter = Number(depthControl.value || 0);
  }
  const bottleneckIds = new Set((analysis.bottlenecks || []).map((item) => item.skillId));
  const neighborhoods = Object.values(analysis.neighborhoods || {});
  const filtered = neighborhoods
    .filter((item) => {
      const text = `${item.skillId} ${item.name} ${item.subjectId} ${item.subjectName}`.toLowerCase();
      if (state.graphSkillFilter && !text.includes(state.graphSkillFilter.toLowerCase())) {
        return false;
      }
      if (state.graphSubjectFilter && item.subjectId !== state.graphSubjectFilter) {
        return false;
      }
      if (Number(item.depth || 0) < state.graphDepthFilter) {
        return false;
      }
      if (state.graphBottleneckOnly && !bottleneckIds.has(item.skillId)) {
        return false;
      }
      return true;
    })
    .sort((a, b) => Number(b.depth || 0) - Number(a.depth || 0) || a.skillId.localeCompare(b.skillId))
    .slice(0, 24);
  const bottleneckRows = (analysis.bottlenecks || []).slice(0, 8).map((item) => `
    <tr>
      <td><code>${escapeHtml(item.skillId)}</code></td>
      <td>${escapeHtml(item.name)}</td>
      <td>${escapeHtml(item.subjectName)}</td>
      <td>${escapeHtml(item.dependentCount)}</td>
      <td>${escapeHtml(item.depth)}</td>
    </tr>
  `).join("");
  const neighborhoodRows = filtered.map((item) => `
    <tr>
      <td><code>${escapeHtml(item.skillId)}</code></td>
      <td>${escapeHtml(item.name)}</td>
      <td>${escapeHtml(item.subjectName)}</td>
      <td>${escapeHtml(item.depth)}</td>
      <td>${escapeHtml((item.prerequisites || []).map((row) => row.skillId).join(", ") || "root")}</td>
      <td>${escapeHtml((item.dependents || []).map((row) => row.skillId).join(", ") || "leaf")}</td>
    </tr>
  `).join("");
  root.innerHTML = `
    <section>
      <h3>Graph Diagnostics</h3>
      <div class="graph-summary compact">
        <span class="graph-pill">${escapeHtml(analysis.summary.skills)} skills</span>
        <span class="graph-pill">${escapeHtml(analysis.summary.dependencies)} dependencies</span>
        <span class="graph-pill">${escapeHtml(analysis.summary.maxDepth)} max depth</span>
        <span class="graph-pill">${escapeHtml(analysis.summary.roots)} roots</span>
        <span class="graph-pill">${escapeHtml(analysis.summary.leaves)} leaves</span>
      </div>
    </section>
    <section>
      <h3>Bottleneck Skills</h3>
      <table>
        <thead><tr><th>Skill</th><th>Name</th><th>Subject</th><th>Dependents</th><th>Depth</th></tr></thead>
        <tbody>${bottleneckRows}</tbody>
      </table>
    </section>
    <section>
      <h3>Neighborhood Table</h3>
      <table>
        <thead><tr><th>Skill</th><th>Name</th><th>Subject</th><th>Depth</th><th>Prerequisites</th><th>Dependents</th></tr></thead>
        <tbody>${neighborhoodRows || '<tr><td colspan="6">No matching skills.</td></tr>'}</tbody>
      </table>
    </section>
  `;
}

function renderDependencyFlows(analysis) {
  const root = el("dependency-flows");
  if (!root) {
    return;
  }
  const flows = (analysis?.subjectFlows || []).slice(0, 20);
  if (!flows.length) {
    root.innerHTML = '<p class="empty">No cross-subject prerequisite flows.</p>';
    return;
  }
  const flowRows = flows.map((flow) => `
    <tr>
      <td>${escapeHtml(flow.sourceSubjectName)} <code>${escapeHtml(flow.sourceSubjectId)}</code></td>
      <td>${escapeHtml(flow.targetSubjectName)} <code>${escapeHtml(flow.targetSubjectId)}</code></td>
      <td>${escapeHtml(flow.count)}</td>
    </tr>
  `).join("");
  root.innerHTML = `
    <table>
      <caption>Top subject-to-subject prerequisite flows</caption>
      <thead>
        <tr>
          <th scope="col">Prerequisite subject</th>
          <th scope="col">Dependent subject</th>
          <th scope="col">Dependencies</th>
        </tr>
      </thead>
      <tbody>${flowRows}</tbody>
    </table>
  `;
}

function renderCurriculumDiagnostics(diagnostics) {
  const root = el("curriculum-diagnostics");
  if (!root) {
    return;
  }
  if (!diagnostics?.available) {
    root.innerHTML = `
      <section class="state-card">
        <h3>Curriculum Diagnostic Gap Map</h3>
        <p class="empty">${escapeHtml(diagnostics?.error || "Run scripts/build_curriculum.py to generate curriculum diagnostics.")}</p>
      </section>
    `;
    return;
  }
  const summary = diagnostics.summary || {};
  const queueRows = (diagnostics.remediationQueue || []).slice(0, 8).map((item) => `
    <tr>
      <td>${escapeHtml(item.priority)}</td>
      <td>${item.skillId ? `<code>${escapeHtml(item.skillId)}</code>` : escapeHtml(item.stratum || "stratum")}</td>
      <td>${escapeHtml(item.action)}</td>
      <td>${escapeHtml(item.reason)}</td>
    </tr>
  `).join("");
  const assessmentRows = (diagnostics.assessmentBalance || []).map((item) => `
    <tr>
      <td>${escapeHtml(item.stratum)}</td>
      <td>${escapeHtml(item.skills)}</td>
      <td>${escapeHtml(item.questionsPerSkill)}</td>
      <td><span class="status-pill ${item.status === "pass" ? "pass" : "warn"}">${escapeHtml(item.status)}</span></td>
    </tr>
  `).join("");
  root.innerHTML = `
    <section>
      <h3>Curriculum Diagnostic Gap Map</h3>
      <div class="graph-summary compact">
        <span class="graph-pill">${escapeHtml(summary.bottleneckCount || 0)} bottlenecks</span>
        <span class="graph-pill">${escapeHtml(summary.longPathCount || 0)} long paths</span>
        <span class="graph-pill">${escapeHtml(summary.remediationCandidates || 0)} remediation rows</span>
        <span class="graph-pill">${escapeHtml(summary.assessmentWarningCount || 0)} assessment warnings</span>
      </div>
    </section>
    <section>
      <h3>Remediation Queue</h3>
      <table>
        <thead><tr><th>Priority</th><th>Target</th><th>Action</th><th>Reason</th></tr></thead>
        <tbody>${queueRows || '<tr><td colspan="4">No remediation rows.</td></tr>'}</tbody>
      </table>
    </section>
    <section>
      <h3>Assessment Balance</h3>
      <table>
        <thead><tr><th>Stratum</th><th>Skills</th><th>Questions / Skill</th><th>Status</th></tr></thead>
        <tbody>${assessmentRows}</tbody>
      </table>
    </section>
  `;
}

function figureCompanionFor(figure, figureCompanions) {
  if (!figure || !figureCompanions?.available) {
    return null;
  }
  const companions = figureCompanions.figures || {};
  if (figure.label && companions[figure.label]) {
    return companions[figure.label];
  }
  return Object.values(companions).find((item) => (
    item?.companionId && item.companionId === figure.table_companion_id
  )) || null;
}

function renderFigureMetadata(figure, companion = null) {
  if (!figure) {
    return "";
  }
  const claimCount = Array.isArray(figure.claim_tokens) ? figure.claim_tokens.length : 0;
  const dataSources = Array.isArray(figure.data_sources) && figure.data_sources.length
    ? figure.data_sources.join("; ")
    : figure.data_source || "Generated project artifact data.";
  const paletteRoots = Array.isArray(figure.palette_roots) && figure.palette_roots.length
    ? figure.palette_roots.join(", ")
    : "blue, gray";
  const boundary = figure.interpretation_boundary || "Inspect as generated artifact evidence.";
  const failure = figure.failure_mode || figure.false_certification_risk
    || "Missing failure-mode metadata; rerun artifact validation.";
  return `
    <section class="artifact-figure-contract" aria-label="Figure contract">
      <dl class="artifact-figure-meta artifact-figure-meta-primary">
      <div><dt>Question</dt><dd>${escapeHtml(figure.question || "Missing figure-specific question; rerun artifact validation.")}</dd></div>
      <div><dt>Data grain</dt><dd>${escapeHtml(figure.data_grain || "Missing source-grain metadata; rerun artifact validation.")}</dd></div>
      <div><dt>Boundary</dt><dd>${escapeHtml(boundary)}</dd></div>
      <div><dt>Failure</dt><dd>${escapeHtml(failure)}</dd></div>
      ${companion ? `<div><dt>Companion</dt><dd>${escapeHtml(companion.title || companion.companionId)}</dd></div>` : ""}
    </dl>
      <details class="artifact-figure-details">
        <summary>Encoding and QA details</summary>
        <dl class="artifact-figure-meta artifact-figure-meta-secondary">
          <div><dt>Chart</dt><dd>${escapeHtml(figure.chart_family || "audit summary")}</dd></div>
          <div><dt>Subtitle</dt><dd>${escapeHtml(figure.subtitle || "Generated project artifact.")}</dd></div>
          <div><dt>Takeaway</dt><dd>${escapeHtml(figure.takeaway || "Generated visual artifact.")}</dd></div>
          <div><dt>Encoding</dt><dd>${escapeHtml(figure.encoding || "Labeled axes and direct annotations.")}</dd></div>
          <div><dt>Non-color encoding</dt><dd>${escapeHtml(figure.non_color_encoding || "Labels and layout preserve meaning without hue.")}</dd></div>
          <div><dt>Palette</dt><dd>${escapeHtml(`${figure.palette_policy || "single-root preferred"} · ${paletteRoots}`)}</dd></div>
          <div><dt>Visual grammar</dt><dd>${escapeHtml(figure.visual_grammar || "Labels, layout, and contrast carry the reading.")}</dd></div>
          <div><dt>Data</dt><dd>${escapeHtml(dataSources)}</dd></div>
          <div><dt>Static read</dt><dd>${escapeHtml(figure.static_read || "Missing static-read metadata; rerun artifact validation.")}</dd></div>
      <div><dt>Mobile</dt><dd>${escapeHtml(figure.mobile_note || "Open the full-size image for dense labels.")}</dd></div>
      <div><dt>Mobile read</dt><dd>${escapeHtml(figure.mobile_read || "Missing mobile-read metadata; rerun artifact validation.")}</dd></div>
      <div><dt>QA</dt><dd>${escapeHtml(figure.qa_role || "Visual checksum for generated artifact state.")}</dd></div>
      <div><dt>Claims</dt><dd>${escapeHtml(claimCount)}</dd></div>
    </dl>
      </details>
    </section>
  `;
}

function renderFigureCompanions(figureCompanions, sourceNetwork) {
  const root = el("artifact-companions");
  if (!root) {
    return;
  }
  const sourceSummary = sourceNetwork?.summary || {};
  const sourceCard = sourceNetwork?.available
    ? `
      <article class="companion-card">
        <h3>Scholarship Health Network</h3>
        <p>Dead links ${escapeHtml(sourceSummary.deadLinks || 0)} · bot blocks ${escapeHtml(sourceSummary.botBlocks || 0)} · role gaps ${escapeHtml(sourceSummary.roleGaps || 0)} · uncited drift ${escapeHtml(sourceSummary.uncitedDrift || 0)}</p>
      </article>
    `
    : `
      <article class="companion-card warn">
        <h3>Scholarship Health Network</h3>
        <p>${escapeHtml(sourceNetwork?.error || "Run scripts/analyze_scholarship.py to generate the network report.")}</p>
      </article>
    `;
  if (!figureCompanions?.available) {
    root.innerHTML = `
      ${sourceCard}
      <article class="companion-card warn">
        <h3>Figure Table Companions</h3>
        <p>${escapeHtml(figureCompanions?.error || "Run scripts/run_kernels.py to generate dense figure companions.")}</p>
      </article>
    `;
    return;
  }
  const companionCards = Object.values(figureCompanions.figures || {}).map((companion) => {
    const columns = Array.isArray(companion.columns) ? companion.columns : [];
    const rows = Array.isArray(companion.rows) ? companion.rows.slice(0, 4) : [];
    const tableRows = rows.map((row) => `
      <tr>${columns.slice(0, 4).map((column) => `<td>${escapeHtml(row?.[column] ?? "")}</td>`).join("")}</tr>
    `).join("");
    return `
      <article class="companion-card">
        <h3>${escapeHtml(companion.title || companion.figureLabel)}</h3>
        <p><code>${escapeHtml(companion.figureLabel)}</code> · <code>${escapeHtml(companion.companionId)}</code></p>
        <table>
          <thead><tr>${columns.slice(0, 4).map((column) => `<th>${escapeHtml(column)}</th>`).join("")}</tr></thead>
          <tbody>${tableRows || '<tr><td>No rows.</td></tr>'}</tbody>
        </table>
      </article>
    `;
  }).join("");
  root.innerHTML = sourceCard + companionCards;
}

function renderArtifacts(artifacts, figureCompanions = null) {
  const root = el("artifact-list");
  if (!artifacts.length) {
    root.innerHTML = '<p class="empty state-card">No dashboard artifacts are registered.</p>';
    return;
  }
  root.innerHTML = artifacts.map((artifact) => {
    const isImage = artifact.exists && String(artifact.mediaType || "").startsWith("image/");
    const figure = artifact.figure || null;
    const companion = figureCompanionFor(figure, figureCompanions);
    const thumbnail = isImage
      ? `<a class="artifact-preview" href="${escapeHtml(artifact.url)}" aria-label="Open full-size image for ${escapeHtml(artifact.title)}">
          <img class="artifact-thumb" src="${escapeHtml(artifact.url)}" alt="${escapeHtml(figure?.alt_text || `${artifact.title} preview`)}">
          <span class="artifact-preview-label">Open full-size image</span>
        </a>`
      : "";
    return `
    <article class="artifact ${artifact.exists ? "" : "missing"} ${isImage ? "visual" : ""}" ${figure?.label ? `data-figure-label="${escapeHtml(figure.label)}"` : ""}>
      ${thumbnail}
      <span>
        <strong><a href="${escapeHtml(artifact.url)}">${escapeHtml(artifact.title)}</a></strong>
        <small>${escapeHtml(artifact.path)}</small>
        ${figure?.label ? `<small>${escapeHtml(figure.label)} · ${escapeHtml(figure.chart_family || "visual artifact")}</small>` : ""}
        ${companion ? `<small>Companion table: ${escapeHtml(companion.companionId)}</small>` : ""}
      </span>
      <em>${artifact.exists ? `${escapeHtml(artifact.category)} · ${formatBytes(artifact.bytes)}` : "missing"}</em>
      ${renderFigureMetadata(figure, companion)}
    </article>
  `;
  }).join("");
}

function renderDeploymentMatrix(deployment) {
  const root = el("deployment-matrix");
  if (!root) {
    return;
  }
  const modes = Array.isArray(deployment?.modes) ? deployment.modes : [];
  if (!modes.length) {
    root.innerHTML = '<p class="empty state-card">SkillTree deployment matrix unavailable.</p>';
    return;
  }
  root.innerHTML = `
    <section>
      <h3>SkillTree Deployment Matrix</h3>
      <div class="deployment-grid">
        ${modes.map((mode) => `
          <article class="deployment-mode ${mode.status === "ready" ? "ready" : "blocked"}">
            <span class="status-pill ${mode.status === "ready" ? "pass" : "warn"}">${escapeHtml(mode.status)}</span>
            <h4>${escapeHtml(mode.label)}</h4>
            <p>${escapeHtml(mode.evidence)}</p>
            <small>${escapeHtml(mode.secretBoundary)}</small>
          </article>
        `).join("")}
      </div>
    </section>
  `;
}

// The full /api/status payload carries the exported project and graph analysis —
// several megabytes of JSON. Rendering all of it into the Runtime <pre> froze the
// panel, so show the runtime-state slice and point at the raw route for the rest.
const runtimeStateKeys = [
  "config",
  "skilltree",
  "liveSkilltree",
  "skilltreeDeployment",
  "curriculum",
  "claims",
  "courseMaterials",
  "generatedAt",
];

function runtimeStateView(payload) {
  const view = {};
  for (const key of runtimeStateKeys) {
    if (payload[key] !== undefined) {
      view[key] = payload[key];
    }
  }
  const artifacts = Array.isArray(payload.artifacts) ? payload.artifacts : [];
  view.artifacts = {
    ...artifactCounts(artifacts),
    missing: artifacts.filter((artifact) => !artifact.exists).map((artifact) => artifact.id),
  };
  view.project = {
    available: payload.project?.available ?? false,
    error: payload.project?.error,
    counts: payload.project?.counts || {},
  };
  view.omitted = {
    note: "Full project, graph-analysis, diagnostics, and artifact detail omitted here for page weight.",
    routes: ["/api/status", "/api/project", "/api/artifacts"],
  };
  return view;
}

function formatBytes(bytes) {
  if (!bytes) {
    return "0 B";
  }
  const units = ["B", "KB", "MB", "GB"];
  let value = bytes;
  let index = 0;
  while (value >= 1024 && index < units.length - 1) {
    value /= 1024;
    index += 1;
  }
  return `${value.toFixed(index === 0 ? 0 : 1)} ${units[index]}`;
}

function renderOfficialFallback(message, config) {
  const container = el("skills-client-container");
  container.setAttribute("aria-busy", "false");
  const wrapper = document.createElement("div");
  wrapper.className = "embed-state warn";
  const title = document.createElement("strong");
  title.textContent = "Official SkillTree display is not mounted.";
  const body = document.createElement("span");
  body.textContent = message;
  const link = document.createElement("a");
  link.className = "button primary";
  link.href = safeHttpUrl(config.skilltree.links.dashboard, config.skilltree.url);
  link.textContent = "Open SkillTree";
  wrapper.append(title, body, link);
  container.replaceChildren(wrapper);
}

async function fetchSkillTreeAuthToken(config) {
  const authenticator = config.skilltree.authenticator;
  if (!authenticator || authenticator === "pki") {
    return null;
  }
  const token = await getJson(authenticator);
  if (!token.access_token) {
    throw new Error(`Authenticator ${authenticator} did not return an access_token`);
  }
  return token.access_token;
}

async function mountOfficialDisplay(payload) {
  const config = payload.config;
  const container = el("skills-client-container");
  container.setAttribute("aria-busy", "true");
  if (!payload.skilltree.available) {
    renderOfficialFallback(
      "SkillTree is offline from this dashboard session. Start the local service or use the artifact panels.",
      config,
    );
    return;
  }
  if (!config.skilltree.authenticatorConfigured) {
    const localAuth = config.skilltree.localAuth || {};
    renderOfficialFallback(
      localAuth.enabled
        ? `Local SkillTree auth is not ready: ${localAuth.message}`
        : "No SkillTree client authenticator is configured. Enable the local trusted-client bridge or provide a deployment authenticator.",
      config,
    );
    return;
  }
  container.innerHTML = '<div class="embed-state">Loading official SkillTree display...</div>';
  try {
    if (!isDashboardAssetModule(config.skilltree.clientModuleUrl)) {
      throw new Error("Token-bearing SkillTree display requires a local dashboard client module.");
    }
    const client = await import(config.skilltree.clientModuleUrl);
    const authToken = await fetchSkillTreeAuthToken(config);
    const skilltreeConfig = {
      serviceUrl: config.skilltree.url,
      projectId: config.project.id,
      authenticator: config.skilltree.authenticator,
    };
    if (authToken) {
      skilltreeConfig.authToken = authToken;
    }
    client.SkillsConfiguration.configure(skilltreeConfig);
    await client.SkillsConfiguration.afterConfigure();
    const display = new client.SkillsDisplayJS({
      options: {
        serviceUrl: config.skilltree.url,
        projectId: config.project.id,
        authenticator: config.skilltree.authenticator,
        disableAutoScroll: true,
        updateHistory: false,
        internalBackButton: true,
      },
      theme: {
        maxWidth: "100%",
        landingPageTitle: config.project.name,
        disableSkillTreeBrand: false,
        backgroundColor: "#f8fafc",
        textPrimaryColor: "#152238",
        textSecondaryColor: "#475569",
        progressIndicators: {
          beforeTodayColor: "#0f766e",
          earnedTodayColor: "#2563eb",
          completeColor: "#15803d",
          incompleteColor: "#d6d3d1",
        },
        prerequisites: {
          achievedColor: "#0f766e",
          skillColor: "#2563eb",
          badgeColor: "#7c3aed",
          thisSkillColor: "#b45309",
          navButtonsColor: "#334155",
        },
      },
    });
    container.innerHTML = "";
    container.setAttribute("aria-busy", "false");
    display.attachTo(container);
  } catch (error) {
    renderOfficialFallback(
      `The official SkillTree client could not mount in this browser session: ${error.message}`,
      config,
    );
  }
}

function activateTab(tab, { focus = false } = {}) {
  document.querySelectorAll(".tab").forEach((item) => {
    item.classList.remove("active");
    item.setAttribute("aria-selected", "false");
    item.setAttribute("tabindex", "-1");
  });
  document.querySelectorAll(".panel").forEach((panel) => {
    panel.classList.remove("active");
    panel.hidden = true;
  });
  tab.classList.add("active");
  tab.setAttribute("aria-selected", "true");
  tab.setAttribute("tabindex", "0");
  const panel = el(tab.dataset.panel);
  panel.hidden = false;
  panel.classList.add("active");
  if (focus) {
    tab.focus();
  }
}

function wireTabs() {
  const tabs = [...document.querySelectorAll(".tab")];
  tabs.forEach((tab, index) => {
    tab.addEventListener("click", () => activateTab(tab));
    tab.addEventListener("keydown", (event) => {
      let target = null;
      if (event.key === "ArrowRight") {
        target = tabs[(index + 1) % tabs.length];
      } else if (event.key === "ArrowLeft") {
        target = tabs[(index - 1 + tabs.length) % tabs.length];
      } else if (event.key === "Home") {
        target = tabs[0];
      } else if (event.key === "End") {
        target = tabs[tabs.length - 1];
      }
      if (target) {
        event.preventDefault();
        activateTab(target, { focus: true });
      }
    });
  });
}

function renderPayload(payload) {
  updateHeaderLinks(payload.config);
  renderMetrics(payload);
  renderSummary(payload);
  renderLocalLogin(payload.config);
  renderMaterialSummary();
  renderRecommendations(state.recommendations);
  renderCurriculum(payload.project);
  renderFigureCompanions(payload.figureCompanions, payload.scholarshipHealthNetwork);
  renderArtifacts(payload.artifacts, payload.figureCompanions);
  populateGraphSubjectFilter(payload.project);
  renderDependencyGraph(payload.project, payload.graphAnalysis);
  renderDependencyFlows(payload.graphAnalysis);
  renderCurriculumDiagnostics(payload.curriculumDiagnostics);
  renderGraphDiagnostics(payload.graphAnalysis);
  renderDeploymentMatrix(payload.skilltreeDeployment);
  el("runtime-json").textContent = JSON.stringify(runtimeStateView(payload), null, 2);
}

// Live dependency parity logs into SkillTree and pulls the whole live graph, which
// takes seconds. Paint from the deferred payload first, then swap in the checked
// parity when it lands, so no panel waits on the live round trip.
async function refreshLiveParity() {
  const checked = await getJson("/api/status");
  if (!state.status) {
    return checked;
  }
  state.status = checked;
  renderMetrics(checked);
  renderSummary(checked);
  el("runtime-json").textContent = JSON.stringify(runtimeStateView(checked), null, 2);
  return checked;
}

async function refresh() {
  document.body.classList.add("is-loading");
  try {
    const [payload, materials, recommendations] = await Promise.all([
      getJson("/api/status?defer_live=1"),
      getJson("/api/course-materials").catch((error) => ({
        available: false,
        error: error.message,
        summary: { skills: 0, externalPointers: 0, sources: 0 },
        sources: [],
        skills: {},
      })),
      getJson("/api/recommendations").catch((error) => ({
        available: false,
        error: error.message,
        recommendations: [],
      })),
    ]);
    state.status = payload;
    state.materials = materials;
    state.recommendations = recommendations;
    renderPayload(payload);
    refreshLiveParity().catch((error) => {
      console.warn("live SkillTree parity check failed", error);
    });
    return payload;
  } finally {
    document.body.classList.remove("is-loading");
  }
}

async function main() {
  wireTabs();
  el("refresh-status").addEventListener("click", () => {
    refresh().catch((error) => {
      setText("service-state", "error");
      el("runtime-json").textContent = error.stack || error.message;
    });
  });
  el("curriculum-panel").addEventListener("click", (event) => {
    const target = event.target instanceof Element
      ? event.target.closest("[data-material-skill-id]")
      : null;
    if (!target) {
      return;
    }
    renderMaterialDetail(target.dataset.materialSkillId, { focus: true });
  });
  el("curriculum-search").addEventListener("input", (event) => {
    state.filter = event.target.value || "";
    if (state.status) {
      renderCurriculum(state.status.project);
    }
  });
  el("graph-skill-search").addEventListener("input", (event) => {
    state.graphSkillFilter = event.target.value || "";
    if (state.status) {
      renderGraphDiagnostics(state.status.graphAnalysis);
    }
  });
  el("graph-subject-filter").addEventListener("change", (event) => {
    state.graphSubjectFilter = event.target.value || "";
    if (state.status) {
      renderGraphDiagnostics(state.status.graphAnalysis);
    }
  });
  el("graph-depth-filter").addEventListener("input", (event) => {
    state.graphDepthFilter = Number(event.target.value || 0);
    if (state.status) {
      renderGraphDiagnostics(state.status.graphAnalysis);
    }
  });
  el("graph-bottleneck-only").addEventListener("change", (event) => {
    state.graphBottleneckOnly = Boolean(event.target.checked);
    if (state.status) {
      renderGraphDiagnostics(state.status.graphAnalysis);
    }
  });
  const payload = await refresh();
  await mountOfficialDisplay(payload);
}

main().catch((error) => {
  setText("service-state", "error");
  document.body.classList.remove("is-loading");
  el("skills-client-container").setAttribute("aria-busy", "false");
  el("skills-client-container").innerHTML = `
    <div class="embed-state warn">
      <strong>Dashboard data could not load.</strong>
      <span>${escapeHtml(error.message || "Unknown dashboard error")}</span>
    </div>
  `;
  el("runtime-json").textContent = error.stack || error.message;
});
