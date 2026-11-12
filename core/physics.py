"""
SmoothScroll Physics Engine — Apple Magic Trackpad Kinetic Glide Model
Simulates authentic macOS / iOS inertial glide with viscous exponential decay.
"""

import time
import math
from typing import Tuple, Optional
from core.config import AppSettings

class AxisState:
    def __init__(self):
        self.velocity: float = 0.0
        self.target_delta: float = 0.0
        self.accumulated_sub_delta: float = 0.0
        self.last_event_time: Optional[float] = None
        self.is_gliding: bool = False

    def reset(self):
        self.velocity = 0.0
        self.target_delta = 0.0
        self.accumulated_sub_delta = 0.0
        self.last_event_time = None
        self.is_gliding = False

class ScrollPhysicsEngine:
    def __init__(self):
        self.vertical = AxisState()
        self.horizontal = AxisState()
        self.total_intercepted = 0
        self.total_dispatched = 0

    def on_input(self, raw_delta: int, is_horizontal: bool, is_trackpad: bool, settings: AppSettings) -> bool:
        if not settings.enabled:
            return False

        self.total_intercepted += 1
        axis = self.horizontal if is_horizontal else self.vertical
        now = time.perf_counter()
        delta = float(raw_delta)

        # Trackpad jitter deadzone filter
        if is_trackpad and settings.trackpad_mode:
            if abs(delta) < settings.trackpad_deadzone:
                return True

        # Direction Inversion
        if is_horizontal:
            if settings.invert_horizontal:
                delta = -delta
        else:
            invert = settings.trackpad_invert if is_trackpad else settings.invert_vertical
            if invert:
                delta = -delta

        # Flick acceleration (frequent ticks increase kinetic energy)
        multiplier = 1.0
        if axis.last_event_time is not None:
            elapsed_ms = (now - axis.last_event_time) * 1000.0
            if 0.5 < elapsed_ms < 140.0:
                ratio = (140.0 - elapsed_ms) / 140.0
                multiplier += ratio * (settings.acceleration_factor - 1.0)
        axis.last_event_time = now

        # Kinetic impulse calculation (tuned for authentic Apple Magic Trackpad glide)
        if is_trackpad:
            # Touchpad gesture gives direct velocity impulse
            impulse = delta * multiplier * settings.trackpad_momentum * 1.8
        else:
            # Physical mouse wheel notch generates sustained kinetic impulse
            sign = 1.0 if delta >= 0.0 else -1.0
            impulse = sign * settings.step_size * multiplier * 0.9

        # Sudden direction reversal cancels opposing momentum instantly
        if (axis.velocity > 0.0 and impulse < 0.0) or (axis.velocity < 0.0 and impulse > 0.0):
            axis.velocity = 0.0
            axis.target_delta = 0.0

        # Inject kinetic momentum into the glide system
        axis.velocity += impulse * 14.5
        axis.target_delta += impulse
        axis.is_gliding = True

        return True

    def update(self, dt: float, settings: AppSettings) -> Tuple[int, int]:
        # Bound dt to prevent physics explosions on background stalls
        bounded_dt = max(0.001, min(0.033, dt))
        v_step = self._update_axis(self.vertical, bounded_dt, settings)
        h_step = self._update_axis(self.horizontal, bounded_dt, settings)

        if v_step != 0 or h_step != 0:
            self.total_dispatched += 1

        return v_step, h_step

    def _update_axis(self, axis: AxisState, dt: float, settings: AppSettings) -> int:
        if not axis.is_gliding and abs(axis.velocity) < 0.05 and abs(axis.target_delta) < 0.05:
            axis.reset()
            return 0

        curve = settings.easing_curve
        dispatch_amount = 0.0

        if curve == "spring":
            # Damped harmonic oscillator
            damping = math.pow(0.89, dt * 120.0)
            spring_force = -16.0 * (axis.target_delta * 0.1)
            axis.velocity = (axis.velocity + spring_force * dt) * damping
            step = axis.velocity * dt * 45.0
            axis.target_delta -= step
            dispatch_amount = step
            if abs(axis.velocity) < 0.2 and abs(axis.target_delta) < 0.8:
                axis.reset()

        elif curve == "linear":
            speed = 600.0 * dt
            if abs(axis.target_delta) > speed:
                sign = 1.0 if axis.target_delta > 0.0 else -1.0
                dispatch_amount = sign * speed
                axis.target_delta -= dispatch_amount
            else:
                dispatch_amount = axis.target_delta
                axis.reset()

        else:
            # Default & "appleGlide" / "exponential":
            # Continuous viscous exponential decay (macOS Magic Trackpad glide)
            # High-friction baseline (0.95 - 0.97) gives a deep, long, frictionless glide
            friction = max(0.85, min(0.985, settings.friction))
            decay = math.pow(friction, dt * 100.0)
            
            step = axis.velocity * dt
            axis.velocity *= decay
            dispatch_amount = step

            if abs(axis.velocity) < 0.2:
                axis.reset()

        # Sub-delta precision accumulator
        axis.accumulated_sub_delta += dispatch_amount
        delta_to_emit = int(round(axis.accumulated_sub_delta))
        if delta_to_emit != 0:
            axis.accumulated_sub_delta -= float(delta_to_emit)

        return delta_to_emit

    def has_active_motion(self) -> bool:
        return self.vertical.is_gliding or self.horizontal.is_gliding
