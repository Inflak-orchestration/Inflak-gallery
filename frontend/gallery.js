const state = {
  cases: [],
  filter: "all",
  query: "",
  artifactSubstrates: new Set(),
  interactionRealizations: new Set(),
};

const elements = {
  grid: document.querySelector("#gallery-grid"),
  empty: document.querySelector("#gallery-empty"),
  resultCount: document.querySelector("#filter-result-count"),
  substrateFilters: document.querySelector("#substrate-filters"),
  realizationFilters: document.querySelector("#realization-filters"),
  clearTaxonomyFilters: document.querySelector("#clear-taxonomy-filters"),
  search: document.querySelector("#gallery-search"),
  template: document.querySelector("#case-card-template"),
  dialog: document.querySelector("#case-dialog"),
  dialogTitle: document.querySelector("#dialog-title"),
  dialogKicker: document.querySelector("#dialog-kicker"),
  dialogAboutTitle: document.querySelector("#dialog-about-title"),
  dialogDescription: document.querySelector("#dialog-description"),
  dialogLayerFiles: document.querySelector("#dialog-layer-files"),
  dialogVideo: document.querySelector("#dialog-video"),
  dialogModel: document.querySelector("#dialog-model"),
  dialogFeatures: document.querySelector("#dialog-features"),
  historyPreview: document.querySelector("#history-preview"),
  historyDownload: document.querySelector("#history-download"),
};

function formatDuration(seconds) {
  if (!Number.isFinite(seconds)) return "Duration unavailable";
  const minutes = Math.floor(seconds / 60);
  const remainder = seconds % 60;
  return minutes ? `${minutes}m ${remainder}s` : `${remainder}s`;
}

function searchableText(item) {
  const features = item.features || {};
  return [item.title, item.focus, item.kind, ...(item.artifactSubstrates || []), ...(item.interactionRealizations || []), ...(features.layers || []), ...(features.tools || [])]
    .join(" ")
    .toLowerCase();
}

function visibleCases() {
  return state.cases.filter((item) => {
    const matchesFilter = state.filter === "all" || item.kind === state.filter;
    const matchesSubstrate = state.artifactSubstrates.size === 0
      || item.artifactSubstrates?.some((value) => state.artifactSubstrates.has(value));
    const matchesRealization = state.interactionRealizations.size === 0
      || item.interactionRealizations?.some((value) => state.interactionRealizations.has(value));
    return matchesFilter && matchesSubstrate && matchesRealization && (!state.query || searchableText(item).includes(state.query));
  });
}

function appendTag(container, label, kind) {
  const tag = document.createElement("span");
  tag.className = `taxonomy-tag taxonomy-tag-${kind}`;
  tag.textContent = label;
  container.append(tag);
}

function renderFacetOptions(container, values, stateKey) {
  container.replaceChildren();
  for (const value of values) {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = value;
    button.setAttribute("aria-pressed", "false");
    button.addEventListener("click", () => {
      const selections = state[stateKey];
      if (selections.has(value)) selections.delete(value);
      else selections.add(value);
      button.classList.toggle("active", selections.has(value));
      button.setAttribute("aria-pressed", String(selections.has(value)));
      renderGallery();
    });
    container.append(button);
  }
}

function showInteractionFrame(video, seconds, fallbackRatio) {
  if (!Number.isFinite(seconds) && !Number.isFinite(fallbackRatio)) return;
  const seekToInteraction = () => {
    if (!Number.isFinite(video.duration) || video.duration <= 0) return;
    const requestedTime = Number.isFinite(seconds) ? seconds : video.duration * fallbackRatio;
    video.currentTime = Math.max(0, Math.min(video.duration - 0.1, requestedTime));
  };
  if (video.readyState >= HTMLMediaElement.HAVE_METADATA) seekToInteraction();
  else video.addEventListener("loadedmetadata", seekToInteraction, { once: true });
}

function renderGallery() {
  const cases = visibleCases();
  elements.grid.replaceChildren();
  elements.empty.classList.toggle("hidden", cases.length > 0);
  elements.resultCount.textContent = `${cases.length} ${cases.length === 1 ? "case" : "cases"}`;
  elements.clearTaxonomyFilters.classList.toggle(
    "hidden",
    state.artifactSubstrates.size === 0 && state.interactionRealizations.size === 0,
  );
  for (const item of cases) {
    const card = elements.template.content.firstElementChild.cloneNode(true);
    const button = card.querySelector(".case-open");
    const video = card.querySelector("video");
    video.src = item.videoUrl || "";
    showInteractionFrame(video, item.coverTimeSeconds, item.features?.interactionPreviewRatio);
    card.querySelector(".case-index").textContent = item.kind === "paradigm" ? item.title.split(" ")[0] : item.kind;
    card.querySelector(".case-kind").textContent = item.kind === "paradigm" ? "Interaction paradigm" : item.kind;
    card.querySelector("h2").textContent = item.title;
    card.querySelector(".case-focus").textContent = item.focus;
    const tags = card.querySelector(".case-tags");
    for (const substrate of item.artifactSubstrates || []) appendTag(tags, substrate, "substrate");
    for (const realization of item.interactionRealizations || []) appendTag(tags, realization, "realization");
    const features = item.features || {};
    card.querySelector(".case-stats").textContent = `${features.completedSteps || 0} steps  /  ${formatDuration(features.durationSeconds)}`;
    button.addEventListener("click", () => openCase(item));
    elements.grid.append(card);
  }
  window.lucide?.createIcons();
}

function addFeature(label, value) {
  const row = document.createElement("div");
  const term = document.createElement("span");
  const detail = document.createElement("strong");
  term.textContent = label;
  detail.textContent = value;
  row.append(term, detail);
  elements.dialogFeatures.append(row);
}

function renderLayerFiles(layerFiles) {
  const labels = {
    L1: "Routing",
    L2: "Task planning",
    L3: "Interaction & execution",
    L4: "Interface rendering",
  };
  elements.dialogLayerFiles.replaceChildren();
  for (const layer of ["L1", "L2", "L3", "L4"]) {
    const group = document.createElement("article");
    group.className = `layer-file-group ${layer === "L2" || layer === "L3" ? "layer-file-group-primary" : ""}`;
    const heading = document.createElement("div");
    heading.className = "layer-file-heading";
    const badge = document.createElement("strong");
    badge.textContent = layer;
    const role = document.createElement("span");
    role.textContent = labels[layer];
    heading.append(badge, role);
    const list = document.createElement("div");
    list.className = "layer-file-list";
    const files = layerFiles?.[layer] || [];
    if (!files.length) {
      const empty = document.createElement("span");
      empty.className = "layer-file-empty";
      empty.textContent = "Not loaded in this recording";
      list.append(empty);
    } else {
      for (const file of files) {
        const row = document.createElement("div");
        const name = document.createElement("span");
        name.className = "layer-skill-name";
        name.textContent = file.name;
        const path = document.createElement("code");
        path.textContent = file.path || "SKILL.md path unavailable";
        const count = document.createElement("span");
        count.className = "layer-file-count";
        count.textContent = `${file.invocations} load${file.invocations === 1 ? "" : "s"}`;
        row.append(name, path, count);
        list.append(row);
      }
    }
    group.append(heading, list);
    elements.dialogLayerFiles.append(group);
  }
}

async function openCase(item) {
  const features = item.features || {};
  elements.dialogTitle.textContent = item.title;
  elements.dialogKicker.textContent = item.focus;
  elements.dialogAboutTitle.textContent = item.kind === "paradigm" ? "About this paradigm" : "About this case";
  elements.dialogDescription.textContent = item.description || "";
  renderLayerFiles(item.layerFiles);
  elements.dialogVideo.src = item.videoUrl || "";
  elements.dialogModel.textContent = item.run?.model || "No model data";
  elements.dialogFeatures.replaceChildren();
  addFeature("Artifact substrate", (item.artifactSubstrates || []).join(", ") || "Unclassified");
  addFeature("Interaction realization", (item.interactionRealizations || []).join(", ") || "Unclassified");
  addFeature("Completed steps", String(features.completedSteps || 0));
  addFeature("Interactive moments", String(features.interactionCount || 0));
  addFeature("Elapsed time", formatDuration(features.durationSeconds));
  addFeature("Observed tools", (features.tools || []).join(", ") || "None recorded");
  elements.historyDownload.classList.toggle("hidden", !item.historyUrl);
  elements.historyDownload.href = item.historyUrl || "#";
  elements.historyDownload.download = `${item.caseId}-history.jsonl`;
  elements.historyPreview.textContent = item.historyUrl ? "Loading history..." : "No history file is available for this case.";
  elements.dialog.showModal();
  window.lucide?.createIcons();
  elements.dialogVideo.currentTime = 0;
  elements.dialogVideo.muted = false;
  try {
    await elements.dialogVideo.play();
  } catch {
    elements.dialogVideo.muted = true;
    await elements.dialogVideo.play().catch(() => {});
  }
  if (!item.historyUrl) return;
  try {
    const response = await fetch(item.historyUrl);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const lines = (await response.text()).trim().split("\n").filter(Boolean);
    const preview = lines.slice(0, 12).map((line) => {
      try {
        const event = JSON.parse(line);
        const time = String(event.timestamp || "").slice(11, 19);
        return `${time}  ${event.status || "event"}  ${event.displayName || event.name || "unknown"}`;
      } catch {
        return "Invalid history record skipped";
      }
    });
    elements.historyPreview.textContent = preview.join("\n") + (lines.length > preview.length ? `\n\n... ${lines.length - preview.length} more events` : "");
  } catch (error) {
    elements.historyPreview.textContent = `History preview unavailable: ${error.message}`;
  }
}

function closeDialog() {
  elements.dialogVideo.pause();
  elements.dialogVideo.removeAttribute("src");
  elements.dialogVideo.load();
  elements.dialog.close();
}

document.querySelectorAll("[data-filter]").forEach((button) => {
  button.addEventListener("click", () => {
    state.filter = button.dataset.filter;
    document.querySelectorAll("[data-filter]").forEach((candidate) => candidate.classList.toggle("active", candidate === button));
    renderGallery();
  });
});
elements.search.addEventListener("input", () => {
  state.query = elements.search.value.trim().toLowerCase();
  renderGallery();
});
elements.clearTaxonomyFilters.addEventListener("click", () => {
  state.artifactSubstrates.clear();
  state.interactionRealizations.clear();
  document.querySelectorAll(".taxonomy-options button").forEach((button) => {
    button.classList.remove("active");
    button.setAttribute("aria-pressed", "false");
  });
  renderGallery();
});
document.querySelector("#dialog-close").addEventListener("click", closeDialog);
elements.dialog.addEventListener("click", (event) => {
  if (event.target === elements.dialog) closeDialog();
});

async function loadGallery() {
  try {
    const response = await fetch("/api/gallery/cases");
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    state.cases = data.cases || [];
    renderFacetOptions(elements.substrateFilters, data.facets?.artifactSubstrates || [], "artifactSubstrates");
    renderFacetOptions(elements.realizationFilters, data.facets?.interactionRealizations || [], "interactionRealizations");
    renderGallery();
  } catch (error) {
    const message = document.createElement("p");
    message.className = "load-error";
    message.textContent = `Could not load gallery: ${error.message}`;
    elements.grid.replaceChildren(message);
  }
}

loadGallery();