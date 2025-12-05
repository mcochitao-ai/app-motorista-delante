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
  const note = document.querySelector('#returnedNote');
  const reason = document.querySelector('#returnReason');
  if (note) note.required = isReturn;
  if (reason) reason.required = isReturn;
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

document.addEventListener('DOMContentLoaded', () => {
  setToday();
  hydrateDriverName();
  toggleReturnFields();
  togglePixFields();
});
