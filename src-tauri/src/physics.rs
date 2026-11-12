use std::time::Instant;
use crate::config::AppSettings;

#[derive(Debug, Clone)]
pub struct AxisState {
    pub velocity: f64,
    pub target_delta: f64,
    pub accumulated_sub_delta: f64,
    pub last_event_time: Option<Instant>,
    pub is_gliding: bool,
}

impl AxisState {
    pub fn new() -> Self {
        Self {
            velocity: 0.0,
            target_delta: 0.0,
            accumulated_sub_delta: 0.0,
            last_event_time: None,
            is_gliding: false,
        }
    }

    pub fn reset(&mut self) {
        self.velocity = 0.0;
        self.target_delta = 0.0;
        self.accumulated_sub_delta = 0.0;
        self.last_event_time = None;
        self.is_gliding = false;
    }
}

pub struct ScrollPhysicsEngine {
    pub vertical: AxisState,
    pub horizontal: AxisState,
    pub last_tick_time: Instant,
    pub total_intercepted_events: u64,
    pub total_dispatched_frames: u64,
}

impl ScrollPhysicsEngine {
    pub fn new() -> Self {
        Self {
            vertical: AxisState::new(),
            horizontal: AxisState::new(),
            last_tick_time: Instant::now(),
            total_intercepted_events: 0,
            total_dispatched_frames: 0,
        }
    }

    /// Process an incoming raw scroll event from the OS hook.
    /// Returns true if the event was consumed and added to the physics queue.
    pub fn on_input(
        &mut self,
        raw_delta: i16,
        is_horizontal: bool,
        is_trackpad: bool,
        settings: &AppSettings,
    ) -> bool {
        if !settings.enabled {
            return false;
        }

        self.total_intercepted_events += 1;
        let axis = if is_horizontal {
            &mut self.horizontal
        } else {
            &mut self.vertical
        };

        let now = Instant::now();
        let mut delta = raw_delta as f64;

        // Apply trackpad deadzone & filtering
        if is_trackpad && settings.trackpad_mode {
            if delta.abs() < settings.trackpad_deadzone {
                return true; // Swallow jitter without triggering motion
            }
        }

        // Apply direction inversion
        if is_horizontal {
            if settings.invert_horizontal {
                delta = -delta;
            }
        } else {
            let invert = if is_trackpad {
                settings.trackpad_invert
            } else {
                settings.invert_vertical
            };
            if invert {
                delta = -delta;
            }
        }

        // Calculate flick acceleration based on event frequency
        let mut multiplier = 1.0;
        if let Some(last_time) = axis.last_event_time {
            let elapsed_ms = now.duration_since(last_time).as_secs_f64() * 1000.0;
            if elapsed_ms < 120.0 && elapsed_ms > 1.0 {
                // Rapid flicks scale up smoothly with acceleration_factor
                let ratio = (120.0 - elapsed_ms) / 120.0;
                multiplier += ratio * (settings.acceleration_factor - 1.0);
            }
        }
        axis.last_event_time = Some(now);

        // Normalize mouse wheel vs trackpad step sizes
        let impulse = if is_trackpad {
            delta * multiplier * settings.trackpad_momentum
        } else {
            // Standard mouse wheel delta is typically ±120
            let sign = if delta >= 0.0 { 1.0 } else { -1.0 };
            sign * settings.step_size * multiplier
        };

        // If user reverses direction suddenly, cancel existing opposite inertia
        if (axis.velocity > 0.0 && impulse < 0.0) || (axis.velocity < 0.0 && impulse > 0.0) {
            axis.velocity = 0.0;
            axis.target_delta = 0.0;
        }

        axis.velocity += impulse * (1000.0 / settings.animation_duration_ms.max(100.0));
        axis.target_delta += impulse;
        axis.is_gliding = true;

        true
    }

    /// Step the physics simulation forward by dt (in seconds).
    /// Returns (vertical_step_to_send, horizontal_step_to_send).
    pub fn update(&mut self, dt_secs: f64, settings: &AppSettings) -> (i32, i32) {
        let v_step = self.update_axis(&mut self.vertical, dt_secs, settings);
        let h_step = self.update_axis(&mut self.horizontal, dt_secs, settings);

        if v_step != 0 || h_step != 0 {
            self.total_dispatched_frames += 1;
        }

        (v_step, h_step)
    }

    fn update_axis(&mut self, axis: &mut AxisState, dt_secs: f64, settings: &AppSettings) -> i32 {
        if !axis.is_gliding && axis.velocity.abs() < 0.01 && axis.target_delta.abs() < 0.01 {
            axis.reset();
            return 0;
        }

        let dt_factor = (dt_secs * 60.0).clamp(0.1, 3.0);
        let mut dispatch_amount = 0.0;

        match settings.easing_curve.as_str() {
            "exponential" => {
                // Viscous exponential friction decay (macOS style glide)
                let friction = settings.friction.powf(dt_factor);
                let step = axis.velocity * dt_secs * 60.0;
                axis.velocity *= friction;
                dispatch_amount = step;

                if axis.velocity.abs() < 0.5 {
                    axis.reset();
                }
            }
            "spring" => {
                // Damped harmonic spring physics
                let spring_k = 18.0;
                let damping = 0.88_f64.powf(dt_factor);
                let force = -spring_k * (axis.target_delta * 0.1);
                axis.velocity = (axis.velocity + force * dt_secs) * damping;
                let step = axis.velocity * dt_secs * 60.0;
                axis.target_delta -= step;
                dispatch_amount = step;

                if axis.velocity.abs() < 0.3 && axis.target_delta.abs() < 1.0 {
                    axis.reset();
                }
            }
            "linear" => {
                // Fixed speed decimation
                let speed = 400.0 * dt_secs;
                if axis.target_delta.abs() > speed {
                    let sign = if axis.target_delta > 0.0 { 1.0 } else { -1.0 };
                    dispatch_amount = sign * speed;
                    axis.target_delta -= dispatch_amount;
                } else {
                    dispatch_amount = axis.target_delta;
                    axis.reset();
                }
            }
            _ => {
                // "easeOutCubic" default: progressive easing towards target
                let decay_rate = 1.0 - (1.0 - settings.friction).powf(dt_factor);
                let step = axis.target_delta * decay_rate.clamp(0.08, 0.45);
                axis.target_delta -= step;
                dispatch_amount = step;

                if axis.target_delta.abs() < 0.4 {
                    dispatch_amount += axis.target_delta;
                    axis.reset();
                }
            }
        }

        // Accumulate sub-deltas and convert into integer mouse wheel events
        axis.accumulated_sub_delta += dispatch_amount;
        let delta_to_emit = axis.accumulated_sub_delta.round() as i32;
        if delta_to_emit != 0 {
            axis.accumulated_sub_delta -= delta_to_emit as f64;
        }

        delta_to_emit
    }

    pub fn has_active_motion(&self) -> bool {
        self.vertical.is_gliding || self.horizontal.is_gliding
    }
}
