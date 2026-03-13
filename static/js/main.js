(function () {
  'use strict';

  // ── DOM references ──────────────────────────────────────────────────
  const dropzone     = document.getElementById('dropzone');
  const fileInput    = document.getElementById('fileInput');
  const fileInfo     = document.getElementById('fileInfo');
  const fileName     = document.getElementById('fileName');
  const clearFile    = document.getElementById('clearFile');
  const generateBtn  = document.getElementById('generateBtn');
  const btnText      = document.getElementById('btnText');
  const btnSpinner   = document.getElementById('btnSpinner');
  const errorBanner  = document.getElementById('errorBanner');
  const reportSection = document.getElementById('reportSection');
  const reportContent = document.getElementById('reportContent');
  const copyMdBtn    = document.getElementById('copyMdBtn');
  const downloadMdBtn = document.getElementById('downloadMdBtn');

  let selectedFile = null;
  let lastMarkdown = '';

  // ── Helpers ─────────────────────────────────────────────────────────
  function showError(msg) {
    errorBanner.textContent = msg;
    errorBanner.classList.remove('hidden');
  }

  function clearError() {
    errorBanner.classList.add('hidden');
    errorBanner.textContent = '';
  }

  function setFile(file) {
    selectedFile = file;
    fileName.textContent = file.name;
    fileInfo.classList.remove('hidden');
    generateBtn.disabled = false;
    clearError();
    reportSection.classList.add('hidden');
  }

  function resetFile() {
    selectedFile = null;
    fileInput.value = '';
    fileInfo.classList.add('hidden');
    generateBtn.disabled = true;
  }

  function setLoading(loading) {
    generateBtn.disabled = loading;
    btnText.textContent = loading ? '분석 중…' : '보고서 생성';
    btnSpinner.classList.toggle('hidden', !loading);
  }

  // ── Dropzone events ──────────────────────────────────────────────────
  dropzone.addEventListener('click', () => fileInput.click());
  dropzone.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      fileInput.click();
    }
  });

  dropzone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropzone.classList.add('drag-over');
  });

  dropzone.addEventListener('dragleave', () => dropzone.classList.remove('drag-over'));

  dropzone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropzone.classList.remove('drag-over');
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  });

  fileInput.addEventListener('change', () => {
    if (fileInput.files.length) handleFile(fileInput.files[0]);
  });

  clearFile.addEventListener('click', () => {
    resetFile();
    clearError();
  });

  // ── File validation ──────────────────────────────────────────────────
  const ALLOWED_TYPES = ['text/plain', 'text/csv', 'application/json', 'text/tab-separated-values'];
  const ALLOWED_EXTS  = /\.(txt|csv|json)$/i;
  const MAX_BYTES     = 5 * 1024 * 1024;

  function handleFile(file) {
    clearError();

    if (!ALLOWED_EXTS.test(file.name)) {
      showError('지원하지 않는 파일 형식입니다. TXT, CSV, JSON 파일만 업로드할 수 있습니다.');
      return;
    }

    if (file.type && !ALLOWED_TYPES.includes(file.type)) {
      showError('지원하지 않는 파일 형식입니다. TXT, CSV, JSON 파일만 업로드할 수 있습니다.');
      return;
    }

    if (file.size > MAX_BYTES) {
      showError('파일 크기가 5 MB를 초과합니다.');
      return;
    }

    setFile(file);
  }

  // ── Generate report ──────────────────────────────────────────────────
  generateBtn.addEventListener('click', async () => {
    if (!selectedFile) return;

    clearError();
    setLoading(true);
    reportSection.classList.add('hidden');

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      const response = await fetch('/generate', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        showError(data.error || '오류가 발생했습니다. 다시 시도해 주세요.');
        return;
      }

      lastMarkdown = data.report_md || '';
      reportContent.innerHTML = data.report_html || '';
      reportSection.classList.remove('hidden');
      reportSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    } catch (err) {
      showError('네트워크 오류가 발생했습니다. 인터넷 연결을 확인하고 다시 시도해 주세요.');
    } finally {
      setLoading(false);
    }
  });

  // ── Copy Markdown ────────────────────────────────────────────────────
  copyMdBtn.addEventListener('click', async () => {
    if (!lastMarkdown) return;
    try {
      await navigator.clipboard.writeText(lastMarkdown);
      const original = copyMdBtn.textContent;
      copyMdBtn.textContent = '✅ 복사됨';
      setTimeout(() => { copyMdBtn.textContent = original; }, 2000);
    } catch {
      showError('클립보드 복사에 실패했습니다.');
    }
  });

  // ── Download Markdown ────────────────────────────────────────────────
  downloadMdBtn.addEventListener('click', () => {
    if (!lastMarkdown) return;
    const blob = new Blob([lastMarkdown], { type: 'text/markdown;charset=utf-8' });
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement('a');
    a.href     = url;
    a.download = 'ux-research-report.md';
    a.click();
    URL.revokeObjectURL(url);
  });
})();
