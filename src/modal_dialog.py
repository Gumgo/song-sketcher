import constants
import timer
from units import *
import widget
import widget_manager

# Returns a function to destroy the dialog
def show_modal_dialog(stack_widget, layout_widget):
    widget_manager.get().release_focused_widget(None)

    background = widget.RectangleWidget()
    background.width.value, background.height.value = widget_manager.get().display_size
    background.color.value = (0.0, 0.0, 0.0, 0.0)

    dialog_background = widget.BackgroundWidget()
    dialog_background.color.value = (0.75, 0.25, 0.4, 1.0)
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

    stack_widget.push_child(background)
    stack_widget.push_child(dialog_background)
    stack_widget.push_child(ui_blocker)

    transition_time = 0.25
    background.color.transition().target((0.0, 0.0, 0.0, 0.5)).duration(transition_time).ease_out()
    dialog_background.y.value = dialog_start_y
    dialog_background.y.transition().target(dialog_end_y).duration(transition_time).ease_out()

    def clear_ui_blocker():
        stack_widget.pop_child()
        # Don't destroy the UI blocker yet - it will be reused
    transition_timer = timer.Timer(clear_ui_blocker, transition_time)

    def destroy_dialog():
        assert not transition_timer.is_running()

        stack_widget.push_child(ui_blocker)

        background.color.transition().target((0.0, 0.0, 0.0, 0.0)).duration(transition_time).ease_in()
        dialog_background.y.transition().target(dialog_start_y).duration(transition_time).ease_in()

        def clear_widgets():
            stack_widget.pop_child()
            stack_widget.pop_child()
            stack_widget.pop_child()
            background.destroy()
            dialog_background.destroy()
            ui_blocker.destroy()
        timer.Timer(clear_widgets, transition_time)

    return destroy_dialog
