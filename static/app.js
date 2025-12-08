const tripDate = document.querySelector('#tripDate');
const statusSelect = document.querySelector('#status');
const returnBlock = document.querySelector('#returnBlock');
const pixOptions = document.querySelectorAll('input[name="pix"]');
const pixBlock = document.querySelector('#pixBlock');
const form = document.querySelector('#tripForm');
const feedback = document.querySelector('#feedback');
const driverNameInput = document.querySelector('#driverName');

// Wizard controls
const panes = document.querySelectorAll('[data-step-pane]');
const steps = document.querySelectorAll('.wizard-step');
const progressBar = document.querySelector('#wizardProgress');
const nextBtn = document.querySelector('#nextStep');
const prevBtn = document.querySelector('#prevStep');
const submitBtn = document.querySelector('#submitForm');
let currentStep = 1;

function setToday() {
  if (!tripDate) return;
  const today = new Date();
  const iso = today.toISOString().split('T')[0];
  tripDate.value = iso;
}

function hydrateDriverName() {
  if (!driverNameInput) return;
  const saved = localStorage.getItem('driverName');
  const defaultName = driverNameInput.dataset.default || '';
  if (driverNameInput.value.trim() === '' && defaultName) {
    driverNameInput.value = defaultName;
  }
  if (!driverNameInput.value && saved) {
    driverNameInput.value = saved;
  }
}

function persistDriverName() {
  if (!driverNameInput) return;
  const value = driverNameInput.value.trim();
  if (value.length > 1) {
    localStorage.setItem('driverName', value);
  }
}

function toggleReturnFields() {
  if (!statusSelect || !returnBlock) return;
  const isReturn = statusSelect.value === 'devolucao';
  returnBlock.classList.toggle('hidden', !isReturn);
  if (!isReturn) {
    const container = document.querySelector('#returnedNotesContainer');
    if (container) container.innerHTML = '';
  } else {
    const container = document.querySelector('#returnedNotesContainer');
    if (container && container.childElementCount === 0) {
      generateReturnFields();
    }
  }
}

function generateReturnFields() {
  const count = parseInt(document.querySelector('#returnCount')?.value || 1);
  const container = document.querySelector('#returnedNotesContainer');
  if (!container) return;

  container.innerHTML = '';
  for (let i = 1; i <= count; i++) {
    const item = document.createElement('div');
    item.className = 'return-note-item';
    item.innerHTML = `
      <h4>Nota devolvida ${i}</h4>
      <div class="field">
        <label for="returnedNote${i}">Número da nota</label>
        <input type="text" id="returnedNote${i}" name="returnedNote${i}" placeholder="Ex: NF-12345" required />
      </div>
      <div class="field">
        <label for="returnReason${i}">Motivo da devolução</label>
        <textarea id="returnReason${i}" name="returnReason${i}" rows="3" placeholder="Descreva o motivo" required></textarea>
      </div>
    `;
    container.appendChild(item);
  }
}

function togglePixFields() {
  if (!pixBlock) return;
  const selected = Array.from(pixOptions).find((opt) => opt.checked);
  const isPix = selected?.value === 'sim';
  pixBlock.classList.toggle('hidden', !isPix);
  const proof = document.querySelector('#pixProof');
  if (proof) proof.required = isPix;
}

function showFeedback(message, ok = true) {
  if (!feedback) return;
  feedback.textContent = message;
  feedback.style.color = ok ? 'var(--accent)' : '#f87171';
}

function setStep(step) {
  currentStep = Math.min(Math.max(step, 1), panes.length);

  panes.forEach((pane, idx) => {
    const paneStep = idx + 1;
    pane.classList.toggle('active', paneStep === currentStep);
  });

  steps.forEach((stepEl, idx) => {
    const stepIndex = idx + 1;
    stepEl.classList.toggle('active', stepIndex === currentStep);
    stepEl.classList.toggle('done', stepIndex < currentStep);
  });

  if (progressBar) {
    const pct = ((currentStep - 1) / (panes.length - 1)) * 100;
    progressBar.style.width = `${pct}%`;
  }

  if (prevBtn) prevBtn.style.display = currentStep === 1 ? 'none' : 'inline-flex';
  if (nextBtn) nextBtn.style.display = currentStep === panes.length ? 'none' : 'inline-flex';
  if (submitBtn) submitBtn.style.display = currentStep === panes.length ? 'inline-flex' : 'none';
}

function validateStep(step) {
  const pane = document.querySelector(`[data-step-pane="${step}"]`);
  if (!pane) return true;
  const fields = pane.querySelectorAll('input, select, textarea');
  for (const field of fields) {
    // ignore hidden blocks
    if (field.closest('.hidden')) continue;
    if (!field.checkValidity()) {
      field.reportValidity();
      return false;
    }
  }
  return true;
}

function handleNext() {
  if (!validateStep(currentStep)) return;
  setStep(currentStep + 1);
  showFeedback('');
}

function handlePrev() {
  setStep(currentStep - 1);
  showFeedback('');
}

function previewFiles(inputEl, previewEl, opts = { grid: false }) {
  if (!inputEl || !previewEl) return;
  previewEl.innerHTML = '';
  const files = Array.from(inputEl.files || []);
  files.forEach((file) => {
    const item = document.createElement('div');
    item.className = 'preview-item';

    if (file.type.startsWith('image/')) {
      const img = document.createElement('img');
      img.src = URL.createObjectURL(file);
      img.alt = file.name;
      item.appendChild(img);
    } else {
      item.textContent = file.name;
    }

    previewEl.appendChild(item);
  });
}

if (form) {
  form.addEventListener('submit', (event) => {
    // Só permite enviar se último passo estiver válido
    if (!validateStep(currentStep) || currentStep !== panes.length) {
      event.preventDefault();
      showFeedback('Finalize o passo atual antes de enviar.', false);
      return;
    }
    persistDriverName();
    if (!form.checkValidity()) {
      event.preventDefault();
      showFeedback('Confira os campos obrigatórios.', false);
    } else {
      showFeedback('Viagem registrada.');
    }
  });
}

statusSelect?.addEventListener('change', toggleReturnFields);
pixOptions.forEach((opt) => opt.addEventListener('change', togglePixFields));
driverNameInput?.addEventListener('blur', persistDriverName);

const generateBtn = document.querySelector('#generateReturnFields');
if (generateBtn) {
  generateBtn.addEventListener('click', generateReturnFields);
}

const pixProofInput = document.querySelector('#pixProof');
const pixPreview = document.querySelector('#pixPreview');
pixProofInput?.addEventListener('change', () => previewFiles(pixProofInput, pixPreview));

const canhoteiraInput = document.querySelector('#canhoteira');
const canhoteiraPreview = document.querySelector('#canhoteiraPreview');
canhoteiraInput?.addEventListener('change', () => previewFiles(canhoteiraInput, canhoteiraPreview, { grid: true }));

nextBtn?.addEventListener('click', handleNext);
prevBtn?.addEventListener('click', handlePrev);

document.addEventListener('DOMContentLoaded', () => {
  setToday();
  hydrateDriverName();
  toggleReturnFields();
  togglePixFields();
  setStep(1);
});
