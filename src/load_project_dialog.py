import drawing
import modal_dialog
import project_manager
from units import *
import widget

class LoadProjectDialog:
    def __init__(self, stack_widget, on_project_selected_func):
        self._stack_widget = stack_widget
        self._on_project_selected_func = on_project_selected_func

        layout = widget.VStackedLayoutWidget()

        title = widget.TextWidget()
        title.text = "Load project"
        title.size.value = points(20.0)
        title.horizontal_alignment = drawing.HorizontalAlignment.CENTER
        title.vertical_alignment = drawing.VerticalAlignment.MIDDLE
        layout.add_child(title)

        layout.add_padding(points(12.0))

        # $TODO replace this with a list widget (which does not currently exist!)
        self._name = widget.InputWidget()
        layout.add_child(self._name)

        layout.add_padding(points(12.0))

        buttons_layout = widget.HStackedLayoutWidget()
        layout.add_child(buttons_layout)
        buttons_layout.add_padding(0.0, weight = 1.0)

        cancel_button = widget.TextButtonWidget()
        buttons_layout.add_child(cancel_button)
        cancel_button.text = "Cancel"
        cancel_button.action_func = self._cancel

        buttons_layout.add_padding(points(4.0))

        load_button = widget.TextButtonWidget()
        buttons_layout.add_child(load_button)
        load_button.text = "Load"
        load_button.action_func = self._load

        self._destroy_func = modal_dialog.show_modal_dialog(stack_widget, layout)

    def _cancel(self):
        self._destroy_func()

    def _load(self):
        name = self._name.text

        if self._on_project_selected_func(name):
            self._destroy_func()
