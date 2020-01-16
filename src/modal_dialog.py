import constants
import drawing
import timer
from units import *
import widget
import widget_manager

_active_modal_count = 0
_background_widget = None

# Returns a function to destroy the dialog
def show_modal_dialog(stack_widget, layout_widget):
    global _active_modal_count
    global _background_widget

    widget_manager.get().release_focused_widget(None)

    # Only create the background for the first modal, otherwise things would darken multiple times
    create_background = _background_widget is None
    _active_modal_count += 1

    if _background_widget is None:
        _background_widget = widget.RectangleWidget()
        _background_widget.width.value, _background_widget.height.value = widget_manager.get().display_size
        _background_widget.color.value = (0.0, 0.0, 0.0, 0.0)

    dialog_background = widget.BackgroundWidget()
    dialog_background.color.value = (0.75, 0.25, 0.4, 1.0)
    dialog_background.border_thickness.value = points(4.0)
    dialog_background.border_color.value = (0.375, 0.125, 0.2, 1.0)
    dialog_background.radius.value = inches(0.25)

    outer_layout = widget.HStackedLayoutWidget()
    outer_layout.margin = inches(0.25)

    outer_layout_b = widget.VStackedLayoutWidget()

    dialog_background.set_child(outer_layout)
    outer_layout.add_child(outer_layout_b)
    outer_layout_b.add_child(layout_widget)

    dialog_background.layout_widget(
        (0.0, 0.0),
        widget_manager.get().display_size,
        widget.HorizontalPlacement.CENTER,
        widget.VerticalPlacement.MIDDLE)

    ui_blocker = widget.AbsoluteLayoutWidget()

    dialog_height = dialog_background.height.value
    dialog_end_y = dialog_background.y.value
    dialog_start_y = dialog_end_y - (widget_manager.get().display_size[1] + dialog_height) * 0.5
    if SNAP_TO_PIXELS:
        dialog_start_y = float(round(dialog_start_y))

    if create_background:
        stack_widget.push_child(_background_widget)
    stack_widget.push_child(dialog_background)
    stack_widget.push_child(ui_blocker)

    transition_time = 0.25
    _background_widget.color.transition().target((0.0, 0.0, 0.0, 0.5)).duration(transition_time).ease_out()
    dialog_background.y.value = dialog_start_y
    dialog_background.y.transition().target(dialog_end_y).duration(transition_time).ease_out()

    def clear_ui_blocker():
        stack_widget.remove_child(ui_blocker)
        # Don't destroy the UI blocker yet - it will be reused
    transition_timer = timer.Timer(clear_ui_blocker, transition_time)

    def destroy_dialog():
        global _active_modal_count
        assert not transition_timer.is_running()

        stack_widget.push_child(ui_blocker)

        # If this is the last active modal, fade the background out
        if _active_modal_count == 1:
            _background_widget.color.transition().target((0.0, 0.0, 0.0, 0.0)).duration(transition_time).ease_in()
        dialog_background.y.transition().target(dialog_start_y).duration(transition_time).ease_in()

        _active_modal_count -= 1
        assert _active_modal_count >= 0

        def clear_widgets():
            global _background_widget

            # Remove the background if no new modal has been created since we started the transition
            if _active_modal_count == 0:
                stack_widget.remove_child(_background_widget)
                _background_widget.destroy()
                _background_widget = None

            stack_widget.remove_child(dialog_background)
            stack_widget.remove_child(ui_blocker)
            dialog_background.destroy()
            ui_blocker.destroy()

        timer.Timer(clear_widgets, transition_time)

    return destroy_dialog

def show_simple_modal_dialog(stack_widget, title, text, buttons, on_closed_func):
    layout = widget.VStackedLayoutWidget()

    title_widget = widget.TextWidget()
    layout.add_child(title_widget)
    title_widget.text = title
    title_widget.size.value = points(20.0)
    title_widget.horizontal_alignment = drawing.HorizontalAlignment.CENTER
    title_widget.vertical_alignment = drawing.VerticalAlignment.MIDDLE

    layout.add_padding(points(12.0))

    text_widget = widget.TextWidget()
    layout.add_child(text_widget)
    text_widget.text = text
    text_widget.horizontal_alignment = drawing.HorizontalAlignment.CENTER
    text_widget.vertical_alignment = drawing.VerticalAlignment.MIDDLE

    layout.add_padding(points(12.0))

    buttons_layout = widget.HStackedLayoutWidget()
    layout.add_child(buttons_layout)
    buttons_layout.add_padding(0.0, weight = 1.0)

    class Context:
        def __init__(self):
            self.destroy_func = None

        def button_pressed(self, i):
            self.destroy_func()
            if on_closed_func is not None:
                on_closed_func(i)

    context = Context()
    for i, button_text in enumerate(buttons):
        button_widget = widget.TextButtonWidget()
        if i > 0:
            buttons_layout.add_padding(points(4.0))
        buttons_layout.add_child(button_widget)
        button_widget.text = button_text
        button_widget.action_func = lambda i = i: context.button_pressed(i)

    context.destroy_func = show_modal_dialog(stack_widget, layout)
