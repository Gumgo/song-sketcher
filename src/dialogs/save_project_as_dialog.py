import drawing
import modal_dialog
import project_manager
from units import *
import widget

class SaveProjectAsDialog:
    def __init__(self, stack_widget, on_name_chosen_func):
        self._stack_widget = stack_widget
        self._on_name_chosen_func = on_name_chosen_func

        layout = widget.VStackedLayoutWidget()

        title = widget.TextWidget()
        title.text = "Save project as"
        title.size.value = points(20.0)
        title.horizontal_alignment = drawing.HorizontalAlignment.CENTER
        title.vertical_alignment = drawing.VerticalAlignment.MIDDLE
        layout.add_child(title)

        layout.add_padding(points(12.0))

        options_layout = widget.HStackedLayoutWidget()
        layout.add_child(options_layout)

        name_title = widget.TextWidget()
        options_layout.add_child(name_title, horizontal_placement = widget.HorizontalPlacement.RIGHT)
        name_title.text = "Name:"
        name_title.horizontal_alignment = drawing.HorizontalAlignment.RIGHT
        name_title.vertical_alignment = drawing.VerticalAlignment.MIDDLE

        options_layout.add_padding(points(12.0))

        self._name = widget.InputWidget()
        options_layout.add_child(self._name)

        layout.add_padding(points(12.0))

        buttons_layout = widget.HStackedLayoutWidget()
        layout.add_child(buttons_layout)
        buttons_layout.add_padding(0.0, weight = 1.0)

        cancel_button = widget.TextButtonWidget()
        buttons_layout.add_child(cancel_button)
        cancel_button.text = "Cancel"
        cancel_button.action_func = self._cancel

        buttons_layout.add_padding(points(4.0))

        save_button = widget.TextButtonWidget()
        buttons_layout.add_child(save_button)
        save_button.text = "Save"
        save_button.action_func = self._save

        self._destroy_func = modal_dialog.show_modal_dialog(stack_widget, layout)

    def _cancel(self):
        self._destroy_func()

    def _save(self):
        pm = project_manager.get()

        name = pm.fixup_project_name(self._name.text)
        if not pm.is_valid_project_name(name):
            modal_dialog.show_simple_modal_dialog(
                self._stack_widget,
                "Invalid project name",
                "Project names can only contain letters, numbers, spaces, and underscores.",
                ["OK"],
                None)
            return

        if pm.project_exists(name):
            modal_dialog.show_simple_modal_dialog(
                self._stack_widget,
                "Project already exists",
                "A project with the name '{}' already exists, please choose another name.".format(name),
                ["OK"],
                None)
            return

        try:
            pm.create_project(name)
        except:
            modal_dialog.show_simple_modal_dialog(
                self._stack_widget,
                "Failed to create project",
                "An error was encountered trying to create the project '{}'.".format(name),
                ["OK"],
                None)
            return

        self._destroy_func()
        self._on_name_chosen_func(name)
