const formEl = document.getElementById("triageForm");
const fileInputEl = document.getElementById("fileInput");
const fileMetaEl = document.getElementById("fileMeta");
const requestEl = document.getElementById("requestJson");
const outputEl = document.getElementById("outputJson");
const summaryEl = document.getElementById("summary");
const stagesEl = document.getElementById("stages");
const fieldsPanelEl = document.getElementById("fieldsPanel");
const decisionCardEl = document.getElementById("decisionCard");
const statusEl = document.getElementById("statusPill");
const stepperEl = document.getElementById("stepper");

function setStatus(text, kind = "") {
  statusEl.textContent = text;
  statusEl.className = `pill ${kind}`.trim();
}

function setStepperState(activeStep) {
  const steps = stepperEl.querySelectorAll(".step");
  steps.forEach((stepEl) => {
    const step = Number(stepEl.dataset.step);
    stepEl.classList.remove("is-active", "is-done");
    if (step < activeStep) stepEl.classList.add("is-done");
    else if (step === activeStep) stepEl.classList.add("is-active");
  });
}

function renderSummary(result) {
  const disposition = result?.disposition || "n/a";
  const route = result?.route || "n/a";
  const priority = result?.priority?.level || "n/a";
  summaryEl.innerHTML = [
    `<div class="chip"><strong>Disposition</strong><br>${disposition}</div>`,
    `<div class="chip"><strong>Route</strong><br>${route}</div>`,
    `<div class="chip"><strong>Priority</strong><br>${priority}</div>`
  ].join("");
}

function renderDecision(result) {
  const disposition = result?.disposition || "n/a";
  const route = result?.route || "n/a";
  const reason = result?.reason ? `Reason: ${result.reason}` : "No blocking reason.";
  const priority = result?.priority?.level ? `Priority: ${result.priority.level} (${result.priority.score})` : "Priority not assigned.";

  decisionCardEl.innerHTML = `
    <strong>${disposition}</strong>
    ${priority}<br>
    Route: ${route}<br>
    ${reason}
  `;
}

function renderStages(result) {
  const details = result?.payload || {};
  const classification = details.classification || {};
  const duplicate = details.duplicate_check || {};
  const extraction = details.extraction || {};
  const validation = details.validation || {};
  const priority = details.priority || result?.priority || {};

  const stageModels = [
    {
      title: "1) Classify Format & Source",
      status: "done",
      detail: `${classification.po_format || "unknown"} from ${classification.source || "unknown source"}`
    },
    {
      title: "2) Duplicate Check",
      status: duplicate.is_duplicate ? "stop" : "done",
      detail: duplicate.is_duplicate
        ? "Duplicate detected. Flow is stopped."
        : "No duplicate found."
    },
    {
      title: "3) Field Extraction",
      status: details.halted ? "skip" : "done",
      detail: details.halted
        ? "Skipped because item was already stopped."
        : `Path: ${extraction.extraction_path || "n/a"}`
    },
    {
      title: "4) Confidence Validation",
      status: details.halted
        ? "skip"
        : details.manual_fallback
          ? "warn"
          : "done",
      detail: details.halted
        ? "Skipped because item was already stopped."
        : details.manual_fallback
          ? "Low confidence. Sent to manual review."
          : "Validation passed."
    },
    {
      title: "5) Priority Scoring",
      status: details.priority ? "done" : "skip",
      detail: details.priority
        ? `${priority.rule_id}: score=${priority.score}, level=${priority.level}. ${priority.rationale || ""}`.trim()
        : `Skipped: ${details.priority_skipped_reason || "not applicable"}`
    },
    {
      title: "6) Downstream Output",
      status: result?.disposition === "REJECT_DUPLICATE" ? "stop" : "done",
      detail: `Disposition: ${result?.disposition || "n/a"} -> ${result?.route || "n/a"}`
    }
  ];

  stagesEl.innerHTML = stageModels.map(toStageCard).join("");
}

function renderExtractedFields(result) {
  const extraction = result?.payload?.extraction;
  if (!extraction || !extraction.extracted_fields) {
    fieldsPanelEl.innerHTML = `<div class="field-empty">No extracted fields available for this item.</div>`;
    return;
  }

  const pairs = Object.entries(extraction.extracted_fields);
  const meta = [
    ["extraction_path", extraction.extraction_path || "n/a"],
    ["template_id", extraction.template_id || "n/a"],
    ["confidence", extraction.confidence ?? "n/a"]
  ];

  const cards = [...meta, ...pairs].map(([k, v]) => `
    <div class="field-chip">
      <span class="k">${k}</span>
      <span class="v">${v === null || v === "" ? "n/a" : String(v)}</span>
    </div>
  `);
  fieldsPanelEl.innerHTML = cards.join("");
}

function toStageCard(stage) {
  const map = {
    done: { label: "Done", cls: "ok" },
    warn: { label: "Needs Review", cls: "warn" },
    stop: { label: "Stopped", cls: "stop" },
    skip: { label: "Skipped", cls: "skip" }
  };
  const badge = map[stage.status] || map.skip;
  return `
    <article class="stage-card">
      <div class="stage-head">
        <span class="stage-title">${stage.title}</span>
        <span class="badge ${badge.cls}">${badge.label}</span>
      </div>
      <p class="stage-detail">${stage.detail}</p>
    </article>
  `;
}

async function readDocument(file) {
  const mime = file.type || inferMime(file.name);
  const payload = {
    filename: file.name,
    mime_type: mime,
    size_bytes: file.size
  };

  if (mime.startsWith("text/") || file.name.toLowerCase().endsWith(".eml") || mime === "application/pdf") {
    payload.text = await file.text();
  }
  return payload;
}

function inferMime(filename) {
  const lower = filename.toLowerCase();
  if (lower.endsWith(".pdf")) return "application/pdf";
  if (lower.endsWith(".png")) return "image/png";
  if (lower.endsWith(".jpg") || lower.endsWith(".jpeg")) return "image/jpeg";
  if (lower.endsWith(".txt")) return "text/plain";
  if (lower.endsWith(".eml")) return "message/rfc822";
  return "application/octet-stream";
}

function buildPayload(documentPayload) {
  return { document: documentPayload };
}

async function runTriage(event) {
  event.preventDefault();
  const file = fileInputEl.files?.[0];
  if (!file) {
    setStatus("Select a file", "error");
    return;
  }

  setStatus("Uploading...");
  outputEl.textContent = "";
  requestEl.textContent = "";
  summaryEl.innerHTML = "";
  stagesEl.innerHTML = "";
  fieldsPanelEl.innerHTML = "";
  decisionCardEl.textContent = "Processing...";
  setStepperState(2);

  try {
    const documentPayload = await readDocument(file);
    const payload = buildPayload(documentPayload);
    requestEl.textContent = JSON.stringify(payload, null, 2);

    const response = await fetch("/api/triage", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const result = await response.json();
    outputEl.textContent = JSON.stringify(result, null, 2);

    if (!response.ok) {
      setStatus("Request failed", "error");
      setStepperState(1);
      return;
    }
    setStepperState(3);
    renderDecision(result);
    renderSummary(result);
    renderExtractedFields(result);
    renderStages(result);
    setStatus("Complete", "success");
  } catch (error) {
    setStatus("Error", "error");
    setStepperState(1);
    decisionCardEl.textContent = "Could not process this document.";
    outputEl.textContent = JSON.stringify({ error: String(error) }, null, 2);
  }
}

fileInputEl.addEventListener("change", () => {
  const file = fileInputEl.files?.[0];
  fileMetaEl.textContent = file
    ? `Selected: ${file.name} (${file.type || inferMime(file.name)}), ${file.size} bytes`
    : "No file selected.";
  setStepperState(file ? 2 : 1);
});

formEl.addEventListener("submit", runTriage);
setStepperState(1);
setStatus("Ready");
