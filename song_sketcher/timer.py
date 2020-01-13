_timer_manager = None

def initialize():
    global _timer_manager
    _timer_manager = _TimerManager()

def shutdown():
    global _timer_manager
    if _timer_manager is not None:
        _timer_manager.shutdown()
        _timer_manager = None

def update(dt):
    _timer_manager.update(dt)

class _TimerManager:
    def __init__(self):
        self._active_timers = []
        self._active_updaters = []

    def shutdown(self):
        pass

    def update(self, dt):
        self._active_timers = [x for x in self._active_timers if not x.update(dt)]
        self._active_updaters = [x for x in self._active_updaters if not x.update(dt)]

    def add_timer(self, timer):
        self._active_timers.append(timer)

    def add_updater(self, updater):
        self._active_updaters.append(updater)

class Timer:
    def __init__(self, func, duration):
        self._func = func
        self._time_remaining = duration
        self._running = True
        _timer_manager.add_timer(self)

    def update(self, dt):
        if not self._running:
            return True

        self._time_remaining = max(self._time_remaining - dt, 0.0)
        if self._time_remaining == 0.0:
            self._func()
            self._running = False
            return True

        return False

    def is_running(self):
        return self._running

    def cancel(self):
        self._running = False

class Updater:
    def __init__(self, func):
        self._func = func
        self._running = True
        _timer_manager.add_updater(self)

    def update(self, dt):
        if not self._running:
            return True

        self._func(dt)
        return False

    def is_running(self):
        return self._running

    def cancel(self):
        self._running = False
