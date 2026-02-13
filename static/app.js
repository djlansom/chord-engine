// ============================================================
// Chord Engine — Frontend Logic
// ============================================================

const state = {
  playing: false,
  bpm: 120,
  beatsPerBar: 4,
  beat: 0,
  chords: [],         // full progression from API
  position: 0,        // current chord index
  loopChords: [],     // chords for loop view
  metronome: true,
  config: null,
  timerID: null,
  audioCtx: null,
  // Rhythm pattern
  pattern: [1],       // chords-per-bar for each bar in the cycle
  patternBar: 0,      // current bar index within pattern
  chordInBar: 0,      // which chord within current bar
  beatInBar: 0,       // which beat within current bar
  pendingAdvance: false, // chord advance deferred to next beat's downbeat
  rhythmMode: 'simple',  // 'simple' or 'script'
  // Swing
  swing: 50,          // 50 = straight, 67 = triplet swing
  // Count-in
  countingIn: false,
  countInBeat: 0,
  // Practice mode
  practiceMode: false,
  practiceWaiting: false,
  chordsInCycle: 0,
};

// ---- DOM refs ----
const dom = {
  keySelect:      document.getElementById('key-select'),
  scaleSelect:    document.getElementById('scale-select'),
  bpmInput:       document.getElementById('bpm-input'),
  meterInput:     document.getElementById('meter-input'),
  seedInput:      document.getElementById('seed-input'),
  chordTrack:     document.getElementById('chord-track'),
  beatIndicator:  document.getElementById('beat-indicator'),
  loopView:       document.getElementById('loop-view'),
  loopStrip:      document.getElementById('loop-strip'),
  mutationSlider: document.getElementById('mutation-slider'),
  mutationValue:  document.getElementById('mutation-value'),
  voicingSelect:  document.getElementById('voicing-select'),
  lengthSelect:   document.getElementById('length-select'),
  modeBtn:        document.getElementById('mode-btn'),
  playBtn:        document.getElementById('play-btn'),
  newSeedBtn:     document.getElementById('new-seed-btn'),
  saveBtn:        document.getElementById('save-btn'),
  historyBtn:     document.getElementById('history-btn'),
  metroBtn:       document.getElementById('metro-btn'),
  loopToggleBtn:  document.getElementById('loop-toggle-btn'),
  historyPanel:   document.getElementById('history-panel'),
  historyList:    document.getElementById('history-list'),
  historyCloseBtn:document.getElementById('history-close-btn'),
  // Rhythm pattern
  barsPerChordSelect:  document.getElementById('bars-per-chord-select'),
  chordsPerBarSelect:  document.getElementById('chords-per-bar-select'),
  rhythmScriptBtn:     document.getElementById('rhythm-script-btn'),
  rhythmSimpleBtn:     document.getElementById('rhythm-simple-btn'),
  rhythmControls:      document.getElementById('rhythm-controls'),
  rhythmScript:        document.getElementById('rhythm-script'),
  patternInput:        document.getElementById('pattern-input'),
  // Swing
  swingSlider:   document.getElementById('swing-slider'),
  swingValue:    document.getElementById('swing-value'),
  // Practice
  practiceBtn:     document.getElementById('practice-btn'),
  practiceOverlay: document.getElementById('practice-overlay'),
};

// ============================================================
// Init
// ============================================================

async function init() {
  state.config = await fetchJSON('/config');
  populateSelects();
  renderBeatDots();
  setupListeners();
  await fetchProgression();
  renderChords();
}

function populateSelects() {
  const cfg = state.config;

  cfg.keys.forEach(k => {
    dom.keySelect.appendChild(new Option(k, k));
  });

  cfg.scales.forEach(s => {
    const label = s.replace(/_/g, ' ');
    dom.scaleSelect.appendChild(new Option(label, s));
  });

  cfg.voicings.forEach(v => {
    dom.voicingSelect.appendChild(new Option(v, v));
  });
  dom.voicingSelect.value = 'sevenths';

  cfg.lengths.forEach(l => {
    dom.lengthSelect.appendChild(new Option(l, l));
  });
  dom.lengthSelect.value = '8';
}

// ============================================================
// API calls
// ============================================================

async function fetchJSON(url) {
  const res = await fetch(url);
  return res.json();
}

function getParams() {
  const seed = dom.seedInput.value.trim();
  const params = new URLSearchParams({
    key: dom.keySelect.value,
    scale: dom.scaleSelect.value,
    length: dom.lengthSelect.value,
    mutation: (dom.mutationSlider.value / 100).toFixed(2),
    voicing: dom.voicingSelect.value,
    mode: dom.modeBtn.dataset.mode,
    count: Math.max(parseInt(dom.lengthSelect.value), 16),
  });
  if (seed) params.set('seed', seed);
  return params;
}

async function fetchProgression() {
  const data = await fetchJSON('/progression?' + getParams());
  state.chords = data.chords;
  state.loopChords = data.chords.slice(0, parseInt(dom.lengthSelect.value));
  state.position = 0;
  state.beat = 0;
  if (data.register_state !== undefined) {
    dom.seedInput.placeholder = data.register_state;
  }
}

async function stepOne() {
  const data = await fetchJSON('/step');
  return data.chord;
}

// ============================================================
// Rendering
// ============================================================

function renderChords() {
  const track = dom.chordTrack;
  track.innerHTML = '';

  // Show a window of chords around the current position
  const windowSize = 7;
  const half = Math.floor(windowSize / 2);

  for (let offset = -half; offset <= half; offset++) {
    const idx = state.position + offset;
    const chord = state.chords[idx];
    const card = document.createElement('div');
    card.className = 'chord-card';

    if (chord) {
      card.classList.add('quality-' + chord.category);
      if (offset === 0) card.classList.add('current');
      else if (Math.abs(offset) === 1) card.classList.add('adjacent');
      if (chord.mutated) card.classList.add('mutated');

      card.innerHTML = `
        <div class="chord-symbol">${chord.symbol}</div>
        <div class="chord-roman">${chord.roman}</div>
      `;
    } else {
      card.style.visibility = 'hidden';
    }

    track.appendChild(card);
  }

  renderLoopView();
  updateBeatDots();
}

function renderLoopView() {
  const strip = dom.loopStrip;
  strip.innerHTML = '';

  state.loopChords.forEach((chord, i) => {
    const cell = document.createElement('div');
    cell.className = 'loop-cell quality-' + chord.category;
    if (i === state.position % state.loopChords.length) {
      cell.classList.add('active');
    }
    cell.textContent = chord.symbol;
    strip.appendChild(cell);
  });
}

function renderBeatDots() {
  dom.beatIndicator.innerHTML = '';
  for (let i = 0; i < state.beatsPerBar; i++) {
    const dot = document.createElement('span');
    dot.className = 'beat-dot';
    dom.beatIndicator.appendChild(dot);
  }
}

function updateBeatDots() {
  const dots = dom.beatIndicator.querySelectorAll('.beat-dot');
  dots.forEach((dot, i) => {
    dot.classList.toggle('active', i === state.beat);
  });
}

// ============================================================
// Rhythm pattern helpers
// ============================================================

function getPattern() {
  if (state.rhythmMode === 'script') {
    const text = dom.patternInput.value.trim();
    if (!text) return [1];
    // Parse pattern: space-separated ints
    const parts = text.split(/\s+/);
    const result = [];
    for (const p of parts) {
      const n = parseInt(p);
      if (isNaN(n) || n < 0) return [1];  // fallback on invalid
      result.push(n);
    }
    if (!result.length || result[0] === 0) return [1];
    return result;
  }
  // Simple mode: derive pattern from dropdowns
  const bars = parseInt(dom.barsPerChordSelect.value);
  const chords = parseInt(dom.chordsPerBarSelect.value);
  if (bars > 1) return [1, ...Array(bars - 1).fill(0)];
  if (chords > 1) return [chords];
  return [1];
}

function resetPatternState() {
  state.pattern = getPattern();
  state.patternBar = 0;
  state.chordInBar = 0;
  state.beatInBar = 0;
  state.beat = 0;
  state.pendingAdvance = false;
  state.chordsInCycle = 0;
}

// ============================================================
// Playback engine
// ============================================================

function startPlayback() {
  if (state.practiceWaiting) {
    // Resume from practice pause
    state.practiceWaiting = false;
    dom.practiceOverlay.classList.add('hidden');
    state.chordsInCycle = 0;
    resetPatternState();
    scheduleBeat();
    return;
  }

  state.playing = true;
  dom.playBtn.innerHTML = '&#9632; Stop';
  dom.playBtn.classList.add('playing');

  resetPatternState();

  // Count-in: play one bar of clicks before starting chords
  state.countingIn = true;
  state.countInBeat = 0;
  dom.chordTrack.classList.add('counting-in');

  scheduleBeat();
}

function stopPlayback() {
  state.playing = false;
  state.practiceWaiting = false;
  state.countingIn = false;
  dom.playBtn.innerHTML = '&#9654; Play';
  dom.playBtn.classList.remove('playing');
  dom.chordTrack.classList.remove('counting-in');
  dom.practiceOverlay.classList.add('hidden');
  if (state.timerID) {
    clearTimeout(state.timerID);
    state.timerID = null;
  }
}

function calcBeatDelay() {
  const straightBeat = 60000 / state.bpm;
  if (state.swing <= 50) return straightBeat;

  // Swing: alternate long/short beats in pairs
  const swingRatio = state.swing / 100;
  const pairDuration = straightBeat * 2;
  if (state.beatInBar % 2 === 0) {
    return pairDuration * swingRatio;
  } else {
    return pairDuration * (1 - swingRatio);
  }
}

function scheduleBeat() {
  if (!state.playing) return;

  const delay = calcBeatDelay();

  // --- Count-in phase ---
  if (state.countingIn) {
    if (state.metronome) {
      playClick(state.countInBeat === 0);
    }
    // Show count-in on beat dots
    state.beat = state.countInBeat;
    updateBeatDots();

    state.countInBeat++;
    if (state.countInBeat >= state.beatsPerBar) {
      // Count-in complete, start real playback
      state.countingIn = false;
      state.beat = 0;
      state.beatInBar = 0;
      dom.chordTrack.classList.remove('counting-in');
    }
    state.timerID = setTimeout(scheduleBeat, delay);
    return;
  }

  // --- Normal playback ---

  // Fire any pending chord advance BEFORE this beat plays.
  // This makes the chord change land ON the downbeat, not after the previous bar.
  if (state.pendingAdvance) {
    advanceChord();
    state.pendingAdvance = false;
  }

  // Play metronome click (accent on beat 0 of bar)
  if (state.metronome) {
    playClick(state.beatInBar === 0);
  }

  // Update beat indicator
  state.beat = state.beatInBar;
  updateBeatDots();

  // Determine chord boundaries within the current bar
  const chordsThisBar = state.pattern[state.patternBar];

  state.beatInBar++;

  // Mid-bar chord boundaries (for multiple chords per bar)
  if (chordsThisBar > 1) {
    const beatsPerChord = state.beatsPerBar / chordsThisBar;
    const prevChordIdx = Math.floor((state.beatInBar - 1) / beatsPerChord);
    const nextChordIdx = Math.floor(state.beatInBar / beatsPerChord);
    if (state.beatInBar < state.beatsPerBar && nextChordIdx > prevChordIdx) {
      state.chordInBar++;
      // Defer to next beat so the change lands on the beat, not after
      state.pendingAdvance = true;
    }
  }

  // End of bar?
  if (state.beatInBar >= state.beatsPerBar) {
    // Schedule chord advance for beat 1 of next bar (not now)
    if (chordsThisBar > 0) {
      state.pendingAdvance = true;
    }

    // Move to next bar in the pattern
    state.patternBar = (state.patternBar + 1) % state.pattern.length;
    state.beatInBar = 0;
    state.chordInBar = 0;
  }

  // Check for practice mode pause
  if (state.practiceWaiting) return;

  state.timerID = setTimeout(scheduleBeat, delay);
}

async function advanceChord() {
  state.position++;
  state.chordsInCycle++;

  // Pre-fetch chords so there are always at least 4 ahead for the display
  while (state.chords.length - state.position < 4) {
    const chord = await stepOne();
    state.chords.push(chord);
    // Update loop view
    const loopLen = parseInt(dom.lengthSelect.value);
    const loopIdx = (state.chords.length - 1) % loopLen;
    if (loopIdx < state.loopChords.length) {
      state.loopChords[loopIdx] = chord;
    }
  }

  renderChords();

  // Practice mode: pause after one full loop cycle
  if (state.practiceMode) {
    const loopLen = parseInt(dom.lengthSelect.value);
    if (state.chordsInCycle >= loopLen) {
      state.practiceWaiting = true;
      dom.practiceOverlay.classList.remove('hidden');
      // Don't stop playback — scheduleBeat checks practiceWaiting
    }
  }
}

// ============================================================
// Web Audio — Metronome clicks
// ============================================================

function ensureAudioCtx() {
  if (!state.audioCtx) {
    state.audioCtx = new (window.AudioContext || window.webkitAudioContext)();
  }
  return state.audioCtx;
}

function playClick(downbeat) {
  const ctx = ensureAudioCtx();
  const osc = ctx.createOscillator();
  const gain = ctx.createGain();

  osc.connect(gain);
  gain.connect(ctx.destination);

  osc.frequency.value = downbeat ? 1000 : 700;
  osc.type = 'triangle';

  const now = ctx.currentTime;
  gain.gain.setValueAtTime(downbeat ? 0.3 : 0.15, now);
  gain.gain.exponentialRampToValueAtTime(0.001, now + 0.06);

  osc.start(now);
  osc.stop(now + 0.06);
}

// ============================================================
// Event listeners
// ============================================================

function setupListeners() {
  // Play/Stop
  dom.playBtn.addEventListener('click', () => {
    if (state.playing) stopPlayback();
    else startPlayback();
  });

  // New Seed
  dom.newSeedBtn.addEventListener('click', async () => {
    dom.seedInput.value = '';
    await fetchProgression();
    renderChords();
  });

  // BPM
  dom.bpmInput.addEventListener('change', () => {
    state.bpm = Math.max(40, Math.min(200, parseInt(dom.bpmInput.value) || 120));
    dom.bpmInput.value = state.bpm;
  });

  // Meter
  dom.meterInput.addEventListener('change', () => {
    state.beatsPerBar = Math.max(2, Math.min(12, parseInt(dom.meterInput.value) || 4));
    dom.meterInput.value = state.beatsPerBar;
    state.beat = 0;
    renderBeatDots();
    updateBeatDots();
  });

  // Mutation slider
  dom.mutationSlider.addEventListener('input', () => {
    const val = (dom.mutationSlider.value / 100).toFixed(2);
    dom.mutationValue.textContent = val;
  });

  // Swing slider
  dom.swingSlider.addEventListener('input', () => {
    state.swing = parseInt(dom.swingSlider.value);
    dom.swingValue.textContent = state.swing + '%';
  });

  // Rhythm: simple mode dropdowns
  dom.barsPerChordSelect.addEventListener('change', () => {
    if (parseInt(dom.barsPerChordSelect.value) > 1) {
      dom.chordsPerBarSelect.value = '1';
    }
    state.pattern = getPattern();
  });
  dom.chordsPerBarSelect.addEventListener('change', () => {
    if (parseInt(dom.chordsPerBarSelect.value) > 1) {
      dom.barsPerChordSelect.value = '1';
    }
    state.pattern = getPattern();
  });

  // Rhythm: toggle simple <-> script
  dom.rhythmScriptBtn.addEventListener('click', () => {
    state.rhythmMode = 'script';
    dom.rhythmControls.classList.add('hidden');
    dom.rhythmScript.classList.remove('hidden');
    state.pattern = getPattern();
  });
  dom.rhythmSimpleBtn.addEventListener('click', () => {
    state.rhythmMode = 'simple';
    dom.rhythmScript.classList.add('hidden');
    dom.rhythmControls.classList.remove('hidden');
    state.pattern = getPattern();
  });

  // Rhythm: pattern input change
  dom.patternInput.addEventListener('change', () => {
    state.pattern = getPattern();
  });

  // Mode toggle
  dom.modeBtn.addEventListener('click', () => {
    const current = dom.modeBtn.dataset.mode;
    const next = current === 'raw' ? 'smooth' : 'raw';
    dom.modeBtn.dataset.mode = next;
    dom.modeBtn.textContent = next.charAt(0).toUpperCase() + next.slice(1);
  });

  // Metronome toggle
  dom.metroBtn.addEventListener('click', () => {
    state.metronome = !state.metronome;
    dom.metroBtn.classList.toggle('active', state.metronome);
    dom.metroBtn.textContent = state.metronome ? 'Audio' : 'Muted';
  });

  // Practice mode toggle
  dom.practiceBtn.addEventListener('click', () => {
    state.practiceMode = !state.practiceMode;
    dom.practiceBtn.classList.toggle('active', state.practiceMode);
    if (!state.practiceMode) {
      // If turning off mid-pause, resume
      if (state.practiceWaiting) {
        state.practiceWaiting = false;
        dom.practiceOverlay.classList.add('hidden');
        state.chordsInCycle = 0;
        scheduleBeat();
      }
    }
  });

  // Practice overlay click to continue
  dom.practiceOverlay.addEventListener('click', () => {
    if (state.practiceWaiting) startPlayback();
  });

  // Loop view toggle
  dom.loopToggleBtn.addEventListener('click', () => {
    dom.loopView.classList.toggle('hidden');
    dom.loopToggleBtn.classList.toggle('active');
  });

  // Settings changes -> re-fetch
  const refetchOnChange = [dom.keySelect, dom.scaleSelect, dom.voicingSelect, dom.lengthSelect];
  refetchOnChange.forEach(el => {
    el.addEventListener('change', async () => {
      await fetchProgression();
      renderChords();
    });
  });

  // Save loop
  dom.saveBtn.addEventListener('click', saveLoop);

  // History
  dom.historyBtn.addEventListener('click', () => {
    dom.historyPanel.classList.toggle('hidden');
    renderHistory();
  });
  dom.historyCloseBtn.addEventListener('click', () => {
    dom.historyPanel.classList.add('hidden');
  });

  // Keyboard shortcuts
  document.addEventListener('keydown', handleKeyboard);
}

function handleKeyboard(e) {
  // Ignore if typing in an input
  if (e.target.tagName === 'INPUT' || e.target.tagName === 'SELECT') return;

  switch (e.code) {
    case 'Space':
      e.preventDefault();
      if (state.practiceWaiting) {
        startPlayback();
      } else if (state.playing) {
        stopPlayback();
      } else {
        startPlayback();
      }
      break;
    case 'KeyS':
      saveLoop();
      break;
    case 'ArrowUp':
      e.preventDefault();
      state.bpm = Math.min(200, state.bpm + 5);
      dom.bpmInput.value = state.bpm;
      break;
    case 'ArrowDown':
      e.preventDefault();
      state.bpm = Math.max(40, state.bpm - 5);
      dom.bpmInput.value = state.bpm;
      break;
    case 'ArrowRight':
      e.preventDefault();
      dom.mutationSlider.value = Math.min(100, parseInt(dom.mutationSlider.value) + 5);
      dom.mutationValue.textContent = (dom.mutationSlider.value / 100).toFixed(2);
      break;
    case 'ArrowLeft':
      e.preventDefault();
      dom.mutationSlider.value = Math.max(0, parseInt(dom.mutationSlider.value) - 5);
      dom.mutationValue.textContent = (dom.mutationSlider.value / 100).toFixed(2);
      break;
    case 'KeyM':
      state.metronome = !state.metronome;
      dom.metroBtn.classList.toggle('active', state.metronome);
      dom.metroBtn.textContent = state.metronome ? 'Audio' : 'Muted';
      break;
    case 'KeyL':
      dom.loopView.classList.toggle('hidden');
      dom.loopToggleBtn.classList.toggle('active');
      break;
    case 'KeyN':
      dom.seedInput.value = '';
      fetchProgression().then(() => renderChords());
      break;
    case 'KeyP':
      state.practiceMode = !state.practiceMode;
      dom.practiceBtn.classList.toggle('active', state.practiceMode);
      break;
  }
}

// ============================================================
// Save / Load (localStorage)
// ============================================================

function saveLoop() {
  const saved = JSON.parse(localStorage.getItem('chord-engine-saves') || '[]');
  const entry = {
    id: Date.now(),
    date: new Date().toLocaleString(),
    key: dom.keySelect.value,
    scale: dom.scaleSelect.value,
    voicing: dom.voicingSelect.value,
    mode: dom.modeBtn.dataset.mode,
    length: dom.lengthSelect.value,
    mutation: (dom.mutationSlider.value / 100).toFixed(2),
    seed: dom.seedInput.value || dom.seedInput.placeholder,
    chords: state.loopChords.map(c => c.symbol).join(' | '),
  };
  saved.unshift(entry);
  // Keep last 50
  if (saved.length > 50) saved.length = 50;
  localStorage.setItem('chord-engine-saves', JSON.stringify(saved));
  renderHistory();

  // Visual feedback
  dom.saveBtn.textContent = 'Saved!';
  setTimeout(() => { dom.saveBtn.textContent = 'Save Loop'; }, 1200);
}

function renderHistory() {
  const saved = JSON.parse(localStorage.getItem('chord-engine-saves') || '[]');
  dom.historyList.innerHTML = '';

  saved.forEach(entry => {
    const item = document.createElement('div');
    item.className = 'history-item';
    item.innerHTML = `
      <div class="chords-preview">${entry.chords}</div>
      <div class="meta">${entry.key} ${entry.scale} | ${entry.voicing} | ${entry.date}</div>
    `;
    item.addEventListener('click', () => loadSavedLoop(entry));
    dom.historyList.appendChild(item);
  });
}

async function loadSavedLoop(entry) {
  dom.keySelect.value = entry.key;
  dom.scaleSelect.value = entry.scale;
  dom.voicingSelect.value = entry.voicing;
  dom.lengthSelect.value = entry.length;
  dom.modeBtn.dataset.mode = entry.mode;
  dom.modeBtn.textContent = entry.mode.charAt(0).toUpperCase() + entry.mode.slice(1);
  dom.mutationSlider.value = 0;  // Load as locked to replay
  dom.mutationValue.textContent = '0.00';
  dom.seedInput.value = entry.seed;
  dom.historyPanel.classList.add('hidden');

  await fetchProgression();
  renderChords();
}

// ============================================================
// Boot
// ============================================================

init();
