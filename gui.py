"""
SmoothScroll Windows 11 — Native GUI (Tkinter Fluent Dark Theme)
Completely self-contained desktop interface with no browser or web server dependencies.
"""

import sys
import os
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional

from core.hook import hook_manager
from core.config import AppSettings

# Design Tokens (Windows 11 Fluent Dark)
BG_BASE = "#0b0f19"
BG_CARD = "#161f30"
BG_CARD_HOVER = "#1e293b"
BG_INPUT = "#0f172a"
BORDER = "#334155"
TEXT_PRIMARY = "#f8fafc"
TEXT_SECONDARY = "#94a3b8"
TEXT_MUTED = "#64748b"
ACCENT = "#38bdf8"
ACCENT_ACTIVE = "#0284c7"
COL_GREEN = "#10b981"
COL_AMBER = "#f59e0b"
COL_RED = "#f87171"

class SmoothScrollGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Glidify — Windows 11")
        self.root.geometry("860x680")
        self.root.minsize(780, 580)
        self.root.configure(bg=BG_BASE)

        # Set window icon if available
        icon_path = os.path.join(os.path.dirname(__file__), "src-tauri", "icons", "icon.ico")
        if os.path.exists(icon_path):
            try:
                self.root.iconbitmap(icon_path)
            except Exception:
                pass

        self.settings = hook_manager.settings

        self._init_styles()
        self._build_header()
        self._build_tabs()
        self._build_footer()

        # Handle window close (minimize to tray)
        self.root.protocol("WM_DELETE_WINDOW", self.hide_to_tray)

        # Start periodic telemetry & metric updates
        self._update_metrics()

    def _init_styles(self):
        style = ttk.Style(self.root)
        style.theme_use("clam")

        # Configure Notebook (Tabs)
        style.configure(
            "TNotebook",
            background=BG_BASE,
            borderwidth=0,
            tabmargins=[16, 8, 16, 0]
        )
        style.configure(
            "TNotebook.Tab",
            background=BG_CARD,
            foreground=TEXT_SECONDARY,
            padding=[16, 8],
            font=("Segoe UI", 10, "bold"),
            borderwidth=0
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", ACCENT), ("active", BG_CARD_HOVER)],
            foreground=[("selected", "#0b0f19"), ("active", TEXT_PRIMARY)]
        )

        # Sliders
        style.configure(
            "Horizontal.TScale",
            background=BG_CARD,
            troughcolor=BG_INPUT,
            sliderlength=20,
            borderwidth=0
        )

    def _build_header(self):
        header = tk.Frame(self.root, bg=BG_BASE, height=70)
        header.pack(fill="x", padx=24, pady=(16, 10))

        # Title block
        title_frame = tk.Frame(header, bg=BG_BASE)
        title_frame.pack(side="left")

        title = tk.Label(
            title_frame,
            text="Glidify",
            font=("Segoe UI", 17, "bold"),
            fg=TEXT_PRIMARY,
            bg=BG_BASE
        )
        title.pack(anchor="w")

        subtitle = tk.Label(
            title_frame,
            text="By Haistellar — Apple Magic Trackpad Kinetic Glide for Windows 11",
            font=("Segoe UI", 9),
            fg=TEXT_MUTED,
            bg=BG_BASE
        )
        subtitle.pack(anchor="w")

        # Controls & Status Pill
        actions_frame = tk.Frame(header, bg=BG_BASE)
        actions_frame.pack(side="right")

        self.status_pill = tk.Label(
            actions_frame,
            text="● Engine Active" if self.settings.enabled else "● Paused",
            font=("Segoe UI", 10, "bold"),
            fg=COL_GREEN if self.settings.enabled else COL_AMBER,
            bg=BG_CARD,
            padx=14,
            pady=6,
            relief="flat"
        )
        self.status_pill.pack(side="left", padx=8)

        self.power_btn = tk.Button(
            actions_frame,
            text="Pause" if self.settings.enabled else "Resume",
            font=("Segoe UI", 9, "bold"),
            bg=BG_CARD,
            fg=TEXT_PRIMARY,
            activebackground=BG_CARD_HOVER,
            activeforeground=TEXT_PRIMARY,
            relief="flat",
            padx=16,
            pady=6,
            cursor="hand2",
            command=self._toggle_power
        )
        self.power_btn.pack(side="left")

    def _build_tabs(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=20, pady=8)

        self.tab_playground = tk.Frame(self.notebook, bg=BG_BASE)
        self.tab_wheel = tk.Frame(self.notebook, bg=BG_BASE)
        self.tab_trackpad = tk.Frame(self.notebook, bg=BG_BASE)
        self.tab_blacklist = tk.Frame(self.notebook, bg=BG_BASE)
        self.tab_system = tk.Frame(self.notebook, bg=BG_BASE)

        self.notebook.add(self.tab_playground, text="Playground & Tuning")
        self.notebook.add(self.tab_wheel, text="Mouse Wheel")
        self.notebook.add(self.tab_trackpad, text="Trackpad Mode")
        self.notebook.add(self.tab_blacklist, text="Excluded Apps")
        self.notebook.add(self.tab_system, text="System & Keys")

        self._build_tab_playground()
        self._build_tab_wheel()
        self._build_tab_trackpad()
        self._build_tab_blacklist()
        self._build_tab_system()

    def _build_tab_playground(self):
        # Quick Presets Strip
        preset_frame = tk.Frame(self.tab_playground, bg=BG_BASE)
        preset_frame.pack(fill="x", pady=(10, 14), padx=10)

        lbl = tk.Label(preset_frame, text="Quick Presets:", font=("Segoe UI", 9, "bold"), fg=TEXT_MUTED, bg=BG_BASE)
        lbl.pack(side="left", padx=(0, 10))

        presets = [
            ("Apple Magic Glide", 130, 650, 1.85, 0.965, "appleGlide"),
            ("Deep Coasting Glide", 150, 800, 2.2, 0.975, "appleGlide"),
            ("Snappy Mac", 110, 400, 1.4, 0.94, "appleGlide"),
            ("Direct Minimal", 80, 200, 1.1, 0.88, "linear"),
        ]

        for text, step, dur, accel, frict, curve in presets:
            btn = tk.Button(
                preset_frame,
                text=text,
                font=("Segoe UI", 8, "bold" if "Magic" in text else "normal"),
                bg=ACCENT if "Magic" in text else BG_CARD,
                fg="#0b0f19" if "Magic" in text else TEXT_PRIMARY,
                activebackground=ACCENT,
                activeforeground="#0b0f19",
                relief="flat",
                padx=10,
                pady=4,
                cursor="hand2",
                command=lambda s=step, d=dur, a=accel, f=frict, c=curve: self._apply_preset(s, d, a, f, c)
            )
            btn.pack(side="left", padx=4)

        # Split Layout
        split = tk.Frame(self.tab_playground, bg=BG_BASE)
        split.pack(fill="both", expand=True, padx=10)

        # Left: Interactive Scroll Test Canvas
        left_card = tk.LabelFrame(split, text=" Interactive Test Zone (Scroll Here) ", font=("Segoe UI", 10, "bold"), fg=ACCENT, bg=BG_CARD, padx=10, pady=10)
        left_card.pack(side="left", fill="both", expand=True, padx=(0, 8))

        scroll_bar = tk.Scrollbar(left_card)
        scroll_bar.pack(side="right", fill="y")

        self.test_listbox = tk.Listbox(
            left_card,
            bg=BG_INPUT,
            fg=TEXT_PRIMARY,
            selectbackground=ACCENT,
            selectforeground="#0b0f19",
            font=("Segoe UI", 10),
            borderwidth=0,
            highlightthickness=0,
            yscrollcommand=scroll_bar.set
        )
        self.test_listbox.pack(side="left", fill="both", expand=True)
        scroll_bar.config(command=self.test_listbox.yview)

        for i in range(1, 101):
            if i == 1:
                self.test_listbox.insert("end", f"  Line {i}: [TOP] Scroll with mouse wheel or trackpad here...")
            elif i % 10 == 0:
                self.test_listbox.insert("end", f"  Line {i}: >>> Notice the fluid momentum & deceleration <<<")
            else:
                self.test_listbox.insert("end", f"  Line {i}: High-refresh smooth scrolling test sample row")

        # Right: Real-time Telemetry & Quick Adjusters
        right_card = tk.LabelFrame(split, text=" Live Telemetry & Dynamics ", font=("Segoe UI", 10, "bold"), fg=ACCENT, bg=BG_CARD, padx=14, pady=10)
        right_card.pack(side="right", fill="both", padx=(8, 0))

        # Metrics display
        metrics_box = tk.Frame(right_card, bg=BG_CARD)
        metrics_box.pack(fill="x", pady=6)

        self.lbl_intercepted = tk.Label(metrics_box, text="Intercepted: 0", font=("Segoe UI", 10, "bold"), fg=ACCENT, bg=BG_CARD)
        self.lbl_intercepted.pack(anchor="w", pady=2)

        self.lbl_dispatched = tk.Label(metrics_box, text="Dispatched: 0", font=("Segoe UI", 10, "bold"), fg=COL_GREEN, bg=BG_CARD)
        self.lbl_dispatched.pack(anchor="w", pady=2)

        # Quick Sliders
        self.quick_step_var = tk.DoubleVar(value=self.settings.step_size)
        self._add_slider_row(right_card, "Step Size", self.quick_step_var, 40, 300, 5, "px", self._on_quick_change)

        self.quick_dur_var = tk.DoubleVar(value=self.settings.animation_duration_ms)
        self._add_slider_row(right_card, "Duration", self.quick_dur_var, 150, 900, 10, "ms", self._on_quick_change)

        self.quick_frict_var = tk.DoubleVar(value=self.settings.friction)
        self._add_slider_row(right_card, "Friction (Glide coasting)", self.quick_frict_var, 0.85, 0.985, 0.005, "", self._on_quick_change)

    def _build_tab_wheel(self):
        card = tk.Frame(self.tab_wheel, bg=BG_CARD, padx=20, pady=16)
        card.pack(fill="both", expand=True, padx=14, pady=14)

        self.step_var = tk.DoubleVar(value=self.settings.step_size)
        self._add_slider_row(card, "Step Size (Pixels per tick):", self.step_var, 40, 300, 5, "px", self._save_settings)

        self.dur_var = tk.DoubleVar(value=self.settings.animation_duration_ms)
        self._add_slider_row(card, "Animation Duration (ms):", self.dur_var, 150, 900, 10, "ms", self._save_settings)

        self.accel_var = tk.DoubleVar(value=self.settings.acceleration_factor)
        self._add_slider_row(card, "Flick Acceleration Multiplier:", self.accel_var, 1.0, 3.5, 0.05, "x", self._save_settings)

        self.frict_var = tk.DoubleVar(value=self.settings.friction)
        self._add_slider_row(card, "Deceleration Friction (Coast):", self.frict_var, 0.85, 0.985, 0.005, "", self._save_settings)

        # Easing curve dropdown
        curve_frame = tk.Frame(card, bg=BG_CARD)
        curve_frame.pack(fill="x", pady=10)
        tk.Label(curve_frame, text="Easing Curve:", font=("Segoe UI", 10), fg=TEXT_PRIMARY, bg=BG_CARD).pack(side="left")

        self.curve_var = tk.StringVar(value=self.settings.easing_curve)
        curve_cb = ttk.Combobox(curve_frame, textvariable=self.curve_var, values=["appleGlide", "exponential", "spring", "linear"], state="readonly", width=18)
        curve_cb.pack(side="right")
        curve_cb.bind("<<ComboboxSelected>>", lambda e: self._save_settings())

        # Direction Inversion
        self.inv_v_var = tk.BooleanVar(value=self.settings.invert_vertical)
        cb_v = tk.Checkbutton(card, text="Invert Vertical Scroll Direction", variable=self.inv_v_var, font=("Segoe UI", 10), fg=TEXT_PRIMARY, bg=BG_CARD, selectcolor=BG_INPUT, activebackground=BG_CARD, activeforeground=TEXT_PRIMARY, command=self._save_settings)
        cb_v.pack(anchor="w", pady=6)

        self.inv_h_var = tk.BooleanVar(value=self.settings.invert_horizontal)
        cb_h = tk.Checkbutton(card, text="Invert Horizontal Tilt Direction", variable=self.inv_h_var, font=("Segoe UI", 10), fg=TEXT_PRIMARY, bg=BG_CARD, selectcolor=BG_INPUT, activebackground=BG_CARD, activeforeground=TEXT_PRIMARY, command=self._save_settings)
        cb_h.pack(anchor="w", pady=6)

    def _build_tab_trackpad(self):
        card = tk.Frame(self.tab_trackpad, bg=BG_CARD, padx=20, pady=16)
        card.pack(fill="both", expand=True, padx=14, pady=14)

        self.tp_mode_var = tk.BooleanVar(value=self.settings.trackpad_mode)
        cb_tp = tk.Checkbutton(card, text="Enable Dedicated Precision Trackpad Smoothing", variable=self.tp_mode_var, font=("Segoe UI", 10, "bold"), fg=ACCENT, bg=BG_CARD, selectcolor=BG_INPUT, activebackground=BG_CARD, activeforeground=ACCENT, command=self._save_settings)
        cb_tp.pack(anchor="w", pady=(0, 14))

        self.tp_deadzone_var = tk.DoubleVar(value=self.settings.trackpad_deadzone)
        self._add_slider_row(card, "Jitter Deadzone (filters finger resting jitter):", self.tp_deadzone_var, 0.5, 8.0, 0.5, "px", self._save_settings)

        self.tp_momentum_var = tk.DoubleVar(value=self.settings.trackpad_momentum)
        self._add_slider_row(card, "Momentum Glide Multiplier (post-release inertia):", self.tp_momentum_var, 0.8, 2.5, 0.05, "x", self._save_settings)

        self.tp_inv_var = tk.BooleanVar(value=self.settings.trackpad_invert)
        cb_tp_inv = tk.Checkbutton(card, text="Invert Trackpad Independently of Mouse Wheel", variable=self.tp_inv_var, font=("Segoe UI", 10), fg=TEXT_PRIMARY, bg=BG_CARD, selectcolor=BG_INPUT, activebackground=BG_CARD, activeforeground=TEXT_PRIMARY, command=self._save_settings)
        cb_tp_inv.pack(anchor="w", pady=10)

    def _build_tab_blacklist(self):
        card = tk.Frame(self.tab_blacklist, bg=BG_CARD, padx=20, pady=16)
        card.pack(fill="both", expand=True, padx=14, pady=14)

        tk.Label(card, text="Excluded Applications (Bypasses smoothing for games/CAD):", font=("Segoe UI", 10, "bold"), fg=TEXT_PRIMARY, bg=BG_CARD).pack(anchor="w", pady=(0, 8))

        # Add input frame
        add_frame = tk.Frame(card, bg=BG_CARD)
        add_frame.pack(fill="x", pady=6)

        self.app_entry = tk.Entry(add_frame, font=("Segoe UI", 10), bg=BG_INPUT, fg=TEXT_PRIMARY, insertbackground=TEXT_PRIMARY, relief="flat", highlightthickness=1, highlightcolor=ACCENT)
        self.app_entry.pack(side="left", fill="x", expand=True, padx=(0, 8), ipady=4)

        add_btn = tk.Button(add_frame, text="Add App", font=("Segoe UI", 9, "bold"), bg=ACCENT, fg="#0b0f19", relief="flat", padx=12, pady=4, cursor="hand2", command=self._add_app)
        add_btn.pack(side="left", padx=4)

        detect_btn = tk.Button(add_frame, text="Detect Foreground App", font=("Segoe UI", 9), bg=BG_CARD_HOVER, fg=TEXT_PRIMARY, relief="flat", padx=12, pady=4, cursor="hand2", command=self._detect_app)
        detect_btn.pack(side="left", padx=4)

        # Listbox of apps
        list_frame = tk.Frame(card, bg=BG_CARD)
        list_frame.pack(fill="both", expand=True, pady=10)

        sb = tk.Scrollbar(list_frame)
        sb.pack(side="right", fill="y")

        self.bl_listbox = tk.Listbox(list_frame, font=("Consolas", 10), bg=BG_INPUT, fg=TEXT_PRIMARY, selectbackground=COL_RED, selectforeground="#ffffff", relief="flat", yscrollcommand=sb.set)
        self.bl_listbox.pack(side="left", fill="both", expand=True)
        sb.config(command=self.bl_listbox.yview)

        for app in self.settings.blacklisted_apps:
            self.bl_listbox.insert("end", app)

        rem_btn = tk.Button(card, text="Remove Selected App", font=("Segoe UI", 9), bg=COL_RED, fg="#ffffff", relief="flat", padx=14, pady=4, cursor="hand2", command=self._remove_app)
        rem_btn.pack(anchor="e", pady=4)

    def _build_tab_system(self):
        card = tk.Frame(self.tab_system, bg=BG_CARD, padx=20, pady=16)
        card.pack(fill="both", expand=True, padx=14, pady=14)

        self.autostart_var = tk.BooleanVar(value=self.settings.start_with_windows)
        cb_auto = tk.Checkbutton(card, text="Start with Windows 11 (Automatic background launch)", variable=self.autostart_var, font=("Segoe UI", 10), fg=TEXT_PRIMARY, bg=BG_CARD, selectcolor=BG_INPUT, activebackground=BG_CARD, activeforeground=TEXT_PRIMARY, command=self._save_settings)
        cb_auto.pack(anchor="w", pady=8)

        self.minimized_var = tk.BooleanVar(value=self.settings.start_minimized)
        cb_min = tk.Checkbutton(card, text="Start Minimized to System Tray", variable=self.minimized_var, font=("Segoe UI", 10), fg=TEXT_PRIMARY, bg=BG_CARD, selectcolor=BG_INPUT, activebackground=BG_CARD, activeforeground=TEXT_PRIMARY, command=self._save_settings)
        cb_min.pack(anchor="w", pady=8)

        self.ctrl_var = tk.BooleanVar(value=self.settings.ctrl_passthrough_zoom)
        cb_ctrl = tk.Checkbutton(card, text="Hold Ctrl for Instant Zoom Passthrough (Browser & Editors)", variable=self.ctrl_var, font=("Segoe UI", 10), fg=TEXT_PRIMARY, bg=BG_CARD, selectcolor=BG_INPUT, activebackground=BG_CARD, activeforeground=TEXT_PRIMARY, command=self._save_settings)
        cb_ctrl.pack(anchor="w", pady=8)

        self.alt_var = tk.BooleanVar(value=self.settings.alt_accelerate)
        cb_alt = tk.Checkbutton(card, text="Hold Alt for Double Acceleration", variable=self.alt_var, font=("Segoe UI", 10), fg=TEXT_PRIMARY, bg=BG_CARD, selectcolor=BG_INPUT, activebackground=BG_CARD, activeforeground=TEXT_PRIMARY, command=self._save_settings)
        cb_alt.pack(anchor="w", pady=8)

        btn_reset = tk.Button(card, text="Reset to Recommended Defaults", font=("Segoe UI", 9), bg=BG_CARD_HOVER, fg=COL_AMBER, relief="flat", padx=16, pady=6, cursor="hand2", command=self._reset_defaults)
        btn_reset.pack(anchor="w", pady=(20, 0))

    def _build_footer(self):
        footer = tk.Frame(self.root, bg=BG_BASE, height=44)
        footer.pack(fill="x", padx=24, pady=10)

        lbl = tk.Label(footer, text="All modifications apply immediately to the Windows input hook.", font=("Segoe UI", 9), fg=TEXT_MUTED, bg=BG_BASE)
        lbl.pack(side="left")

        self.saved_feedback = tk.Label(footer, text="", font=("Segoe UI", 9, "bold"), fg=COL_GREEN, bg=BG_BASE)
        self.saved_feedback.pack(side="right")

    def _add_slider_row(self, parent, label_text, var, from_, to, step, unit, callback):
        row = tk.Frame(parent, bg=BG_CARD)
        row.pack(fill="x", pady=6)

        hdr = tk.Frame(row, bg=BG_CARD)
        hdr.pack(fill="x")

        lbl = tk.Label(hdr, text=label_text, font=("Segoe UI", 9), fg=TEXT_PRIMARY, bg=BG_CARD)
        lbl.pack(side="left")

        val_lbl = tk.Label(hdr, text=f"{var.get():.2f}{unit}" if isinstance(step, float) else f"{int(var.get())}{unit}", font=("Segoe UI", 9, "bold"), fg=ACCENT, bg=BG_CARD)
        val_lbl.pack(side="right")

        def on_slide(val):
            v = float(val)
            val_lbl.config(text=f"{v:.2f}{unit}" if isinstance(step, float) else f"{int(v)}{unit}")
            callback()

        scale = ttk.Scale(row, from_=from_, to=to, variable=var, style="Horizontal.TScale", command=on_slide)
        scale.pack(fill="x", pady=2)

    def _toggle_power(self):
        self.settings.enabled = not self.settings.enabled
        hook_manager.update_settings(self.settings)

        if self.settings.enabled:
            self.status_pill.config(text="● Engine Active", fg=COL_GREEN)
            self.power_btn.config(text="Pause")
        else:
            self.status_pill.config(text="● Paused", fg=COL_AMBER)
            self.power_btn.config(text="Resume")

    def _apply_preset(self, step, dur, accel, frict, curve):
        self.settings.step_size = step
        self.settings.animation_duration_ms = dur
        self.settings.acceleration_factor = accel
        self.settings.friction = frict
        self.settings.easing_curve = curve

        self.quick_step_var.set(step)
        self.quick_dur_var.set(dur)
        self.quick_frict_var.set(frict)

        self.step_var.set(step)
        self.dur_var.set(dur)
        self.accel_var.set(accel)
        self.frict_var.set(frict)
        self.curve_var.set(curve)

        self._save_settings()

    def _on_quick_change(self):
        self.settings.step_size = self.quick_step_var.get()
        self.settings.animation_duration_ms = self.quick_dur_var.get()
        self.settings.friction = self.quick_frict_var.get()

        self.step_var.set(self.settings.step_size)
        self.dur_var.set(self.settings.animation_duration_ms)
        self.frict_var.set(self.settings.friction)

        self._save_settings()

    def _save_settings(self):
        self.settings.step_size = self.step_var.get()
        self.settings.animation_duration_ms = self.dur_var.get()
        self.settings.acceleration_factor = self.accel_var.get()
        self.settings.friction = self.frict_var.get()
        self.settings.easing_curve = self.curve_var.get()
        self.settings.invert_vertical = self.inv_v_var.get()
        self.settings.invert_horizontal = self.inv_h_var.get()

        self.settings.trackpad_mode = self.tp_mode_var.get()
        self.settings.trackpad_deadzone = self.tp_deadzone_var.get()
        self.settings.trackpad_momentum = self.tp_momentum_var.get()
        self.settings.trackpad_invert = self.tp_inv_var.get()

        self.settings.start_with_windows = self.autostart_var.get()
        self.settings.start_minimized = self.minimized_var.get()
        self.settings.ctrl_passthrough_zoom = self.ctrl_var.get()
        self.settings.alt_accelerate = self.alt_var.get()

        hook_manager.update_settings(self.settings)

        self.saved_feedback.config(text="Settings Applied ✓")
        self.root.after(1200, lambda: self.saved_feedback.config(text=""))

    def _add_app(self):
        name = self.app_entry.get().strip()
        if name and name not in self.settings.blacklisted_apps:
            self.settings.blacklisted_apps.append(name)
            self.bl_listbox.insert("end", name)
            self.app_entry.delete(0, "end")
            self._save_settings()

    def _remove_app(self):
        sel = self.bl_listbox.curselection()
        if sel:
            idx = sel[0]
            val = self.bl_listbox.get(idx)
            if val in self.settings.blacklisted_apps:
                self.settings.blacklisted_apps.remove(val)
            self.bl_listbox.delete(idx)
            self._save_settings()

    def _detect_app(self):
        proc = hook_manager.get_foreground_process()
        if proc:
            self.app_entry.delete(0, "end")
            self.app_entry.insert(0, proc)

    def _reset_defaults(self):
        def_s = AppSettings()
        self.settings = def_s
        hook_manager.update_settings(def_s)

        self.step_var.set(def_s.step_size)
        self.dur_var.set(def_s.animation_duration_ms)
        self.accel_var.set(def_s.acceleration_factor)
        self.frict_var.set(def_s.friction)
        self.curve_var.set(def_s.easing_curve)
        self.inv_v_var.set(def_s.invert_vertical)
        self.inv_h_var.set(def_s.invert_horizontal)

        self.tp_mode_var.set(def_s.trackpad_mode)
        self.tp_deadzone_var.set(def_s.trackpad_deadzone)
        self.tp_momentum_var.set(def_s.trackpad_momentum)
        self.tp_inv_var.set(def_s.trackpad_invert)

        self.quick_step_var.set(def_s.step_size)
        self.quick_dur_var.set(def_s.animation_duration_ms)
        self.quick_frict_var.set(def_s.friction)

        self.bl_listbox.delete(0, "end")
        for app in def_s.blacklisted_apps:
            self.bl_listbox.insert("end", app)

        self.saved_feedback.config(text="Defaults Restored ✓")
        self.root.after(1200, lambda: self.saved_feedback.config(text=""))

    def _update_metrics(self):
        try:
            intercepted, dispatched = hook_manager.get_metrics()
            self.lbl_intercepted.config(text=f"Intercepted: {intercepted:,}")
            self.lbl_dispatched.config(text=f"Dispatched: {dispatched:,}")
        except Exception:
            pass
        self.root.after(400, self._update_metrics)

    def hide_to_tray(self):
        self.root.withdraw()

    def show_from_tray(self):
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()

def launch_gui():
    root = tk.Tk()
    app = SmoothScrollGUI(root)
    return root, app
