(function () {
  const questionsContainer = document.getElementById('questions');
  const questionTpl = document.getElementById('question-template');
  const optionTpl = document.getElementById('option-template');
  const textAnswerTpl = document.getElementById('text-answer-template');

  let questionCounter = 0;

  // ---------- Общие утилиты ----------

  function applyIndex(root, qIndex) {
    root.querySelectorAll('[name]').forEach(el => {
      el.name = el.name.replaceAll('__i__', qIndex);
    });
    root.dataset.index = qIndex;
  }

  function renumberQuestions() {
    questionsContainer.querySelectorAll('.question-block').forEach((block, i) => {
      block.querySelector('.q-number').textContent = i + 1;
    });
  }

  function updateCounts(block) {
    block.querySelector('.options-count').value =
      block.querySelector('.options-list').children.length;
    block.querySelector('.text-answers-count').value =
      block.querySelector('.text-answers-list').children.length;
  }

  // ---------- Правильные контролы ----------

  // Создаёт правильный input под текущий тип вопроса.
  // radio для single (общий name -> только один выбор в группе),
  // checkbox для multiple (уникальный name на каждый вариант).
  function createCorrectControl(type, qIndex, optionIndex) {
    const el = document.createElement('input');
    el.className = 'option-correct';
    if (type === 'single') {
      el.type = 'radio';
      el.name = `questions-${qIndex}-correct`;
      el.value = String(optionIndex);
    } else {
      el.type = 'checkbox';
      el.name = `questions-${qIndex}-options-${optionIndex}-correct`;
    }
    return el;
  }

  // Пересобирает контролы и name-атрибуты у всех вариантов вопроса.
  // Вызывается после добавления/удаления варианта и при смене типа.
  function rebuildOptions(block) {
    const qIndex = block.dataset.index;
    const type = block.querySelector('.q-type').value;

    block.querySelectorAll('.options-list .option-row').forEach((row, j) => {
      const oldControl = row.querySelector('.option-correct');
      const wasChecked = oldControl.checked;

      const newControl = createCorrectControl(type, qIndex, j);
      newControl.checked = wasChecked;

      // Подсветка ряда по факту отметки
      newControl.addEventListener('change', () => {
        row.classList.toggle('is-correct', newControl.checked);
        if (type === 'single' && newControl.checked) {
          // для single гасим остальные (на случай, если что-то пошло не так)
          block.querySelectorAll('.option-correct').forEach(c => {
            if (c !== newControl) {
              c.checked = false;
              c.closest('.option-row').classList.remove('is-correct');
            }
          });
        }
      });

      oldControl.replaceWith(newControl);
      row.classList.toggle('is-correct', newControl.checked);

      // name текста варианта должен соответствовать позиции
      row.querySelector('.option-text').name =
        `questions-${qIndex}-options-${j}-text`;
    });

    // name текстовых ответов тоже привязываем к позиции
    block.querySelectorAll('.text-answers-list .text-answer-row').forEach((row, j) => {
      row.querySelector('.text-answer-input').name =
        `questions-${qIndex}-text-answers-${j}`;
    });
  }

  // ---------- Видимость секций по типу ----------

  function syncTypeVisibility(block) {
    const type = block.querySelector('.q-type').value;
    const optionsSection = block.querySelector('.options-section');
    const textSection = block.querySelector('.text-answers-section');
    const hintSingle = block.querySelector('.hint-single');
    const hintMultiple = block.querySelector('.hint-multiple');

    if (type === 'text') {
      optionsSection.hidden = true;
      textSection.hidden = false;
      if (!textSection.querySelector('.text-answers-list').children.length) {
        addTextAnswer(block);
      }
    } else {
      optionsSection.hidden = false;
      textSection.hidden = true;
      hintSingle.hidden = type !== 'single';
      hintMultiple.hidden = type !== 'multiple';
      if (!optionsSection.querySelector('.options-list').children.length) {
        addOption(block);
        addOption(block);
      }
    }
    rebuildOptions(block);
  }

  // ---------- Добавление элементов ----------

  function addOption(block) {
    const clone = optionTpl.content.cloneNode(true);
    block.querySelector('.options-list').appendChild(clone);
    rebuildOptions(block);
    updateCounts(block);
  }

  function addTextAnswer(block) {
    const clone = textAnswerTpl.content.cloneNode(true);
    block.querySelector('.text-answers-list').appendChild(clone);
    rebuildOptions(block);
    updateCounts(block);
  }

  function addQuestion() {
    const qIndex = questionCounter++;
    const clone = questionTpl.content.cloneNode(true);
    const block = clone.querySelector('.question-block');

    questionsContainer.appendChild(clone);
    applyIndex(block, qIndex);

    block.querySelector('.remove-question').addEventListener('click', () => {
      block.remove();
      renumberQuestions();
    });
    block.querySelector('.q-type').addEventListener('change', () =>
      syncTypeVisibility(block));
    block.querySelector('.add-option').addEventListener('click', () =>
      addOption(block));
    block.querySelector('.add-text-answer').addEventListener('click', () =>
      addTextAnswer(block));

    block.querySelector('.options-list').addEventListener('click', e => {
      if (e.target.classList.contains('remove-option')) {
        e.target.closest('.option-row').remove();
        rebuildOptions(block);  // пересобирает value у radio и name у text
        updateCounts(block);
      }
    });
    block.querySelector('.text-answers-list').addEventListener('click', e => {
      if (e.target.classList.contains('remove-text-answer')) {
        e.target.closest('.text-answer-row').remove();
        rebuildOptions(block);
        updateCounts(block);
      }
    });

    syncTypeVisibility(block);
    renumberQuestions();
  }

  document.getElementById('add-question').addEventListener('click', addQuestion);

  // ---------- Предзаполнение при редактировании ----------

  const initial = JSON.parse(
    document.getElementById('initial-data')?.textContent || 'null'
  );

  if (initial && Array.isArray(initial.questions)) {
    initial.questions.forEach(q => {
      addQuestion();
      const block = questionsContainer.lastElementChild;
      block.querySelector('.q-type').value = q.type;
      block.querySelector('textarea[name$="-text"]').value = q.text;
      block.querySelector('input[name$="-points"]').value = q.points || 1;
      syncTypeVisibility(block); // переключает секции и правильные контролы

      if (q.type === 'text') {
        block.querySelector('.text-answers-list').innerHTML = '';
        q.correct.forEach(ans => {
          addTextAnswer(block);
          block.querySelector(
            '.text-answers-list .text-answer-row:last-child .text-answer-input'
          ).value = ans;
        });
      } else {
        block.querySelector('.options-list').innerHTML = '';
        q.options.forEach(opt => {
          addOption(block);
          const row = block.querySelector('.options-list .option-row:last-child');
          row.querySelector('.option-text').value = opt.text;
          if (q.correct.includes(opt.id)) {
            const ctrl = row.querySelector('.option-correct');
            ctrl.checked = true;
            row.classList.add('is-correct');
          }
        });
        rebuildOptions(block); // синхронизирует value с индексами после пересборки
      }
    });
  } else {
    addQuestion();
  }
  
})();
