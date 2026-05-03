export function downloadJSON(data, filename = 'risk-register.json') {
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
  _download(blob, filename);
}

export function downloadCSV(csvString, filename = 'risk-register.csv') {
  const blob = new Blob([csvString], { type: 'text/csv' });
  _download(blob, filename);
}

function _download(blob, filename) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}
