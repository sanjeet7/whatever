const API_BASE = localStorage.getItem('dap-api-base') || 'http://localhost:8000';

const templateForm = document.getElementById('template-form');
const templateList = document.getElementById('template-list');
const toolForm = document.getElementById('tool-form');
const toolList = document.getElementById('tool-list');
const deploymentForm = document.getElementById('deployment-form');
const deploymentList = document.getElementById('deployment-list');
const deploymentTemplateSelect = document.getElementById('deployment-template');
const routeForm = document.getElementById('route-form');
const routeOutput = document.getElementById('route-output');
const improveButton = document.getElementById('improve-button');
const improveOutput = document.getElementById('improve-output');

const state = {
  templates: [],
  tools: [],
  agents: [],
};

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
    ...options,
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(`Request failed: ${response.status} ${response.statusText}\n${detail}`);
  }

  if (response.status === 204) {
    return null;
  }

  return response.json();
}

function renderTemplates() {
  templateList.innerHTML = '';
  deploymentTemplateSelect.innerHTML = '<option value="" disabled selected>Select template</option>';

  state.templates.forEach((template) => {
    const item = document.createElement('div');
    item.className = 'list-item';
    item.innerHTML = `<strong>${template.name}</strong><span>${template.description}</span>`;
    templateList.appendChild(item);

    const option = document.createElement('option');
    option.value = template.id;
    option.textContent = `${template.name} (#${template.id})`;
    deploymentTemplateSelect.appendChild(option);
  });
}

function renderTools() {
  toolList.innerHTML = '';
  state.tools.forEach((tool) => {
    const item = document.createElement('div');
    item.className = 'list-item';
    item.innerHTML = `<strong>${tool.name}</strong><span>${tool.description}</span>`;
    toolList.appendChild(item);
  });
}

function renderAgents() {
  deploymentList.innerHTML = '';
  if (state.agents.length === 0) {
    deploymentList.innerHTML = '<p>No agents deployed yet.</p>';
    return;
  }

  state.agents.forEach((agent) => {
    const item = document.createElement('div');
    item.className = 'list-item';
    const tools = agent.assigned_tools.length ? agent.assigned_tools.join(', ') : 'none';
    item.innerHTML = `
      <strong>${agent.name}</strong>
      <span>Template: ${agent.template_id}</span>
      <span>Owner: ${agent.owner_id || 'n/a'}</span>
      <span>Tools: ${tools}</span>
    `;
    deploymentList.appendChild(item);
  });
}

async function loadInitialData() {
  try {
    const [templates, tools, agents] = await Promise.all([
      request('/templates'),
      request('/tools'),
      request('/agents'),
    ]);
    state.templates = templates;
    state.tools = tools;
    state.agents = agents;
    renderTemplates();
    renderTools();
    renderAgents();
  } catch (error) {
    console.error(error);
    routeOutput.textContent = error.message;
  }
}

templateForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  const name = document.getElementById('template-name').value.trim();
  const description = document.getElementById('template-description').value.trim();
  if (!name || !description) return;

  try {
    const template = await request('/templates', {
      method: 'POST',
      body: JSON.stringify({ name, description }),
    });
    state.templates.push(template);
    renderTemplates();
    templateForm.reset();
  } catch (error) {
    alert(error.message);
  }
});

toolForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  const name = document.getElementById('tool-name').value.trim();
  const description = document.getElementById('tool-description').value.trim();
  if (!name || !description) return;

  try {
    const tool = await request('/tools', {
      method: 'POST',
      body: JSON.stringify({ name, description }),
    });
    state.tools.push(tool);
    renderTools();
    toolForm.reset();
  } catch (error) {
    alert(error.message);
  }
});

deploymentForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  const name = document.getElementById('deployment-name').value.trim();
  const owner = document.getElementById('deployment-owner').value.trim();
  const templateId = deploymentTemplateSelect.value;
  if (!name || !templateId) return;

  try {
    const payload = { name, template_id: Number(templateId) };
    if (owner) payload.owner_id = owner;
    const agent = await request('/agents/deploy', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    state.agents.push(agent);
    renderAgents();
    deploymentForm.reset();
    deploymentTemplateSelect.selectedIndex = 0;
  } catch (error) {
    alert(error.message);
  }
});

routeForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  const userInput = document.getElementById('route-input').value.trim();
  const ownerId = document.getElementById('route-owner').value.trim();
  if (!userInput) return;

  try {
    const body = { user_input: userInput };
    if (ownerId) body.owner_id = ownerId;
    const result = await request('/route', {
      method: 'POST',
      body: JSON.stringify(body),
    });
    routeOutput.textContent = JSON.stringify(result, null, 2);
  } catch (error) {
    routeOutput.textContent = error.message;
  }
});

improveButton.addEventListener('click', async () => {
  const ownerId = document.getElementById('route-owner').value.trim();
  const params = ownerId ? `?owner_id=${encodeURIComponent(ownerId)}` : '';
  try {
    const result = await request(`/self-improve${params}`, { method: 'POST' });
    improveOutput.textContent = JSON.stringify(result, null, 2);
    if (result.generated?.context?.instance) {
      const agents = await request('/agents');
      state.agents = agents;
      renderAgents();
    }
  } catch (error) {
    improveOutput.textContent = error.message;
  }
});

loadInitialData();
