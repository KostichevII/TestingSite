

/* ============================================================
 *  СОХРАНЕНИЕ ТЕСТА В ФАЙЛ С ШИФРОВАНИЕМ ПРАВИЛЬНЫХ ОТВЕТОВ
 * ============================================================ */

// --- Настройки крипто ---
const CRYPTO_CONFIG = {
  // ВАЖНО: та же фраза должна быть в Python-коде расшифровки.
  // Меняйте её на что-то своё.
  PASSPHRASE: 'TestIt::v1::change-me-please',
  ITERATIONS: 100_000,
  SALT_LENGTH: 16,   // байт
  IV_LENGTH: 12,     // байт для AES-GCM
};

// ---------- Утилиты кодирования ----------

function bufToBase64(buf) {
  const bytes = new Uint8Array(buf);
  let binary = '';
  for (let i = 0; i < bytes.length; i++) binary += String.fromCharCode(bytes[i]);
  return btoa(binary);
}

function base64ToBuf(b64) {
  const binary = atob(b64);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
  return bytes;
}

// ---------- Ключ из парольной фразы (PBKDF2 → AES-GCM 256) ----------

async function deriveKey(passphrase, salt) {
  const enc = new TextEncoder();
  const baseKey = await crypto.subtle.importKey(
    'raw', enc.encode(passphrase), 'PBKDF2', false, ['deriveKey']
  );
  return crypto.subtle.deriveKey(
    { name: 'PBKDF2', salt, iterations: CRYPTO_CONFIG.ITERATIONS, hash: 'SHA-256' },
    baseKey,
    { name: 'AES-GCM', length: 256 },
    false,
    ['encrypt', 'decrypt']
  );
}

// ---------- Шифрование произвольного JSON-значения ----------

async function encryptJson(value, key) {
  const iv = crypto.getRandomValues(new Uint8Array(CRYPTO_CONFIG.IV_LENGTH));
  const plaintext = new TextEncoder().encode(JSON.stringify(value));
  const ciphertext = await crypto.subtle.encrypt(
    { name: 'AES-GCM', iv }, key, plaintext
  );
  return {
    alg: 'AES-GCM-256',
    iv: bufToBase64(iv),
    ct: bufToBase64(ciphertext),
  };
}

// ---------- Сбор данных из DOM формы ----------

function collectTestFromForm() {
  const form = document.getElementById('quiz-form');
  const blocks = form.querySelectorAll('.question-block');
  const questions = [];

  blocks.forEach((block, qi) => {
    const type = block.querySelector('.q-type').value;
    const text = block.querySelector('textarea[name$="-text"]').value.trim();
    const points = parseInt(block.querySelector('input[name$="-points"]').value, 10) || 1;

    if (!text) return; // пустые вопросы пропускаем

    const q = { id: qi + 1, type, text, points };

    if (type === 'text') {
      q.correct = [...block.querySelectorAll('.text-answers-list .text-answer-input')]
        .map(inp => inp.value.trim())
        .filter(Boolean);
    } else {
      const options = [];
      const correct = [];
      block.querySelectorAll('.options-list .option-row').forEach(row => {
        const optText = row.querySelector('.option-text').value.trim();
        if (!optText) return;
        const label = String.fromCharCode(97 + options.length); // a, b, c...
        options.push({ id: label, text: optText });
        if (row.querySelector('.option-correct').checked) correct.push(label);
      });
      q.options = options;
      q.correct = correct;
    }

    questions.push(q);
  });

  return {
    version: '1.0',
    title: document.querySelector('input[name="title"]').value.trim(),
    description: document.querySelector('textarea[name="description"]').value.trim(),
    time_limit_sec: parseInt(document.querySelector('input[name="time_limit_sec"]').value, 10) || 0,
    pass_score: parseInt(document.querySelector('input[name="pass_score"]').value, 10) || 70,
    created_at: new Date().toISOString(),
    questions,
  };
}

// ---------- Валидация перед сохранением ----------

function validateTest(test) {
  if (!test.title) return 'Укажите название теста.';
  if (!test.questions.length) return 'Добавьте хотя бы один вопрос.';
  for (const q of test.questions) {
    if (!q.text) return `Вопрос ${q.id}: пустой текст.`;
    if (q.type === 'text') {
      if (!q.correct.length) return `Вопрос ${q.id}: нет допустимых ответов.`;
    } else {
      if (!q.options || q.options.length < 2)
        return `Вопрос ${q.id}: нужно минимум 2 варианта.`;
      if (!q.correct.length)
        return `Вопрос ${q.id}: не отмечен правильный ответ.`;
      if (q.type === 'single' && q.correct.length !== 1)
        return `Вопрос ${q.id}: для одиночного выбора — ровно один правильный.`;
    }
  }
  return null;
}

// ---------- Скачивание JSON ----------

function downloadJson(data, filename) {
  const blob = new Blob(
    [JSON.stringify(data, null, 2)],
    { type: 'application/json' }
  );
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

// ---------- Обработчик кнопки «Сохранить в файл» ----------

(async function setupSaveHandler() {
  const btn = document.getElementById('save-quiz');
  const status = document.getElementById('save-status');
  if (!btn) return;

  function setStatus(text, isError) {
    if (!status) return;
    status.hidden = false;
    status.textContent = text;
    status.classList.toggle('is-error', !!isError);
  }

  btn.addEventListener('click', async () => {
    try {
      btn.disabled = true;
      setStatus('Шифрование и сохранение…', false);

      const test = collectTestFromForm();

      const error = validateTest(test);
      if (error) {
        setStatus(error, true);
        btn.disabled = false;
        return;
      }

      // 1. Готовим соль и ключ
      const salt = crypto.getRandomValues(new Uint8Array(CRYPTO_CONFIG.SALT_LENGTH));
      const key = await deriveKey(CRYPTO_CONFIG.PASSPHRASE, salt);

      // 2. Шифруем correct каждого вопроса отдельно
      const encryptedQuestions = [];
      for (const q of test.questions) {
        const { correct, ...rest } = q;
        const correctEnc = await encryptJson(correct, key);
        encryptedQuestions.push({ ...rest, correct_enc: correctEnc });
      }

      // 3. Собираем итоговый документ
      const payload = {
        version: test.version,
        title: test.title,
        description: test.description,
        time_limit_sec: test.time_limit_sec,
        pass_score: test.pass_score,
        created_at: test.created_at,
        crypto: {
          alg: 'AES-GCM-256',
          kdf: 'PBKDF2',
          hash: 'SHA-256',
          iterations: CRYPTO_CONFIG.ITERATIONS,
          salt: bufToBase64(salt),
        },
        questions: encryptedQuestions,
      };

      // 4. Имя файла
      const safeName = test.title
        .replace(/[^\p{L}\p{N}\-_ ]/gu, '')
        .trim()
        .replace(/\s+/g, '_') || 'quiz';

      downloadJson(payload, `${safeName}.json`);
      setStatus('Файл сохранён в папку загрузок.', false);
    } catch (e) {
      console.error(e);
      setStatus('Ошибка сохранения: ' + e.message, true);
    } finally {
      btn.disabled = false;
    }
  });
})();