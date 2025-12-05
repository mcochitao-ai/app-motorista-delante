const tripDate = document.querySelector('#tripDate');
const statusSelect = document.querySelector('#status');
const returnBlock = document.querySelector('#returnBlock');
const pixOptions = document.querySelectorAll('input[name="pix"]');
const pixBlock = document.querySelector('#pixBlock');
const form = document.querySelector('#tripForm');
const feedback = document.querySelector('#feedback');
const driverNameInput = document.querySelector('#driverName');

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

if (form) {
  form.addEventListener('submit', (event) => {
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

document.addEventListener('DOMContentLoaded', () => {
  setToday();
  hydrateDriverName();
  toggleReturnFields();
  togglePixFields();
});
