async function loadIndex() {
  const response = await fetch("/api/index");
  if (!response.ok) {
    throw new Error(`Failed to load review data: ${response.status}`);
  }
  return response.json();
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

function fmtTime(seconds) {
  const totalSeconds = Math.max(0, Math.round(Number(seconds || 0)));
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const secs = totalSeconds % 60;
  if (hours > 0) {
    return `${hours}h ${minutes}min ${secs}s`;
  }
  if (minutes > 0) {
    return `${minutes}min ${secs}s`;
  }
  return `${secs}s`;
}

function segmentLabel(segment) {
  return segment.title || segment.segment_id || segment.folder_name;
}

function buildCanonicalLookup(workspaces) {
  const canonical = workspaces.find((workspace) => workspace.kind === "canonical");
  if (!canonical) {
    return { workspace: null, byId: new Map() };
  }

  const byId = new Map();
  for (const segment of canonical.segments) {
    byId.set(segment.segment_id, segment);
  }
  return { workspace: canonical, byId };
}

function render(state) {
  const app = document.getElementById("app");
  if (!state.workspaces.length) {
    app.innerHTML = `<div class="panel section"><p class="empty">No workspaces loaded.</p></div>`;
    return;
  }

  const workspace = state.workspaces[state.workspaceIndex];
  const segment = workspace.segments[state.segmentIndex] || null;
  const canonicalLookup = buildCanonicalLookup(state.workspaces);
  const sourceSegmentId = segment?.source_map?.source_segment_ids?.[0] || null;
  const sourceSegment = sourceSegmentId ? canonicalLookup.byId.get(sourceSegmentId) : null;

  app.innerHTML = `
    <div class="shell">
      <aside class="panel sidebar">
        <div class="workspace-switcher">
          ${state.workspaces.map((item, index) => `
            <button class="workspace-button ${index === state.workspaceIndex ? "active" : ""}" data-workspace-index="${index}">
              <div><strong>${escapeHtml(item.label)}</strong></div>
              <div class="workspace-meta">${escapeHtml(item.kind)} · ${item.segments.length} segments</div>
            </button>
          `).join("")}
        </div>
        <div class="section">
          <h2>Segments</h2>
          <div class="segment-list">
            ${workspace.segments.map((item, index) => `
              <button class="segment-button ${index === state.segmentIndex ? "active" : ""}" data-segment-index="${index}">
                <div><strong>${escapeHtml(segmentLabel(item))}</strong></div>
                <div class="segment-meta">${escapeHtml(item.segment_id)} · ${fmtTime(item.start_time)} - ${fmtTime(item.end_time)}</div>
              </button>
            `).join("") || `<p class="empty">No segment folders found.</p>`}
          </div>
        </div>
      </aside>
      <main class="main">
        <section class="panel header">
          <span class="pill">${escapeHtml(workspace.label)}</span>
          <span class="pill">${escapeHtml(workspace.kind)}</span>
          <h1>${escapeHtml(segment ? segmentLabel(segment) : workspace.label)}</h1>
          <p>${escapeHtml(segment?.summary || "Select a segment to inspect clip timing, subtitles, and captions.")}</p>
          <div class="toolbar">
            ${workspace.source_video_url ? `<a href="${workspace.source_video_url}" target="_blank" rel="noreferrer">Open source video</a>` : ""}
            ${segment?.clip_url ? `<a href="${segment.clip_url}" target="_blank" rel="noreferrer">Open segment clip</a>` : ""}
            ${segment?.subtitles_url ? `<a href="${segment.subtitles_url}" target="_blank" rel="noreferrer">Open segment subtitles</a>` : ""}
            ${segment?.readme_url ? `<a href="${segment.readme_url}" target="_blank" rel="noreferrer">Open segment README</a>` : ""}
          </div>
        </section>

        <section class="viewer-grid">
          <div class="panel section">
            <h2>Primary Video</h2>
            ${segment?.clip_url
              ? `<video controls preload="metadata" src="${segment.clip_url}"></video>`
              : workspace.source_video_url
                ? `<video controls preload="metadata" src="${workspace.source_video_url}"></video>`
                : `<p class="empty">No playable video found for this selection.</p>`}
          </div>
          <div class="panel section">
            <h2>${sourceSegment ? "Source Comparison" : "Workspace Context"}</h2>
            ${sourceSegment?.clip_url
              ? `<video controls preload="metadata" src="${sourceSegment.clip_url}"></video>`
              : workspace.source_video_url
                ? `<video controls preload="metadata" src="${workspace.source_video_url}"></video>`
                : `<p class="empty">No comparison video available.</p>`}
            ${workspace.normalized_audio_url
              ? `<div class="toolbar"><a href="${workspace.normalized_audio_url}" target="_blank" rel="noreferrer">Open normalized audio</a></div>`
              : ""}
          </div>
        </section>

        <section class="info-grid">
          <div class="panel card">
            <h3>Segment Metadata</h3>
            ${segment ? `
              <dl class="meta-table">
                <dt>Segment ID</dt><dd>${escapeHtml(segment.segment_id)}</dd>
                <dt>Folder</dt><dd>${escapeHtml(segment.folder_name)}</dd>
                <dt>Start</dt><dd>${fmtTime(segment.start_time)}</dd>
                <dt>End</dt><dd>${fmtTime(segment.end_time)}</dd>
                <dt>Duration</dt><dd>${fmtTime(segment.duration)}</dd>
                <dt>Title</dt><dd>${escapeHtml(segment.title)}</dd>
                <dt>Summary</dt><dd>${escapeHtml(segment.summary)}</dd>
                <dt>Detail</dt><dd>${escapeHtml(segment.detail || "<empty>")}</dd>
              </dl>
            ` : `<p class="empty">Select a segment to inspect metadata.</p>`}
          </div>
          <div class="panel card">
            <h3>Workspace Overview</h3>
            <pre class="code-block">${escapeHtml(workspace.root_readme_text)}</pre>
          </div>
          <div class="panel card">
            <h3>Subtitles</h3>
            <pre class="code-block">${escapeHtml(segment?.subtitles_text || workspace.root_subtitles_text || "No subtitles found.")}</pre>
          </div>
          <div class="panel card">
            <h3>Caption / README</h3>
            <pre class="code-block">${escapeHtml(segment?.readme_text || "No segment README selected.")}</pre>
          </div>
          <div class="panel card">
            <h3>Task / Source Mapping</h3>
            <pre class="code-block">${escapeHtml(JSON.stringify(segment?.source_map || workspace.derivation || workspace.execution_plan || {}, null, 2) || "No task mapping or execution metadata available.")}</pre>
          </div>
          <div class="panel card">
            <h3>Source Segment Context</h3>
            <pre class="code-block">${escapeHtml(sourceSegment ? sourceSegment.readme_text : (workspace.task_text || "No linked canonical source segment for this selection."))}</pre>
          </div>
        </section>
      </main>
    </div>
  `;

  for (const button of app.querySelectorAll("[data-workspace-index]")) {
    button.addEventListener("click", () => {
      state.workspaceIndex = Number(button.dataset.workspaceIndex);
      state.segmentIndex = 0;
      render(state);
    });
  }

  for (const button of app.querySelectorAll("[data-segment-index]")) {
    button.addEventListener("click", () => {
      state.segmentIndex = Number(button.dataset.segmentIndex);
      render(state);
    });
  }
}

async function main() {
  const app = document.getElementById("app");
  app.innerHTML = `<div class="panel section"><p class="empty">Loading review workspace...</p></div>`;
  try {
    const data = await loadIndex();
    render({
      workspaces: data.workspaces || [],
      workspaceIndex: 0,
      segmentIndex: 0,
    });
  } catch (error) {
    app.innerHTML = `<div class="panel section"><p class="empty">${escapeHtml(error.message)}</p></div>`;
  }
}

main();
