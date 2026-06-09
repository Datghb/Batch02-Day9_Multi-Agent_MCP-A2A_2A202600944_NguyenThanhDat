const servicesEl = document.querySelector("#services");
const serviceCountEl = document.querySelector("#service-count");
const elapsedEl = document.querySelector("#elapsed");
const logEl = document.querySelector("#log");
const answerEl = document.querySelector("#answer");
const demoButton = document.querySelector("#run-demo");
const realButton = document.querySelector("#run-real");
const questionEl = document.querySelector("#question");
const refreshButton = document.querySelector("#refresh-services");
const clearButton = document.querySelector("#clear-log");

let source = null;

const nodeOrder = [
  "analyze_law",
  "check_routing",
  "call_tax_specialist",
  "call_compliance_specialist",
  "call_privacy_specialist",
  "aggregate",
];

function setNodeStatus(id, status, text) {
  const node = document.querySelector(`[data-node="${id}"]`);
  if (!node) return;
  node.classList.remove("pending", "running", "completed", "error");
  node.classList.add(status);
  node.querySelector("span").textContent = text || status;
}

function resetNodes() {
  nodeOrder.forEach((id) => setNodeStatus(id, "pending", "pending"));
}

function appendLog(title, detail, update) {
  const entry = document.createElement("div");
  entry.className = "log-entry";
  const strong = document.createElement("strong");
  strong.textContent = title;
  const small = document.createElement("span");
  small.textContent = detail || "";
  entry.append(strong, small);
  if (update) {
    const code = document.createElement("code");
    code.textContent = JSON.stringify(update, null, 2);
    entry.append(code);
  }
  logEl.prepend(entry);
}

async function refreshServices() {
  servicesEl.innerHTML = "";
  const response = await fetch("/api/services");
  const data = await response.json();
  const online = data.services.filter((service) => service.status === "online").length;
  serviceCountEl.textContent = `${online}/${data.services.length}`;

  data.services.forEach((service) => {
    const item = document.createElement("div");
    item.className = `service ${service.status}`;
    item.innerHTML = `
      <div class="status"><span class="dot"></span><strong>${service.name}</strong></div>
      <span>${service.url}</span>
      <span>${service.status} · ${service.latency_ms}ms</span>
    `;
    servicesEl.append(item);
  });
}

function setRunning(isRunning) {
  demoButton.disabled = isRunning;
  realButton.disabled = isRunning;
  demoButton.textContent = isRunning ? "Running" : "Run Demo";
}

function runGraph(endpoint) {
  if (source) {
    source.close();
  }

  resetNodes();
  logEl.innerHTML = "";
  answerEl.textContent = "";
  elapsedEl.textContent = "0.00s";
  setRunning(true);

  setNodeStatus("analyze_law", "running", "running");
  const question = encodeURIComponent(questionEl.value.trim());
  source = new EventSource(`${endpoint}?question=${question}`);

  source.addEventListener("reset", (event) => {
    const data = JSON.parse(event.data);
    appendLog("Request started", data.question);
  });

  source.addEventListener("node", (event) => {
    const data = JSON.parse(event.data);
    setNodeStatus(data.id, "completed", `${data.elapsed}s · ${data.summary}`);
    elapsedEl.textContent = `${data.elapsed.toFixed(2)}s`;
    appendLog(data.label, `${data.elapsed}s · ${data.summary}`, data.update);

    const currentIndex = nodeOrder.indexOf(data.id);
    const next = nodeOrder[currentIndex + 1];
    if (next) {
      const nextNode = document.querySelector(`[data-node="${next}"]`);
      if (nextNode && nextNode.classList.contains("pending")) {
        setNodeStatus(next, "running", "running");
      }
    }
  });

  source.addEventListener("answer", (event) => {
    const data = JSON.parse(event.data);
    answerEl.textContent = data.answer;
    elapsedEl.textContent = `${data.elapsed.toFixed(2)}s`;
  });

  source.addEventListener("done", (event) => {
    const data = JSON.parse(event.data);
    elapsedEl.textContent = `${data.elapsed.toFixed(2)}s`;
    setRunning(false);
    source.close();
  });

  source.addEventListener("error", (event) => {
    let message = "Stream error";
    if (event.data) {
      const data = JSON.parse(event.data);
      message = data.message;
      elapsedEl.textContent = `${data.elapsed.toFixed(2)}s`;
    }
    appendLog("Error", message);
    nodeOrder.forEach((id) => {
      const node = document.querySelector(`[data-node="${id}"]`);
      if (node && node.classList.contains("running")) {
        setNodeStatus(id, "error", "error");
      }
    });
    setRunning(false);
    if (source) source.close();
  });
}

demoButton.addEventListener("click", () => runGraph("/api/run-demo"));
realButton.addEventListener("click", () => runGraph("/api/run-stage4"));
refreshButton.addEventListener("click", refreshServices);
clearButton.addEventListener("click", () => {
  logEl.innerHTML = "";
  answerEl.textContent = "";
});

refreshServices();
