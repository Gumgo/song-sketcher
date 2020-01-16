import pygame
from pygame.locals import *

from song_sketcher import timer
from song_sketcher import transform
from song_sketcher import widget_event

# $TODO make a system to detect un-destroyed widgets which aren't part of any layout

_LONG_PRESS_DURATION = 0.5
_DOUBLE_CLICK_DURATION = 0.5

_KEYS_FROM_PYGAME_KEYS = {
    pygame.K_BACKSPACE: widget_event.KeyCode.BACKSPACE,
    pygame.K_TAB: widget_event.KeyCode.TAB,
    pygame.K_CLEAR: widget_event.KeyCode.CLEAR,
    pygame.K_RETURN: widget_event.KeyCode.RETURN,
    pygame.K_PAUSE: widget_event.KeyCode.PAUSE,
    pygame.K_ESCAPE: widget_event.KeyCode.ESCAPE,
    pygame.K_SPACE: widget_event.KeyCode.SPACE,
    pygame.K_EXCLAIM: widget_event.KeyCode.EXCLAIM,
    pygame.K_QUOTEDBL: widget_event.KeyCode.QUOTEDBL,
    pygame.K_HASH: widget_event.KeyCode.HASH,
    pygame.K_DOLLAR: widget_event.KeyCode.DOLLAR,
    pygame.K_AMPERSAND: widget_event.KeyCode.AMPERSAND,
    pygame.K_QUOTE: widget_event.KeyCode.QUOTE,
    pygame.K_LEFTPAREN: widget_event.KeyCode.LEFTPAREN,
    pygame.K_RIGHTPAREN: widget_event.KeyCode.RIGHTPAREN,
    pygame.K_ASTERISK: widget_event.KeyCode.ASTERISK,
    pygame.K_PLUS: widget_event.KeyCode.PLUS,
    pygame.K_COMMA: widget_event.KeyCode.COMMA,
    pygame.K_MINUS: widget_event.KeyCode.MINUS,
    pygame.K_PERIOD: widget_event.KeyCode.PERIOD,
    pygame.K_SLASH: widget_event.KeyCode.SLASH,
    pygame.K_0: widget_event.KeyCode.NUM_0,
    pygame.K_1: widget_event.KeyCode.NUM_1,
    pygame.K_2: widget_event.KeyCode.NUM_2,
    pygame.K_3: widget_event.KeyCode.NUM_3,
    pygame.K_4: widget_event.KeyCode.NUM_4,
    pygame.K_5: widget_event.KeyCode.NUM_5,
    pygame.K_6: widget_event.KeyCode.NUM_6,
    pygame.K_7: widget_event.KeyCode.NUM_7,
    pygame.K_8: widget_event.KeyCode.NUM_8,
    pygame.K_9: widget_event.KeyCode.NUM_9,
    pygame.K_COLON: widget_event.KeyCode.COLON,
    pygame.K_SEMICOLON: widget_event.KeyCode.SEMICOLON,
    pygame.K_LESS: widget_event.KeyCode.LESS,
    pygame.K_EQUALS: widget_event.KeyCode.EQUALS,
    pygame.K_GREATER: widget_event.KeyCode.GREATER,
    pygame.K_QUESTION: widget_event.KeyCode.QUESTION,
    pygame.K_AT: widget_event.KeyCode.AT,
    pygame.K_LEFTBRACKET: widget_event.KeyCode.LEFTBRACKET,
    pygame.K_BACKSLASH: widget_event.KeyCode.BACKSLASH,
    pygame.K_RIGHTBRACKET: widget_event.KeyCode.RIGHTBRACKET,
    pygame.K_CARET: widget_event.KeyCode.CARET,
    pygame.K_UNDERSCORE: widget_event.KeyCode.UNDERSCORE,
    pygame.K_BACKQUOTE: widget_event.KeyCode.BACKQUOTE,
    pygame.K_a: widget_event.KeyCode.A,
    pygame.K_b: widget_event.KeyCode.B,
    pygame.K_c: widget_event.KeyCode.C,
    pygame.K_d: widget_event.KeyCode.D,
    pygame.K_e: widget_event.KeyCode.E,
    pygame.K_f: widget_event.KeyCode.F,
    pygame.K_g: widget_event.KeyCode.G,
    pygame.K_h: widget_event.KeyCode.H,
    pygame.K_i: widget_event.KeyCode.I,
    pygame.K_j: widget_event.KeyCode.J,
    pygame.K_k: widget_event.KeyCode.K,
    pygame.K_l: widget_event.KeyCode.L,
    pygame.K_m: widget_event.KeyCode.M,
    pygame.K_n: widget_event.KeyCode.N,
    pygame.K_o: widget_event.KeyCode.O,
    pygame.K_p: widget_event.KeyCode.P,
    pygame.K_q: widget_event.KeyCode.Q,
    pygame.K_r: widget_event.KeyCode.R,
    pygame.K_s: widget_event.KeyCode.S,
    pygame.K_t: widget_event.KeyCode.T,
    pygame.K_u: widget_event.KeyCode.U,
    pygame.K_v: widget_event.KeyCode.V,
    pygame.K_w: widget_event.KeyCode.W,
    pygame.K_x: widget_event.KeyCode.X,
    pygame.K_y: widget_event.KeyCode.Y,
    pygame.K_z: widget_event.KeyCode.Z,
    pygame.K_DELETE: widget_event.KeyCode.DELETE,
    pygame.K_KP0: widget_event.KeyCode.KP0,
    pygame.K_KP1: widget_event.KeyCode.KP1,
    pygame.K_KP2: widget_event.KeyCode.KP2,
    pygame.K_KP3: widget_event.KeyCode.KP3,
    pygame.K_KP4: widget_event.KeyCode.KP4,
    pygame.K_KP5: widget_event.KeyCode.KP5,
    pygame.K_KP6: widget_event.KeyCode.KP6,
    pygame.K_KP7: widget_event.KeyCode.KP7,
    pygame.K_KP8: widget_event.KeyCode.KP8,
    pygame.K_KP9: widget_event.KeyCode.KP9,
    pygame.K_KP_PERIOD: widget_event.KeyCode.KP_PERIOD,
    pygame.K_KP_DIVIDE: widget_event.KeyCode.KP_DIVIDE,
    pygame.K_KP_MULTIPLY: widget_event.KeyCode.KP_MULTIPLY,
    pygame.K_KP_MINUS: widget_event.KeyCode.KP_MINUS,
    pygame.K_KP_PLUS: widget_event.KeyCode.KP_PLUS,
    pygame.K_KP_ENTER: widget_event.KeyCode.KP_ENTER,
    pygame.K_KP_EQUALS: widget_event.KeyCode.KP_EQUALS,
    pygame.K_UP: widget_event.KeyCode.UP,
    pygame.K_DOWN: widget_event.KeyCode.DOWN,
    pygame.K_RIGHT: widget_event.KeyCode.RIGHT,
    pygame.K_LEFT: widget_event.KeyCode.LEFT,
    pygame.K_INSERT: widget_event.KeyCode.INSERT,
    pygame.K_HOME: widget_event.KeyCode.HOME,
    pygame.K_END: widget_event.KeyCode.END,
    pygame.K_PAGEUP: widget_event.KeyCode.PAGEUP,
    pygame.K_PAGEDOWN: widget_event.KeyCode.PAGEDOWN,
    pygame.K_F1: widget_event.KeyCode.F1,
    pygame.K_F2: widget_event.KeyCode.F2,
    pygame.K_F3: widget_event.KeyCode.F3,
    pygame.K_F4: widget_event.KeyCode.F4,
    pygame.K_F5: widget_event.KeyCode.F5,
    pygame.K_F6: widget_event.KeyCode.F6,
    pygame.K_F7: widget_event.KeyCode.F7,
    pygame.K_F8: widget_event.KeyCode.F8,
    pygame.K_F9: widget_event.KeyCode.F9,
    pygame.K_F10: widget_event.KeyCode.F10,
    pygame.K_F11: widget_event.KeyCode.F11,
    pygame.K_F12: widget_event.KeyCode.F12,
    pygame.K_F13: widget_event.KeyCode.F13,
    pygame.K_F14: widget_event.KeyCode.F14,
    pygame.K_F15: widget_event.KeyCode.F15,
    pygame.K_NUMLOCK: widget_event.KeyCode.NUMLOCK,
    pygame.K_CAPSLOCK: widget_event.KeyCode.CAPSLOCK,
    pygame.K_SCROLLOCK: widget_event.KeyCode.SCROLLOCK,
    pygame.K_RSHIFT: widget_event.KeyCode.RSHIFT,
    pygame.K_LSHIFT: widget_event.KeyCode.LSHIFT,
    pygame.K_RCTRL: widget_event.KeyCode.RCTRL,
    pygame.K_LCTRL: widget_event.KeyCode.LCTRL,
    pygame.K_RALT: widget_event.KeyCode.RALT,
    pygame.K_LALT: widget_event.KeyCode.LALT,
    pygame.K_RMETA: widget_event.KeyCode.RMETA,
    pygame.K_LMETA: widget_event.KeyCode.LMETA,
    pygame.K_LSUPER: widget_event.KeyCode.LSUPER,
    pygame.K_RSUPER: widget_event.KeyCode.RSUPER,
    pygame.K_MODE: widget_event.KeyCode.MODE,
    pygame.K_HELP: widget_event.KeyCode.HELP,
    pygame.K_PRINT: widget_event.KeyCode.PRINT,
    pygame.K_SYSREQ: widget_event.KeyCode.SYSREQ,
    pygame.K_BREAK: widget_event.KeyCode.BREAK,
    pygame.K_MENU: widget_event.KeyCode.MENU,
    pygame.K_POWER: widget_event.KeyCode.POWER,
    pygame.K_EURO: widget_event.KeyCode.EURO
}

_widget_manager = None

def initialize(display_size):
    global _widget_manager
    _widget_manager = _WidgetManager(display_size)

def shutdown():
    global _widget_manager
    if _widget_manager is not None:
        _widget_manager = None

def get():
    return _widget_manager

class _WidgetManager:
    def __init__(self, display_size):
        pygame.key.set_repeat(500, 50)
        self._display_size = display_size
        self._widget_placements_stale = False
        self._last_mouse_position = None
        self._root_widget = None
        self._widget_under_mouse = None # The widget currently under the mouse
        self._captured_widget = None    # The currently captured widget - all events will route to it
        self._focused_widget = None     # The widget with keyboard focus
        self._long_press_timers = {}    # Maps widget to timer
        self._double_click_widget = None
        self._double_click_button = None
        self._double_click_timer = None
        self._overlay_funcs = []

    @property
    def display_size(self):
        return self._display_size

    @property
    def captured_widget(self):
        return self._captured_widget

    @property
    def focused_widget(self):
        return self._focused_widget

    @property
    def widget_under_mouse(self):
        return self._widget_under_mouse

    def set_root_widget(self, root_widget):
        self._root_widget = root_widget

    def destroy_widget(self, widget):
        if self._widget_under_mouse is widget:
            self._widget_under_mouse = None
        self.release_captured_widget(widget)
        self.release_focused_widget(widget)
        self._cancel_long_press_timer(widget)
        if widget is self._double_click_widget:
            self._cancel_double_click_timer()

    # Used to force re-evaluation of whether the mouse is inside or outside widgets
    def invalidate_widget_placements(self):
        self._widget_placements_stale = True

    def capture_widget(self, widget):
        self._captured_widget = widget

    def release_captured_widget(self, widget):
        if self._captured_widget is widget:
            self._captured_widget = None

    def focus_widget(self, widget):
        prev_focused_widget = self._focused_widget
        self._focused_widget = widget
        if prev_focused_widget is not None and prev_focused_widget is not widget:
            self._send_event_to_widget(widget_event.FocusLostEvent(), prev_focused_widget, False)

    def release_focused_widget(self, widget):
        if widget is None or self._focused_widget is widget:
            if self._focused_widget is not None:
                prev_focused_widget = self._focused_widget
                self._focused_widget = None
                self._send_event_to_widget(widget_event.FocusLostEvent(), prev_focused_widget, False)

    def add_overlay(self, draw_func):
        self._overlay_funcs.append(draw_func)

    def draw(self):
        if self._root_widget is not None:
            self._root_widget.draw(transform.Transform())
        for draw_func in self._overlay_funcs:
            draw_func()
        self._overlay_funcs.clear()

    def begin_process_events(self):
        if self._root_widget is None:
            return

        if self._widget_placements_stale and self._last_mouse_position is not None:
            self._widget_placements_stale = False
            self._send_mouse_enter_leave_events()

    def process_event(self, pygame_event):
        if self._root_widget is None:
            return

        if pygame_event.type == pygame.KEYDOWN:
            key_press_event = widget_event.KeyEvent(
                widget_event.KeyEventType.PRESS,
                _KEYS_FROM_PYGAME_KEYS.get(pygame_event.key, None),
                pygame_event.unicode)

            if self._focused_widget is not None:
                self._send_event_to_widget(key_press_event, self._focused_widget, True)
        elif pygame_event.type == pygame.KEYUP:
            key_release_event = widget_event.KeyEvent(
                widget_event.KeyEventType.RELEASE,
                _KEYS_FROM_PYGAME_KEYS.get(pygame_event.key, None),
                None)

            if self._focused_widget is not None:
                self._send_event_to_widget(key_release_event, self._focused_widget, True)
        elif pygame_event.type == pygame.MOUSEMOTION:
            self._last_mouse_position = (pygame_event.pos[0], self._display_size[1] - pygame_event.pos[1] - 1)
            self._send_mouse_enter_leave_events()

            mouse_move_event = widget_event.MouseEvent(
                widget_event.MouseEventType.MOVE,
                None,
                self._last_mouse_position[0],
                self._last_mouse_position[1])
            self._send_event_to_captured_widget_and_other(mouse_move_event, self._widget_under_mouse, False)
        elif pygame_event.type == pygame.MOUSEBUTTONDOWN:
            button = self._get_mouse_button_from_pygame_event(pygame_event)

            if self._double_click_button is button and self._is_a_ancestor_of_b(self._double_click_widget, self._widget_under_mouse):
                double_click_widget = self._double_click_widget
                self._cancel_double_click_timer()

                # Note: double-click doesn't work with the captured widget, don't rely on capturing for double clicking
                double_click_event = widget_event.MouseEvent(
                    widget_event.MouseEventType.DOUBLE_CLICK,
                    button,
                    self._last_mouse_position[0],
                    self._last_mouse_position[1])
                self._send_event_to_widget(double_click_event, double_click_widget, False)
            else:
                self._cancel_double_click_timer()

                mouse_press_event = widget_event.MouseEvent(
                    widget_event.MouseEventType.PRESS,
                    button,
                    self._last_mouse_position[0],
                    self._last_mouse_position[1])
                widget = self._send_event_to_captured_widget_or_other(mouse_press_event, self._widget_under_mouse, True)

                if widget is not None:
                    self._cancel_long_press_timer(widget)
                    self._long_press_timers[widget] = timer.Timer(
                        lambda: self._send_long_press_event(widget, mouse_press_event.button),
                        _LONG_PRESS_DURATION)
                    self._double_click_button = button
                    self._double_click_widget = widget
                    self._double_click_timer = timer.Timer(self._cancel_double_click_timer, _DOUBLE_CLICK_DURATION)
        elif pygame_event.type == pygame.MOUSEBUTTONUP:
            self._cancel_all_long_press_timers()

            mouse_release_event = widget_event.MouseEvent(
                widget_event.MouseEventType.RELEASE,
                self._get_mouse_button_from_pygame_event(pygame_event),
                self._last_mouse_position[0],
                self._last_mouse_position[1])
            self._send_event_to_captured_widget_or_other(mouse_release_event, self._widget_under_mouse, True)

    def _send_mouse_enter_leave_events(self):
        # Widgets have moved - determine which widget the mouse lies in
        widget_under_mouse = self._root_widget.get_widget_for_point(
            transform.Transform(),
            self._last_mouse_position[0],
            self._last_mouse_position[1])

        if widget_under_mouse is not self._widget_under_mouse:
            previous_widget_under_mouse = self._widget_under_mouse
            self._widget_under_mouse = widget_under_mouse
            if previous_widget_under_mouse is not None:
                self._cancel_long_press_timer(previous_widget_under_mouse)
                previous_widget_under_mouse.process_event(widget_event.MouseLeaveEvent())
            if self._widget_under_mouse is not None:
                self._widget_under_mouse.process_event(widget_event.MouseEnterEvent())

    def _send_event_to_widget(self, event, widget, propagate_to_parent):
        assert widget is not None
        while widget is not None:
            processed = widget.process_event(event)
            if processed:
                return widget
            widget = widget.parent if propagate_to_parent else None

    def _send_event_to_captured_widget_and_other(self, event, other_widget, propagate_to_parent):
        widgets = []
        captured_widget = self._captured_widget # Cache it in case it changes
        if captured_widget is not None:
            widget = self._send_event_to_widget(event, captured_widget, False)
            if widget is not None:
                widgets.append(widget)
        if other_widget is not None and other_widget is not captured_widget:
            widget = self._send_event_to_widget(event, other_widget, propagate_to_parent)
            if widget is not None:
                widgets.append(widget)
        return tuple(widgets)

    def _send_event_to_captured_widget_or_other(self, event, other_widget, propagate_to_parent):
        if self._captured_widget is not None:
            return self._send_event_to_widget(event, self._captured_widget, False)
        elif other_widget is not None:
            return self._send_event_to_widget(event, other_widget, propagate_to_parent)
        return None

    def _is_a_ancestor_of_b(self, widget_a, widget_b):
        current_ancestor = widget_b
        while current_ancestor is not None:
            if current_ancestor is widget_a:
                return True
            current_ancestor = current_ancestor.parent
        return False

    def _get_mouse_button_from_pygame_event(self, pygame_event):
        return {
            1: widget_event.MouseButton.LEFT,
            2: widget_event.MouseButton.MIDDLE,
            3: widget_event.MouseButton.RIGHT,
            4: widget_event.MouseButton.SCROLL_UP,
            5: widget_event.MouseButton.SCROLL_DOWN
        }[pygame_event.button]

    def _cancel_long_press_timer(self, widget):
        timer = self._long_press_timers.pop(widget, None)
        if timer is not None:
            timer.cancel()

    def _cancel_all_long_press_timers(self):
        for timer in self._long_press_timers.values():
            timer.cancel()
        self._long_press_timers.clear()

    def _cancel_double_click_timer(self):
        if self._double_click_widget is not None:
            self._double_click_timer.cancel()
            self._double_click_widget = None
            self._double_click_button = None
            self._double_click_timer = None

    def _send_long_press_event(self, widget, button):
        self._long_press_timers.pop(widget)
        mouse_press_event = widget_event.MouseEvent(
            widget_event.MouseEventType.LONG_PRESS,
            button,
            self._last_mouse_position[0],
            self._last_mouse_position[1])
        # We don't want to propagate, because the original click event already propagated
        self._send_event_to_widget(mouse_press_event, widget, False)
