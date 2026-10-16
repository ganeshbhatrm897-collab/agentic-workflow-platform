const $ = (selector) => document.querySelector(selector);
const state = { examples: [], latest: null, busy: false };
const icons = { meeting: "M", project: "P", document: "D", support: "S" };

function showError(message) {
  const box = $("#error-banner");
  box.textContent = message;
  box.hidden = !message;
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  const data = await response.json();
  if (!response.ok) {
    const detail = Array.isArray(data.detail)
      ? data.detail.map((item) => item.msg).join("; ")
      : data.detail;
    throw new Error(detail || `Request failed (${response.status}).`);
  }
  return data;
}

function renderExamples() {
  const container = $("#example-list");
  container.replaceChildren();
  state.examples.forEach((example) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "example-button";
    button.setAttribute("aria-label", `Load ${example.title} demo`);
    const icon = document.createElement("span");
    icon.className = "example-icon";
    icon.textContent = icons[example.scenario] || "W";
    const copy = document.createElement("span");
    copy.className = "example-copy";
    const title = document.createElement("strong");
    title.textContent = example.title;
    const description = document.createElement("small");
    description.textContent = example.description;
    copy.append(title, description);
    button.append(icon, copy);
    button.addEventListener("click", () => {
      $("#task-input").value = example.task;
      $("#task-input").focus();
      $("#task-input").dataset.scenario = example.scenario;
      showError("");
    });
    container.append(button);
  });
}

function renderAgents(agents) {
  $("#agent-count").textContent = String(agents.length);
  const list = $("#agent-list");
  list.replaceChildren();
  agents.forEach((agent) => {
    const item = document.createElement("li");
    item.className = "agent-item";
    const icon = document.createElement("span");
    icon.className = "agent-icon";
    icon.textContent = agent.name.slice(0, 1);
    const detail = document.createElement("div");
    const name = document.createElement("strong");
    name.textContent = agent.name;
    const description = document.createElement("p");
    description.textContent = agent.description;
    detail.append(name, description);
    item.append(icon, detail);
    list.append(item);
  });
}

function renderHistory(items) {
  const list = $("#history-list");
  list.replaceChildren();
  if (!items.length) {
    const empty = document.createElement("p");
    empty.className = "empty-note";
    empty.textContent = "Your recent workflows will appear here.";
    list.append(empty);
    return;
  }
  items.slice(0, 5).forEach((item) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "history-item";
    const task = document.createElement("strong");
    task.textContent = item.task;
    const meta = document.createElement("span");
    meta.textContent = `${item.status} · ${new Date(item.created_at).toLocaleString()}`;
    button.append(task, meta);
    button.addEventListener("click", async () => {
      try {
        renderWorkflow(await api(`/api/workflows/${encodeURIComponent(item.workflow_id)}`));
      } catch (error) {
        showError(error.message);
      }
    });
    list.append(button);
  });
}

function renderWorkflow(workflow) {
  state.latest = workflow;
  $("#execution-panel").hidden = false;
  const status = $("#workflow-status");
  status.textContent = workflow.status;
  status.className = `status-pill ${workflow.status}`;
  const plans = $("#plan-list");
  plans.replaceChildren();
  workflow.plan.forEach((step, index) => {
    const card = document.createElement("article");
    card.className = `plan-step ${step.status}`;
    const number = document.createElement("span");
    number.className = "step-number";
    number.textContent = step.status === "completed" ? "✓" : String(index + 1).padStart(2, "0");
    const body = document.createElement("div");
    const title = document.createElement("strong");
    title.textContent = step.agent_id;
    const description = document.createElement("p");
    description.textContent = step.description;
    body.append(title, description);
    if (step.output || step.validation || step.error) {
      const details = document.createElement("details");
      details.className = "step-details";
      const summary = document.createElement("summary");
      summary.textContent = step.error ? "View failure details" : "View output & validation";
      const pre = document.createElement("pre");
      pre.textContent = JSON.stringify({ output: step.output, validation: step.validation, error: step.error }, null, 2);
      details.append(summary, pre);
      body.append(details);
    }
    const stepStatus = document.createElement("span");
    stepStatus.className = "step-state";
    stepStatus.textContent = step.status;
    card.append(number, body, stepStatus);
    plans.append(card);
  });
  const events = $("#event-list");
  events.replaceChildren();
  workflow.events.forEach((event) => {
    const item = document.createElement("li");
    if (event.level === "error") item.classList.add("error");
    const time = document.createElement("span");
    time.className = "event-time";
    time.textContent = new Date(event.timestamp).toLocaleTimeString();
    item.append(time, document.createTextNode(event.message));
    events.append(item);
  });
  $("#final-result").textContent = workflow.final_summary;
  const structure = $("#structured-output");
  structure.replaceChildren();
  const details = document.createElement("details");
  const summary = document.createElement("summary");
  summary.textContent = "Inspect structured result data";
  const pre = document.createElement("pre");
  pre.textContent = JSON.stringify(workflow.result, null, 2);
  details.append(summary, pre);
  structure.append(details);
  $("#execution-panel").scrollIntoView({ behavior: "smooth", block: "start" });
}

async function runWorkflow() {
  if (state.busy) return;
  const task = $("#task-input").value.trim();
  if (!task) {
    showError("Enter a task or choose a demo scenario before running the workflow.");
    $("#task-input").focus();
    return;
  }
  state.busy = true;
  const button = $("#run-button");
  button.disabled = true;
  button.querySelector("span").textContent = "Running…";
  showError("");
  try {
    const scenario = $("#task-input").dataset.scenario;
    const workflow = await api("/api/workflows", {
      method: "POST",
      body: JSON.stringify({ task, ...(scenario ? { scenario } : {}) }),
    });
    renderWorkflow(workflow);
    $("#task-input").dataset.scenario = "";
    renderHistory(await api("/api/workflows"));
  } catch (error) {
    showError(error.message);
  } finally {
    state.busy = false;
    button.disabled = false;
    button.querySelector("span").textContent = "Run workflow";
  }
}

async function initialize() {
  try {
    const [health, agents, examples, history] = await Promise.all([
      api("/api/health"), api("/api/agents"), api("/api/workflows/examples"), api("/api/workflows"),
    ]);
    $("#mode-badge").textContent = health.demo_mode ? "DEMO MODE · OFFLINE READY" : "OPTIONAL LLM CONFIGURED";
    state.examples = examples;
    renderExamples();
    renderAgents(agents);
    renderHistory(history);
  } catch (error) {
    showError(`Could not load the dashboard: ${error.message}`);
  }
}

$("#run-button").addEventListener("click", runWorkflow);
$("#reset-button").addEventListener("click", () => {
  $("#task-input").value = "";
  $("#task-input").dataset.scenario = "";
  $("#execution-panel").hidden = true;
  showError("");
  $("#task-input").focus();
});
$("#task-input").addEventListener("input", () => {
  $("#task-input").dataset.scenario = "";
});
initialize();
