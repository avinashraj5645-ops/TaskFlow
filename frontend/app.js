// ---------------------------------------------------------------------------
// TaskFlow frontend logic.
// CHANGEABLE: point this at wherever your backend actually runs.
// ---------------------------------------------------------------------------
const API_BASE = "https://taskflow-y6lj.onrender.com";
const CACHE_KEY = "taskflow_cached_tasks";

// CHANGEABLE: hard-code a project to add tasks into, or wire a project
// picker later. Seed data (seed.py) creates project id 1.
const ACTIVE_PROJECT_ID = 1;

const taskListEl = document.getElementById("task-list");
const emptyStateEl = document.getElementById("empty-state");
const taskForm = document.getElementById("task-form");
const quickAddForm = document.getElementById("quickadd-form");
const titleInput = document.getElementById("title");
const titleError = document.getElementById("title-error");
const sortSelect = document.getElementById("sort-select");
const searchInput = document.getElementById("search-input");

document.getElementById("api-base-label").textContent = API_BASE;

let currentTasks = [];

// ---------------------------------------------------------------------------
// Cache helpers (Task 14) — localStorage is a cache of real backend data,
// never a substitute for it.
// ---------------------------------------------------------------------------
function cacheTasks(tasks) {
  try {
    localStorage.setItem(CACHE_KEY, JSON.stringify(tasks));
  } catch (e) {
    console.warn("Could not cache tasks:", e);
  }
}

function readCachedTasks() {
  try {
    const raw = localStorage.getItem(CACHE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch (e) {
    return [];
  }
}

// ---------------------------------------------------------------------------
// Rendering — createElement/appendChild only, textContent for user input.
// ---------------------------------------------------------------------------
function renderTasks(tasks) {
  taskListEl.innerHTML = ""; // safe: clearing, not inserting user data
  emptyStateEl.hidden = tasks.length > 0;

  tasks.forEach((task) => {
    const item = document.createElement("div");
    item.className = "task-item";
    item.dataset.priority = task.priority;
    item.dataset.taskId = task.id;

    const main = document.createElement("div");
    main.className = "task-item__main";

    const title = document.createElement("span");
    title.className = "task-item__title";
    title.textContent = task.title; // textContent, never innerHTML, for user data

    const meta = document.createElement("div");
    meta.className = "task-item__meta";

    const badge = document.createElement("span");
    badge.className = `badge badge--${task.priority}`;
    badge.textContent = task.priority;
    meta.appendChild(badge);

    if (task.due_date) {
      const due = document.createElement("span");
      due.textContent = `due ${task.due_date}`;
      meta.appendChild(due);
    }

    const status = document.createElement("span");
    status.textContent = task.status;
    meta.appendChild(status);

    main.appendChild(title);
    main.appendChild(meta);

    const actions = document.createElement("div");
    actions.className = "task-item__actions";

    const editBtn = document.createElement("button");
    editBtn.className = "icon-btn";
    editBtn.textContent = "Cycle status";
    editBtn.addEventListener("click", () => cycleStatus(task));

    const deleteBtn = document.createElement("button");
    deleteBtn.className = "icon-btn icon-btn--danger";
    deleteBtn.textContent = "Delete";
    deleteBtn.addEventListener("click", () => deleteTask(task.id));

    actions.appendChild(editBtn);
    actions.appendChild(deleteBtn);

    item.appendChild(main);
    item.appendChild(actions);
    taskListEl.appendChild(item);
  });

  updateStats(tasks);
}

function updateStats(tasks) {
  document.getElementById("stat-total").textContent = tasks.length;
  document.getElementById("stat-low").textContent = tasks.filter((t) => t.priority === "low").length;
  document.getElementById("stat-medium").textContent = tasks.filter((t) => t.priority === "medium").length;
  document.getElementById("stat-high").textContent = tasks.filter((t) => t.priority === "high").length;
}

// ---------------------------------------------------------------------------
// Backend calls (Fetch API) — real end-to-end wiring, no mock data layer.
// ---------------------------------------------------------------------------
async function loadTasks(sort = "") {
  const url = sort ? `${API_BASE}/tasks?sort=${sort}` : `${API_BASE}/tasks`;
  try {
    const res = await fetch(url);
    if (!res.ok) throw new Error(`GET /tasks failed: ${res.status}`);
    const tasks = await res.json();
    currentTasks = tasks;
    cacheTasks(tasks);
    renderTasks(tasks);
  } catch (err) {
    console.error(err);
    // Backend unreachable — keep showing the cached copy already rendered.
  }
}

async function createTask(payload) {
  const res = await fetch(`${API_BASE}/tasks`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const detail = await res.json().catch(() => ({}));
    throw new Error(detail.detail ? JSON.stringify(detail.detail) : `Create failed: ${res.status}`);
  }
  return res.json();
}

async function quickAddTask(description) {
  const res = await fetch(`${API_BASE}/tasks/quick-add`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ description, project_id: ACTIVE_PROJECT_ID }),
  });
  if (!res.ok) {
    const detail = await res.json().catch(() => ({}));
    throw new Error(detail.detail ? JSON.stringify(detail.detail) : `Quick-add failed: ${res.status}`);
  }
  return res.json();
}

async function updateTaskStatus(taskId, status) {
  const res = await fetch(`${API_BASE}/tasks/${taskId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ status }),
  });
  if (!res.ok) throw new Error(`Update failed: ${res.status}`);
  return res.json();
}

async function deleteTask(taskId) {
  try {
    const res = await fetch(`${API_BASE}/tasks/${taskId}`, { method: "DELETE" });
    if (!res.ok) throw new Error(`Delete failed: ${res.status}`);
    currentTasks = currentTasks.filter((t) => t.id !== taskId);
    cacheTasks(currentTasks);
    renderTasks(currentTasks);
  } catch (err) {
    console.error(err);
    alert("Could not delete task — check the backend is running.");
  }
}

const STATUS_CYCLE = ["todo", "in_progress", "done"];
async function cycleStatus(task) {
  const next = STATUS_CYCLE[(STATUS_CYCLE.indexOf(task.status) + 1) % STATUS_CYCLE.length];
  try {
    const updated = await updateTaskStatus(task.id, next);
    currentTasks = currentTasks.map((t) => (t.id === updated.id ? updated : t));
    cacheTasks(currentTasks);
    renderTasks(currentTasks);
  } catch (err) {
    console.error(err);
    alert("Could not update task — check the backend is running.");
  }
}

// ---------------------------------------------------------------------------
// Add-task form: client-side validation + preventDefault + real POST
// ---------------------------------------------------------------------------
taskForm.addEventListener("submit", async (event) => {
  event.preventDefault();

  const title = titleInput.value.trim();
  if (!title) {
    titleError.textContent = "Title is required.";
    return;
  }
  titleError.textContent = "";

  const priority = document.getElementById("priority").value;
  const dueDate = document.getElementById("due_date").value.trim() || null;

  try {
    const created = await createTask({
      title,
      priority,
      due_date: dueDate,
      project_id: ACTIVE_PROJECT_ID,
    });
    currentTasks = [...currentTasks, created];
    cacheTasks(currentTasks);
    renderTasks(currentTasks);
    taskForm.reset();
  } catch (err) {
    console.error(err);
    alert(`Could not add task: ${err.message}`);
  }
});

titleInput.addEventListener("input", () => {
  if (titleInput.value.trim()) {
    titleError.textContent = "";
  }
});

// ---------------------------------------------------------------------------
// Quick-add form
// ---------------------------------------------------------------------------
quickAddForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const input = document.getElementById("quickadd-input");
  const description = input.value.trim();
  if (!description) return;

  try {
    const created = await quickAddTask(description);
    currentTasks = [...currentTasks, created];
    cacheTasks(currentTasks);
    renderTasks(currentTasks);
    input.value = "";
  } catch (err) {
    console.error(err);
    alert(`Quick-add failed: ${err.message}`);
  }
});

// ---------------------------------------------------------------------------
// Sort + search controls
// ---------------------------------------------------------------------------
sortSelect.addEventListener("change", () => loadTasks(sortSelect.value));

searchInput.addEventListener("keydown", async (event) => {
  if (event.key !== "Enter") return;
  const title = searchInput.value.trim();
  if (!title) {
    loadTasks(sortSelect.value);
    return;
  }
  try {
    const res = await fetch(`${API_BASE}/tasks/search?title=${encodeURIComponent(title)}&algo=binary`);
    if (res.status === 404) {
      renderTasks([]);
      return;
    }
    if (!res.ok) throw new Error(`Search failed: ${res.status}`);
    const task = await res.json();
    renderTasks([task]);
  } catch (err) {
    console.error(err);
  }
});

// ---------------------------------------------------------------------------
// Boot: render cached copy immediately, then refresh from the live backend.
// ---------------------------------------------------------------------------
(function init() {
  const cached = readCachedTasks();
  if (cached.length) {
    currentTasks = cached;
    renderTasks(cached);
  }
  loadTasks();
})();


searchInput.addEventListener("input", () => {
  if (!searchInput.value.trim()) {
    loadTasks(sortSelect.value);
  }
});