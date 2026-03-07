// Modern Banking App JavaScript

document.addEventListener('DOMContentLoaded', function() {
  initForms();
  highlightRecentTransactions();
  formatAllBalances();
  loadDarkModePreference();
});

// -------- Dashboard stats (optional endpoint /api/stats) --------

async function refreshDashboard() {
  try {
    const res = await fetch('/api/stats');
    if (!res.ok) return;
    const data = await res.json();
    updateStatsDisplay(data);
  } catch (e) {
    console.log('Stats refresh failed:', e);
  }
}

function updateStatsDisplay(data) {
  const customersEl = document.querySelector('.total-customers');
  const accountsEl = document.querySelector('.total-accounts');
  const balanceEl = document.querySelector('.total-balance');

  if (customersEl) animateNumber(customersEl, data.customers);
  if (accountsEl) animateNumber(accountsEl, data.accounts);
  if (balanceEl) balanceEl.textContent = formatCurrency(data.balance);
}

function animateNumber(element, target) {
  const start = parseInt(element.textContent) || 0;
  const duration = 800;
  const startTime = performance.now();

  function step(currentTime) {
    const progress = Math.min((currentTime - startTime) / duration, 1);
    const ease = 1 - Math.pow(1 - progress, 3);
    element.textContent = Math.floor(ease * target).toLocaleString();
    if (progress < 1) requestAnimationFrame(step);
  }
  requestAnimationFrame(step);
}

// -------- Formatting helpers --------

function formatCurrency(amount) {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    minimumFractionDigits: 2
  }).format(amount || 0);
}

function formatAllBalances() {
  document.querySelectorAll('.balance').forEach(el => {
    const num = parseFloat(el.dataset.value || el.textContent);
    el.textContent = formatCurrency(num);
  });
}

// -------- Forms & validation --------

function initForms() {
  document.querySelectorAll('form').forEach(form => {
    form.addEventListener('submit', function(e) {
      const amountInputs = form.querySelectorAll('input[name="amount"]');
      let ok = true;

      amountInputs.forEach(input => {
        const amount = parseFloat(input.value);
        if (isNaN(amount) || amount <= 0) {
          ok = false;
          input.style.borderColor = '#ef4444';
        }
        const maxBalance = parseFloat(input.dataset.maxBalance);
        if (!isNaN(maxBalance) && amount > maxBalance) {
          ok = false;
          input.style.borderColor = '#ef4444';
          showMessage(
            'Amount exceeds available balance: ' + formatCurrency(maxBalance),
            'error'
          );
        }
      });

      if (!ok) {
        e.preventDefault();
        showMessage('Please fix the highlighted fields.', 'error');
        return;
      }

      const btn = form.querySelector('button[type="submit"]');
      if (btn) {
        const original = btn.textContent;
        btn.textContent = 'Processing...';
        btn.disabled = true;
        setTimeout(() => {
          btn.textContent = original;
          btn.disabled = false;
        }, 2000);
      }
    });

    form.querySelectorAll('input').forEach(input => {
      input.addEventListener('input', function() {
        this.style.borderColor = '#e2e8f0';
      });
    });
  });

  document.addEventListener('input', function(e) {
    if (e.target.matches('input[name="amount"]')) {
      const amount = parseFloat(e.target.value);
      const maxBalance = parseFloat(e.target.dataset.maxBalance);
      if (!isNaN(maxBalance) && amount > maxBalance) {
        e.target.style.borderColor = '#ef4444';
      } else if (!isNaN(amount) && amount > 0) {
        e.target.style.borderColor = '#10b981';
      } else {
        e.target.style.borderColor = '#e2e8f0';
      }
    }
  });
}

// -------- Transactions table UX --------

function highlightRecentTransactions() {
  const rows = document.querySelectorAll('table tr');
  const dataRows = Array.from(rows).slice(1, 6);
  dataRows.forEach((row, i) => {
    row.style.transition = 'background 0.3s ease, transform 0.3s ease';
  });

  document.addEventListener('click', function(e) {
    const row = e.target.closest('tr');
    if (!row || row.parentNode.tagName !== 'TBODY') return;
    row.style.transform = 'scale(1.02)';
    setTimeout(() => {
      row.style.transform = 'scale(1)';
    }, 200);
  });
}

// -------- Flash messages --------

function showMessage(text, type) {
  const container = document.getElementById('flash-messages') || document.body;
  const msg = document.createElement('div');
  msg.className = 'message ' + (type || 'success');
  msg.textContent = text;
  container.prepend(msg);
  setTimeout(() => {
    msg.style.opacity = '0';
    setTimeout(() => msg.remove(), 300);
  }, 4000);
}

// -------- CSV export & print --------

window.exportCSV = function() {
  const rows = document.querySelectorAll('table tr');
  if (!rows.length) {
    showMessage('No data to export.', 'error');
    return;
  }
  const csv = [];
  rows.forEach(row => {
    const cols = row.querySelectorAll('th, td');
    if (!cols.length) return;
    const vals = Array.from(cols).map(col =>
      '"' + col.textContent.replace(/"/g, '""') + '"'
    );
    csv.push(vals.join(','));
  });
  const blob = new Blob([csv.join('\n')], { type: 'text/csv' });
  const link = document.createElement('a');
  link.href = URL.createObjectURL(blob);
  link.download = 'transactions.csv';
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
};

window.printReport = function() {
  window.print();
};

// -------- Keyboard shortcuts & dark mode --------

document.addEventListener('keydown', function(e) {
  if (e.ctrlKey || e.metaKey) {
    if (e.key === '1') {
      e.preventDefault();
      window.location.href = '/';
    } else if (e.key === '2') {
      e.preventDefault();
      window.location.href = '/customers/new';
    } else if (e.key === '3') {
      e.preventDefault();
      window.location.href = '/accounts';
    } else if (e.key.toLowerCase() === 'd') {
      e.preventDefault();
      toggleDarkMode();
    }
  }
});

function toggleDarkMode() {
  document.body.classList.toggle('dark-mode');
  localStorage.setItem(
    'darkMode',
    document.body.classList.contains('dark-mode') ? 'true' : 'false'
  );
}

function loadDarkModePreference() {
  if (localStorage.getItem('darkMode') === 'true') {
    document.body.classList.add('dark-mode');
  }
}
