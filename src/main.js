/**
 * SmoothScroll Windows 11 — Frontend Logic & IPC Bridge
 */

// Preset Configurations
const PRESETS = {
  buttery: {
    stepSize: 120,
    animationDurationMs: 420,
    accelerationFactor: 1.75,
    friction: 0.93,
    easingCurve: "easeOutCubic",
  },
  snappy: {
    stepSize: 100,
    animationDurationMs: 240,
    accelerationFactor: 1.4,
    friction: 0.88,
    easingCurve: "easeOutCubic",
  },
  glide: {
    stepSize: 150,
    animationDurationMs: 650,
    accelerationFactor: 2.1,
    friction: 0.96,
    easingCurve: "exponential",
  },
  subtle: {
    stepSize: 80,
    animationDurationMs: 180,
    accelerationFactor: 1.15,
    friction: 0.84,
    easingCurve: "linear",
  },
};

// Application State
let currentSettings = {
  enabled: true,
  stepSize: 120.0,
  animationDurationMs: 380.0,
  accelerationFactor: 1.75,
  friction: 0.92,
  easingCurve: "easeOutCubic",
  invertVertical: false,
  invertHorizontal: false,
  trackpadMode: true,
  trackpadDeadzone: 2.5,
  trackpadMomentum: 1.45,
  trackpadInvert: false,
  altAccelerate: true,
  ctrlPassthroughZoom: true,
  startWithWindows: false,
  startMinimized: false,
  lowLatencyTimer: true,
  blacklistedApps: ["cs2.exe", "valorant.exe", "Overwatch.exe", "ApexLegends.exe"],
};

let isTauriEnv = false;
let mockIntercepted = 0;
let mockDispatched = 0;

// Safe Invoke Wrapper (Supports both Tauri IPC and Local Python API)
async function tauriInvoke(cmd, args = {}) {
  try {
    if (window.__TAURI__ && window.__TAURI__.core) {
      isTauriEnv = true;
      return await window.__TAURI__.core.invoke(cmd, args);
    } else if (window.__TAURI__ && window.__TAURI__.tauri) {
      isTauriEnv = true;
      return await window.__TAURI__.tauri.invoke(cmd, args);
    }
  } catch (err) {
    console.warn(`[SmoothScroll IPC] Error calling ${cmd}:`, err);
  }

  // Local REST API fallback for Python launcher
  try {
    if (cmd === "get_settings") {
      const res = await fetch("/api/settings");
      if (res.ok) return await res.json();
    } else if (cmd === "update_settings") {
      const res = await fetch("/api/settings", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(args.settings || {}),
      });
      return res.ok;
    } else if (cmd === "toggle_enabled") {
      const res = await fetch("/api/toggle", { method: "POST" });
      if (res.ok) {
        const data = await res.json();
        return data.enabled;
      }
    } else if (cmd === "get_metrics") {
      const res = await fetch("/api/metrics");
      if (res.ok) return await res.json();
    } else if (cmd === "get_foreground_app") {
      const res = await fetch("/api/detect_app");
      if (res.ok) {
        const data = await res.json();
        return data.process;
      }
    } else if (cmd === "reset_defaults") {
      const res = await fetch("/api/defaults", { method: "POST" });
      if (res.ok) return await res.json();
    }
  } catch (_) {}

  isTauriEnv = false;
  return null;
}

// Initialize Application
document.addEventListener("DOMContentLoaded", async () => {
  setupTabs();
  setupPresets();
  setupEventListeners();
  setupPlaygroundPhysics();

  // Load initial settings
  const loaded = await tauriInvoke("get_settings");
  if (loaded) {
    currentSettings = { ...currentSettings, ...loaded };
  }
  syncUiFromSettings();
  startMetricsPolling();
});

// Setup Navigation Tabs
function setupTabs() {
  const tabButtons = document.querySelectorAll(".tab-btn");
  const tabPanels = document.querySelectorAll(".tab-panel");

  tabButtons.forEach((btn) => {
    btn.addEventListener("click", () => {
      const targetId = btn.getAttribute("data-tab");
      if (!targetId) return;

      tabButtons.forEach((b) => b.classList.remove("active"));
      tabPanels.forEach((p) => p.classList.remove("active"));

      btn.classList.add("active");
      const targetPanel = document.getElementById(targetId);
      if (targetPanel) {
        targetPanel.classList.add("active");
      }
    });
  });
}

// Setup Presets
function setupPresets() {
  const chips = document.querySelectorAll(".preset-chip");
  chips.forEach((chip) => {
    chip.addEventListener("click", () => {
      chips.forEach((c) => c.classList.remove("active"));
      chip.classList.add("active");

      const presetKey = chip.getAttribute("data-preset");
      if (presetKey && PRESETS[presetKey]) {
        applyPreset(PRESETS[presetKey]);
      }
    });
  });
}

function applyPreset(preset) {
  currentSettings.stepSize = preset.stepSize;
  currentSettings.animationDurationMs = preset.animationDurationMs;
  currentSettings.accelerationFactor = preset.accelerationFactor;
  currentSettings.friction = preset.friction;
  currentSettings.easingCurve = preset.easingCurve;
  syncUiFromSettings();
  saveCurrentSettings(false);
}

// Synchronize Settings to UI Elements
function syncUiFromSettings() {
  // Status pill
  updateStatusUi(currentSettings.enabled);

  // Sliders & Values
  setSlider("quick-step", "quick-step-val", currentSettings.stepSize, " px");
  setSlider("input-step-size", "val-step-size", currentSettings.stepSize, " px");

  setSlider("quick-duration", "quick-duration-val", currentSettings.animationDurationMs, " ms");
  setSlider("input-duration", "val-duration", currentSettings.animationDurationMs, " ms");

  setSlider("quick-friction", "quick-friction-val", currentSettings.friction, "");
  setSlider("input-friction", "val-friction", currentSettings.friction, "");

  setSlider("input-accel", "val-accel", currentSettings.accelerationFactor, "x");
  setSlider("input-trackpad-deadzone", "val-trackpad-deadzone", currentSettings.trackpadDeadzone, " px");
  setSlider("input-trackpad-momentum", "val-trackpad-momentum", currentSettings.trackpadMomentum, "x");

  // Selects
  const easingSelect = document.getElementById("select-easing");
  if (easingSelect) {
    easingSelect.value = currentSettings.easingCurve;
  }

  // Switches
  setCheckbox("check-invert-v", currentSettings.invertVertical);
  setCheckbox("check-invert-h", currentSettings.invertHorizontal);
  setCheckbox("check-trackpad-mode", currentSettings.trackpadMode);
  setCheckbox("check-trackpad-invert", currentSettings.trackpadInvert);
  setCheckbox("check-autostart", currentSettings.startWithWindows);
  setCheckbox("check-minimized", currentSettings.startMinimized);
  setCheckbox("check-low-latency", currentSettings.lowLatencyTimer);
  setCheckbox("check-ctrl-zoom", currentSettings.ctrlPassthroughZoom);
  setCheckbox("check-alt-accel", currentSettings.altAccelerate);

  // Blacklist
  renderBlacklist();
}

function setSlider(sliderId, labelId, value, unit) {
  const slider = document.getElementById(sliderId);
  const label = document.getElementById(labelId);
  if (slider) slider.value = value;
  if (label) label.textContent = `${value}${unit}`;
}

function setCheckbox(id, checked) {
  const box = document.getElementById(id);
  if (box) box.checked = !!checked;
}

// Setup Event Listeners
function setupEventListeners() {
  // Power Toggle Button
  const powerBtn = document.getElementById("power-toggle-btn");
  if (powerBtn) {
    powerBtn.addEventListener("click", async () => {
      currentSettings.enabled = !currentSettings.enabled;
      updateStatusUi(currentSettings.enabled);
      await tauriInvoke("toggle_enabled");
    });
  }

  // Quick Sliders Sync
  bindSliderPair("quick-step", "input-step-size", "quick-step-val", "val-step-size", " px", (v) => {
    currentSettings.stepSize = parseFloat(v);
  });

  bindSliderPair("quick-duration", "input-duration", "quick-duration-val", "val-duration", " ms", (v) => {
    currentSettings.animationDurationMs = parseFloat(v);
  });

  bindSliderPair("quick-friction", "input-friction", "quick-friction-val", "val-friction", "", (v) => {
    currentSettings.friction = parseFloat(v);
  });

  // Dedicated Sliders
  bindSingleSlider("input-accel", "val-accel", "x", (v) => {
    currentSettings.accelerationFactor = parseFloat(v);
  });

  bindSingleSlider("input-trackpad-deadzone", "val-trackpad-deadzone", " px", (v) => {
    currentSettings.trackpadDeadzone = parseFloat(v);
  });

  bindSingleSlider("input-trackpad-momentum", "val-trackpad-momentum", "x", (v) => {
    currentSettings.trackpadMomentum = parseFloat(v);
  });

  // Select
  const easingSelect = document.getElementById("select-easing");
  if (easingSelect) {
    easingSelect.addEventListener("change", (e) => {
      currentSettings.easingCurve = e.target.value;
      saveCurrentSettings(false);
    });
  }

  // Switches
  bindSwitch("check-invert-v", (val) => (currentSettings.invertVertical = val));
  bindSwitch("check-invert-h", (val) => (currentSettings.invertHorizontal = val));
  bindSwitch("check-trackpad-mode", (val) => (currentSettings.trackpadMode = val));
  bindSwitch("check-trackpad-invert", (val) => (currentSettings.trackpadInvert = val));
  bindSwitch("check-autostart", (val) => (currentSettings.startWithWindows = val));
  bindSwitch("check-minimized", (val) => (currentSettings.startMinimized = val));
  bindSwitch("check-low-latency", (val) => (currentSettings.lowLatencyTimer = val));
  bindSwitch("check-ctrl-zoom", (val) => (currentSettings.ctrlPassthroughZoom = val));
  bindSwitch("check-alt-accel", (val) => (currentSettings.altAccelerate = val));

  // Save Button
  const saveBtn = document.getElementById("btn-save-settings");
  if (saveBtn) {
    saveBtn.addEventListener("click", () => {
      saveCurrentSettings(true);
    });
  }

  // Reset Button
  const resetBtn = document.getElementById("btn-reset-defaults");
  if (resetBtn) {
    resetBtn.addEventListener("click", async () => {
      const def = await tauriInvoke("reset_defaults");
      if (def) {
        currentSettings = def;
      } else {
        // Fallback default
        currentSettings = {
          ...currentSettings,
          stepSize: 120.0,
          animationDurationMs: 380.0,
          accelerationFactor: 1.75,
          friction: 0.92,
          easingCurve: "easeOutCubic",
        };
      }
      syncUiFromSettings();
    });
  }

  // Blacklist Adder
  const addAppBtn = document.getElementById("btn-add-app");
  const newAppInput = document.getElementById("input-new-app");
  if (addAppBtn && newAppInput) {
    addAppBtn.addEventListener("click", () => {
      const appName = newAppInput.value.trim();
      if (appName && !currentSettings.blacklistedApps.includes(appName)) {
        currentSettings.blacklistedApps.push(appName);
        newAppInput.value = "";
        renderBlacklist();
        saveCurrentSettings(false);
      }
    });
  }

  // Detect Active Foreground App
  const detectAppBtn = document.getElementById("btn-detect-app");
  if (detectAppBtn) {
    detectAppBtn.addEventListener("click", async () => {
      const activeApp = await tauriInvoke("get_foreground_app");
      if (activeApp && newAppInput) {
        newAppInput.value = activeApp;
      } else if (newAppInput) {
        newAppInput.value = "Code.exe";
      }
    });
  }
}

function bindSliderPair(id1, id2, label1, label2, unit, onUpdate) {
  const el1 = document.getElementById(id1);
  const el2 = document.getElementById(id2);
  const lbl1 = document.getElementById(label1);
  const lbl2 = document.getElementById(label2);

  const handler = (e) => {
    const val = e.target.value;
    if (el1) el1.value = val;
    if (el2) el2.value = val;
    if (lbl1) lbl1.textContent = `${val}${unit}`;
    if (lbl2) lbl2.textContent = `${val}${unit}`;
    onUpdate(val);
    saveCurrentSettings(false);
  };

  if (el1) el1.addEventListener("input", handler);
  if (el2) el2.addEventListener("input", handler);
}

function bindSingleSlider(sliderId, labelId, unit, onUpdate) {
  const slider = document.getElementById(sliderId);
  const label = document.getElementById(labelId);
  if (!slider) return;

  slider.addEventListener("input", (e) => {
    const val = e.target.value;
    if (label) label.textContent = `${val}${unit}`;
    onUpdate(val);
    saveCurrentSettings(false);
  });
}

function bindSwitch(id, onUpdate) {
  const el = document.getElementById(id);
  if (!el) return;
  el.addEventListener("change", (e) => {
    onUpdate(e.target.checked);
    saveCurrentSettings(false);
  });
}

// Update Active/Paused UI
function updateStatusUi(isEnabled) {
  const statusPill = document.getElementById("engine-status");
  const statusText = document.getElementById("status-text");
  const powerBtn = document.getElementById("power-toggle-btn");

  if (!statusPill || !statusText || !powerBtn) return;

  if (isEnabled) {
    statusPill.className = "status-pill active";
    statusText.textContent = "Engine Active";
    powerBtn.querySelector(".btn-text").textContent = "Pause";
  } else {
    statusPill.className = "status-pill paused";
    statusText.textContent = "Paused";
    powerBtn.querySelector(".btn-text").textContent = "Resume";
  }
}

// Save Settings with Debounce
let saveTimeout = null;
function saveCurrentSettings(showFeedback = false) {
  clearTimeout(saveTimeout);
  saveTimeout = setTimeout(async () => {
    await tauriInvoke("update_settings", { settings: currentSettings });
    if (showFeedback) {
      const saveBtn = document.getElementById("btn-save-settings");
      if (saveBtn) {
        const originalText = saveBtn.textContent;
        saveBtn.textContent = "Saved ✓";
        setTimeout(() => {
          saveBtn.textContent = originalText;
        }, 1200);
      }
    }
  }, 100);
}

// Render Application Blacklist Safely (No innerHTML)
function renderBlacklist() {
  const container = document.getElementById("blacklist-container");
  if (!container) return;

  container.replaceChildren();

  currentSettings.blacklistedApps.forEach((app, index) => {
    const item = document.createElement("div");
    item.className = "blacklist-item";

    const nameSpan = document.createElement("span");
    nameSpan.className = "blacklist-name";
    nameSpan.textContent = app;

    const removeBtn = document.createElement("button");
    removeBtn.className = "btn-remove-app";
    removeBtn.setAttribute("aria-label", `Remove ${app}`);
    removeBtn.textContent = "✕";
    removeBtn.addEventListener("click", () => {
      currentSettings.blacklistedApps.splice(index, 1);
      renderBlacklist();
      saveCurrentSettings(false);
    });

    item.appendChild(nameSpan);
    item.appendChild(removeBtn);
    container.appendChild(item);
  });
}

// Interactive Scroll Playground Physics Simulation
function setupPlaygroundPhysics() {
  const scrollContainer = document.getElementById("scroll-test-container");
  if (!scrollContainer) return;

  let velocity = 0;
  let isGliding = false;
  let animId = null;

  scrollContainer.addEventListener(
    "wheel",
    (e) => {
      if (!currentSettings.enabled) return;

      e.preventDefault();
      mockIntercepted += 1;

      const rawDelta = e.deltaY;
      const isTrackpad = Math.abs(rawDelta) < 100;
      let impulse = 0;

      if (isTrackpad && currentSettings.trackpadMode) {
        if (Math.abs(rawDelta) < currentSettings.trackpadDeadzone) return;
        impulse = rawDelta * currentSettings.trackpadMomentum * 1.8;
      } else {
        const sign = rawDelta > 0 ? 1 : -1;
        impulse = sign * currentSettings.stepSize;
      }

      if (currentSettings.invertVertical) {
        impulse = -impulse;
      }

      velocity += impulse * (1000 / currentSettings.animationDurationMs);

      if (!isGliding) {
        isGliding = true;
        glideLoop();
      }
    },
    { passive: false }
  );

  function glideLoop() {
    if (!isGliding) return;

    scrollContainer.scrollTop += velocity * 0.016;
    velocity *= currentSettings.friction;
    mockDispatched += 1;

    if (Math.abs(velocity) < 0.2) {
      velocity = 0;
      isGliding = false;
      cancelAnimationFrame(animId);
      return;
    }

    animId = requestAnimationFrame(glideLoop);
  }
}

// Telemetry Polling
function startMetricsPolling() {
  const interceptedEl = document.getElementById("metric-intercepted");
  const dispatchedEl = document.getElementById("metric-dispatched");

  setInterval(async () => {
    let metrics = await tauriInvoke("get_metrics");
    if (metrics) {
      if (interceptedEl) interceptedEl.textContent = metrics[0].toLocaleString();
      if (dispatchedEl) dispatchedEl.textContent = metrics[1].toLocaleString();
    } else {
      // In web preview mode, show mock numbers from playground
      if (interceptedEl) interceptedEl.textContent = mockIntercepted.toLocaleString();
      if (dispatchedEl) dispatchedEl.textContent = mockDispatched.toLocaleString();
    }
  }, 500);
}
