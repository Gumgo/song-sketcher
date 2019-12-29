from enum import Enum

_transition_manager = None

def initialize():
    global _transition_manager
    _transition_manager = _TransitionManager()

def shutdown():
    global _transition_manager
    if _transition_manager is not None:
        _transition_manager = None

def update(dt):
    _transition_manager.update_transitions(dt)

class _TransitionManager:
    def __init__(self):
        self._active_transitions = []

    def start_transition(self, transition):
        self._active_transitions.append(transition)

    def stop_transition(self, transition):
        assert transition in self._active_transitions
        self._active_transitions.remove(transition)

    def update_transitions(self, dt):
        self._active_transitions = [x for x in self._active_transitions if not x.update(dt)]

class Parameter:
    def __init__(self, value):
        self._value = value
        self._change_listeners = []

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        self._set_value(value)

    def add_change_listener(self, change_listener):
        self._change_listeners.append(change_listener)

    def remove_change_listener(self, change_listener):
        self._change_listeners.remove(change_listener)

    def _set_value(self, value):
        if value != self._value:
            self._value = value
            for change_listener in self._change_listeners:
                change_listener(value)

class AnimatableParameter(Parameter):
    def __init__(self, value):
        super().__init__(value)
        self._active_transition = None

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        self._set_value(value)
        # Stop any transition if we're setting the value manually
        if self._active_transition is not None:
            _transition_manager.stop_transition(self._active_transition)

    def transition(self):
        if self._active_transition is not None:
            _transition_manager.stop_transition(self._active_transition)
        self._active_transition = Transition(self)
        _transition_manager.start_transition(self._active_transition)
        return self._active_transition

    def _clear_active_transition(self):
        self._active_transition = None

class TransitionType(Enum):
    LINEAR = 0
    EASE_IN = 1
    EASE_OUT = 2
    EASE_IN_EASE_OUT = 3

class Transition:
    def __init__(self, parameter):
        self._parameter = parameter
        self._target_value = None
        self._duration = None
        self._transition_type = TransitionType.LINEAR

        self._initial_value = parameter.value
        self._ratio = 0.0

    def target(self, target_value):
        self._target_value = target_value
        return self

    def delay(self, delay):
        self._ratio = -delay
        return self

    def duration(self, duration):
        self._duration = duration
        return self

    def ease_in(self):
        self._transition_type = TransitionType.EASE_IN
        return self

    def ease_out(self):
        self._transition_type = TransitionType.EASE_OUT
        return self

    def ease_in_ease_out(self):
        self._transition_type = TransitionType.EASE_IN_EASE_OUT
        return self

    # Returns whether the transition is complete
    def update(self, dt):
        assert self._target_value is not None
        assert self._duration > 0.0

        self._ratio = min(self._ratio + dt / self._duration, 1.0)
        ratio = max(self._ratio, 0.0)

        def ease_in(x):
            return x * x

        def ease_out(x):
            y = 1.0 - x
            return 1.0 - y * y

        def ease_in_ease_out(x):
            return x * x * (3.0 - 2.0 * x)

        curved_ratio = {
            TransitionType.LINEAR: lambda r: r,
            TransitionType.EASE_IN: ease_in,
            TransitionType.EASE_OUT: ease_out,
            TransitionType.EASE_IN_EASE_OUT: ease_in_ease_out,
        }[self._transition_type](ratio)

        self._parameter._set_value(_lerp(self._initial_value, self._target_value, curved_ratio))

        done = (self._ratio == 1.0)
        if done:
            self._parameter._clear_active_transition()
        return done

def _lerp(a, b, r):
    assert type(a) == type(b)
    if isinstance(a, float) or isinstance(a, int):
        return a * (1 - r) + b * r
    elif isinstance(a, tuple) or isinstance(a, list):
        return tuple(x * (1 - r) + y * r for x, y in zip(a, b))
    else:
        assert False
