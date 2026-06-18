/* ============================================================
   PolicyMind — Frontend Application
   Handles upload, query, and result rendering
   ============================================================ */

// ---------- Configuration ----------
const API_BASE = '';  // same origin

// ---------- State ----------
const state = {
  documents: [],       // { id, name, selected }
  isUploading: false,
  isQuerying: false,
};

// ---------- DOM Ready ----------
document.addEventListener('DOMContentLoaded', () => {
  initParticles();
  initDropzone();
  initQueryForm();
  initArchitectureAnimation();
  initThemeToggle();
});

// ============================================================
// PARTICLES
// ============================================================
function initParticles() {
  const container = document.querySelector('.particles');
  if (!container) return;
  const count = 30;
  for (let i = 0; i < count; i++) {
    const p = document.createElement('div');
    p.classList.add('particle');
    p.style.left = `${Math.random() * 100}%`;
    p.style.animationDuration = `${8 + Math.random() * 12}s`;
    p.style.animationDelay = `${Math.random() * 10}s`;
    p.style.width = `${1 + Math.random() * 2}px`;
    p.style.height = p.style.width;
    if (Math.random() > 0.5) {
      p.style.background = 'var(--accent-violet)';
    }
    container.appendChild(p);
  }
}

// ============================================================
// TOAST NOTIFICATIONS
// ============================================================
function showToast(message, type = 'info') {
  const container = document.querySelector('.toast-container');
  const icons = {
    success: '✓',
    error: '✕',
    info: 'ℹ',
  };

  const toast = document.createElement('div');
  toast.className = `toast toast--${type}`;
  toast.innerHTML = `
    <span class="toast__icon">${icons[type] || icons.info}</span>
    <span class="toast__message">${message}</span>
    <button class="toast__close" onclick="this.parentElement.classList.add('toast--leaving'); setTimeout(() => this.parentElement.remove(), 300)">✕</button>
  `;

  container.appendChild(toast);
  setTimeout(() => {
    if (toast.parentElement) {
      toast.classList.add('toast--leaving');
      setTimeout(() => toast.remove(), 300);
    }
  }, 4500);
}

// ============================================================
// FILE UPLOAD / DROPZONE
// ============================================================
function initDropzone() {
  const dropzone = document.getElementById('dropzone');
  const fileInput = document.getElementById('fileInput');
  if (!dropzone || !fileInput) return;

  // Click to browse
  dropzone.addEventListener('click', () => fileInput.click());

  // Drag events
  ['dragenter', 'dragover'].forEach(evt => {
    dropzone.addEventListener(evt, e => {
      e.preventDefault();
      dropzone.classList.add('dropzone--active');
    });
  });

  ['dragleave', 'drop'].forEach(evt => {
    dropzone.addEventListener(evt, e => {
      e.preventDefault();
      dropzone.classList.remove('dropzone--active');
    });
  });

  dropzone.addEventListener('drop', e => {
    const files = e.dataTransfer.files;
    if (files.length > 0) handleFileUpload(files[0]);
  });

  fileInput.addEventListener('change', () => {
    if (fileInput.files.length > 0) {
      handleFileUpload(fileInput.files[0]);
      fileInput.value = '';
    }
  });
}

async function handleFileUpload(file) {
  const allowedExts = ['.pdf', '.docx', '.txt', '.pptx'];
  const ext = '.' + file.name.split('.').pop().toLowerCase();
  if (!allowedExts.includes(ext)) {
    showToast(`Unsupported format: ${ext}. Allowed: PDF, DOCX, TXT, PPTX`, 'error');
    return;
  }

  if (state.isUploading) return;
  state.isUploading = true;

  const progress = document.getElementById('uploadProgress');
  const progressFill = document.getElementById('progressFill');
  const statusText = document.getElementById('uploadStatus');

  progress.classList.add('active');
  progressFill.classList.add('progress-bar__fill--indeterminate');
  progressFill.style.width = '30%';
  statusText.textContent = `Uploading ${file.name}...`;

  try {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_BASE}/upload`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const err = await response.json().catch(() => ({ detail: 'Upload failed' }));
      throw new Error(err.detail || `HTTP ${response.status}`);
    }

    const data = await response.json();

    // Animate progress completion
    progressFill.classList.remove('progress-bar__fill--indeterminate');
    progressFill.style.width = '100%';
    statusText.textContent = 'Processing in background...';

    setTimeout(() => {
      progress.classList.remove('active');
      progressFill.style.width = '0%';
    }, 2000);

    // Add to document list
    addDocument(data.document_id, file.name);
    showToast(`"${file.name}" uploaded successfully!`, 'success');

  } catch (err) {
    progressFill.classList.remove('progress-bar__fill--indeterminate');
    progressFill.style.width = '0%';
    statusText.textContent = '';
    progress.classList.remove('active');
    showToast(`Upload failed: ${err.message}`, 'error');
  } finally {
    state.isUploading = false;
  }
}

function addDocument(id, name) {
  state.documents.push({ id, name, selected: true });
  renderDocumentList();
}

function renderDocumentList() {
  const list = document.getElementById('documentList');
  if (!list) return;

  if (state.documents.length === 0) {
    list.innerHTML = `
      <div class="empty-state">
        <div class="empty-state__icon">📄</div>
        <div class="empty-state__text">No documents uploaded yet</div>
      </div>
    `;
    return;
  }

  list.innerHTML = state.documents.map((doc, i) => `
    <div class="document-item anim-fade-in-up">
      <span class="document-item__icon">📄</span>
      <div class="document-item__info">
        <div class="document-item__name">${escapeHtml(doc.name)}</div>
        <div class="document-item__id">${doc.id}</div>
      </div>
      <span class="document-item__status">Indexed</span>
      <label class="document-item__check" title="Include in queries">
        <input type="checkbox" ${doc.selected ? 'checked' : ''} onchange="toggleDocSelection(${i})">
      </label>
    </div>
  `).join('');
}

function toggleDocSelection(index) {
  state.documents[index].selected = !state.documents[index].selected;
}

// ============================================================
// QUERY FLOW
// ============================================================
function initQueryForm() {
  const form = document.getElementById('queryForm');
  if (!form) return;
  form.addEventListener('submit', handleQuery);
}

async function handleQuery(e) {
  e.preventDefault();
  if (state.isQuerying) return;

  const textarea = document.getElementById('queryInput');
  const question = textarea.value.trim();
  if (!question) {
    showToast('Please enter a question', 'error');
    return;
  }

  const selectedDocs = state.documents.filter(d => d.selected).map(d => d.id);

  const includeLogic = document.getElementById('includeLogic')?.checked ?? true;

  state.isQuerying = true;
  const btn = document.getElementById('queryBtn');
  btn.classList.add('btn--loading');
  btn.disabled = true;

  // Show shimmer loading
  showResultsLoading();

  // Animate architecture pipeline
  animatePipeline();

  try {
    const body = {
      question,
      include_logic: includeLogic,
      max_results: 5,
    };
    if (selectedDocs.length > 0) {
      body.document_ids = selectedDocs;
    }

    const response = await fetch(`${API_BASE}/query`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      const err = await response.json().catch(() => ({ detail: 'Query failed' }));
      throw new Error(err.detail || `HTTP ${response.status}`);
    }

    const data = await response.json();
    renderResults(data);
    showToast('Answer generated successfully!', 'success');

  } catch (err) {
    hideResults();
    showToast(`Query failed: ${err.message}`, 'error');
  } finally {
    state.isQuerying = false;
    btn.classList.remove('btn--loading');
    btn.disabled = false;
  }
}

// ============================================================
// RESULTS RENDERING
// ============================================================
function showResultsLoading() {
  const section = document.getElementById('resultsSection');
  section.classList.add('active');
  document.getElementById('answerContent').innerHTML = `
    <div class="shimmer shimmer-line" style="width:100%"></div>
    <div class="shimmer shimmer-line" style="width:85%"></div>
    <div class="shimmer shimmer-line" style="width:70%"></div>
  `;
  document.getElementById('answerMeta').innerHTML = '';
  document.getElementById('clausesGrid').innerHTML = '';
  document.getElementById('confidenceValue').textContent = '—';

  const ring = document.querySelector('.confidence-ring__fill');
  if (ring) ring.style.strokeDashoffset = 113;

  const logicContainer = document.getElementById('logicTreeContainer');
  logicContainer.classList.remove('active');

  section.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function hideResults() {
  document.getElementById('resultsSection').classList.remove('active');
}

function renderResults(data) {
  const section = document.getElementById('resultsSection');
  section.classList.add('active');

  // 1. Typewriter answer
  const answerEl = document.getElementById('answerContent');
  answerEl.innerHTML = '';
  typewriterEffect(answerEl, data.answer || 'No answer generated.');

  // 2. Confidence gauge
  const confidence = data.confidence ?? 0;
  const pct = Math.round(confidence * 100);
  document.getElementById('confidenceValue').textContent = `${pct}%`;

  const ring = document.querySelector('.confidence-ring__fill');
  if (ring) {
    const offset = 113 - (113 * confidence);
    setTimeout(() => { ring.style.strokeDashoffset = offset; }, 300);
  }

  // Update ring color based on confidence
  if (ring) {
    if (confidence >= 0.7) ring.style.stroke = 'var(--accent-green)';
    else if (confidence >= 0.4) ring.style.stroke = 'var(--accent-amber)';
    else ring.style.stroke = 'var(--accent-red)';
  }

  // 3. Meta info
  const metaEl = document.getElementById('answerMeta');
  metaEl.innerHTML = `
    ${data.query_intent ? `
      <div class="meta-item">
        <span class="meta-item__label">Query Intent</span>
        <span class="meta-item__value">${escapeHtml(data.query_intent)}</span>
      </div>` : ''}
    <div class="meta-item">
      <span class="meta-item__label">Sources Used</span>
      <span class="meta-item__value">${data.clauses_used?.length || 0} clauses</span>
    </div>
    ${data.entities && Object.keys(data.entities).length > 0 ? `
      <div class="meta-item">
        <span class="meta-item__label">Entities</span>
        <span class="meta-item__value">${Object.entries(data.entities).map(([k, v]) => `${k}: ${v}`).join(', ')}</span>
      </div>` : ''}
  `;

  // 4. Clauses
  renderClauses(data.clauses_used || []);

  // 5. Logic tree
  if (data.logic_tree) {
    renderLogicTree(data.logic_tree);
  } else {
    document.getElementById('logicTreeContainer').classList.remove('active');
  }
}

function renderClauses(clauses) {
  const grid = document.getElementById('clausesGrid');
  if (clauses.length === 0) {
    grid.innerHTML = `
      <div class="empty-state">
        <div class="empty-state__text">No clauses found</div>
      </div>
    `;
    return;
  }

  grid.innerHTML = clauses.map((clause, i) => {
    const score = (clause.relevance_score * 100).toFixed(0);
    return `
      <div class="clause-card glass-panel anim-fade-in-up anim-delay-${Math.min(i + 1, 5)}" onclick="this.classList.toggle('expanded')">
        <div class="clause-card__header">
          <div class="clause-card__title">
            <span>§</span>
            ${escapeHtml(clause.title || 'Untitled Section')}
          </div>
          <div class="clause-card__score">
            <div class="relevance-bar">
              <div class="relevance-bar__fill" style="width: ${score}%"></div>
            </div>
            <span class="clause-card__score-text">${score}%</span>
            <span class="clause-card__chevron">▼</span>
          </div>
        </div>
        <div class="clause-card__text">${escapeHtml(clause.text || '')}</div>
        <div class="clause-card__meta">
          ${clause.clause_id ? `<span class="clause-meta-tag">Clause #${escapeHtml(clause.clause_id)}</span>` : ''}
          <span class="clause-meta-tag">${escapeHtml(clause.document_id || '')}</span>
          ${clause.page ? `<span class="clause-meta-tag">Page ${clause.page}</span>` : ''}
        </div>
      </div>
    `;
  }).join('');
}

function renderLogicTree(tree) {
  const container = document.getElementById('logicTreeContainer');
  const treeEl = document.getElementById('logicTree');
  container.classList.add('active');
  treeEl.innerHTML = buildTreeHTML(tree);
}

function buildTreeHTML(node) {
  if (!node) return '';
  const typeClass = node.type ? node.type.toLowerCase() : 'and';

  let html = `<div class="tree-node">`;
  html += `<div class="tree-node__type tree-node__type--${typeClass}">
    ${node.type || 'AND'}
    ${node.result !== null && node.result !== undefined ? `<span style="margin-left:8px;opacity:0.7">${node.result ? '✓ True' : '✕ False'}</span>` : ''}
  </div>`;

  if (node.conditions && node.conditions.length > 0) {
    node.conditions.forEach(cond => {
      if (cond.conditions) {
        // Nested tree
        html += buildTreeHTML(cond);
      } else {
        // Leaf condition
        const statusClass = cond.is_met ? 'met' : 'unmet';
        const statusIcon = cond.is_met ? '✓' : '✕';
        html += `
          <div class="tree-condition">
            <div class="tree-condition__status tree-condition__status--${statusClass}">${statusIcon}</div>
            <div class="tree-condition__text">${escapeHtml(cond.condition || '')}</div>
            ${cond.source_clause_id ? `<span class="tree-condition__source">§ ${escapeHtml(cond.source_clause_id)}</span>` : ''}
          </div>
        `;
      }
    });
  }

  html += `</div>`;
  return html;
}

// ============================================================
// TYPEWRITER EFFECT
// ============================================================
function typewriterEffect(element, text, speed = 12) {
  let i = 0;
  const cursor = document.createElement('span');
  cursor.className = 'typewriter-cursor';
  element.textContent = '';
  element.appendChild(cursor);

  function type() {
    if (i < text.length) {
      const chunk = text.substring(i, Math.min(i + 3, text.length));
      cursor.before(document.createTextNode(chunk));
      i += 3;
      setTimeout(type, speed);
    } else {
      // Remove cursor after short delay
      setTimeout(() => cursor.remove(), 1500);
    }
  }

  type();
}

// ============================================================
// ARCHITECTURE PIPELINE ANIMATION
// ============================================================
function initArchitectureAnimation() {
  const steps = document.querySelectorAll('.pipeline-step');
  if (steps.length === 0) return;

  // Intersection observer to trigger animation on scroll
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        animatePipelineSequential();
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.3 });

  const section = document.querySelector('.architecture-section');
  if (section) observer.observe(section);
}

function animatePipelineSequential() {
  const steps = document.querySelectorAll('.pipeline-step');
  steps.forEach((step, i) => {
    setTimeout(() => step.classList.add('active'), i * 300);
  });
}

function animatePipeline() {
  const steps = document.querySelectorAll('.pipeline-step');
  // Reset
  steps.forEach(s => s.classList.remove('active'));
  // Animate each step
  animatePipelineSequential();
}

// ============================================================
// THEME TOGGLE (future use)
// ============================================================
function initThemeToggle() {
  // Currently dark-only, placeholder for light mode toggle
}

// ============================================================
// UTILITIES
// ============================================================
function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}
