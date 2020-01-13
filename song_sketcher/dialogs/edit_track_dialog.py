from song_sketcher import constants
from song_sketcher import drawing
from song_sketcher import modal_dialog
from song_sketcher.units import *
from song_sketcher import widget

class EditTrackDialog:
    # on_accept_func takes name as argument
    def __init__(self, stack_widget, track, on_accept_func, on_delete_func):
        self._stack_widget = stack_widget
        self._on_accept_func = on_accept_func
        self._on_delete_func = on_delete_func

        layout = widget.VStackedLayoutWidget()

        title = widget.TextWidget()
        if track is None:
            title.text = "Create track"
        else:
            title.text = "Edit track"
        title.size.value = points(20.0)
        title.horizontal_alignment = drawing.HorizontalAlignment.CENTER
        title.vertical_alignment = drawing.VerticalAlignment.MIDDLE
        layout.add_child(title)

        layout.add_padding(points(12.0))

        options_layout = widget.GridLayoutWidget()
        layout.add_child(options_layout)

        options_layout.set_column_size(1, points(12.0))

        name_title = widget.TextWidget()
        options_layout.add_child(0, 0, name_title, horizontal_placement = widget.HorizontalPlacement.RIGHT)
        name_title.text = "Name:"
        name_title.horizontal_alignment = drawing.HorizontalAlignment.RIGHT
        name_title.vertical_alignment = drawing.VerticalAlignment.MIDDLE

        self._name = widget.InputWidget()
        options_layout.add_child(0, 2, self._name)
        if track is not None:
            self._name.text = track.name

        layout.add_padding(points(12.0))

        buttons_layout = widget.HStackedLayoutWidget()
        layout.add_child(buttons_layout)

        if track is not None:
            delete_button = widget.IconButtonWidget()
            buttons_layout.add_child(delete_button)
            delete_button.icon_name = "delete"
            delete_button.action_func = self._delete

        buttons_layout.add_padding(points(4.0), weight = 1.0)

        accept_button = widget.IconButtonWidget()
        buttons_layout.add_child(accept_button)
        accept_button.color = constants.Ui.ACCEPT_BUTTON_COLOR
        accept_button.icon_name = "accept"
        accept_button.action_func = self._accept

        buttons_layout.add_padding(points(4.0))

        reject_button = widget.IconButtonWidget()
        buttons_layout.add_child(reject_button)
        reject_button.color = constants.Ui.REJECT_BUTTON_COLOR
        reject_button.icon_name = "reject"
        reject_button.action_func = self._reject

        self._destroy_func = modal_dialog.show_modal_dialog(stack_widget, layout)

    def _accept(self):
        name = self._name.text.strip()
        if len(name) == 0:
            modal_dialog.show_simple_modal_dialog(
                self._stack_widget,
                "Invalid name",
                "The track name cannot be empty.",
                ["OK"],
                None)
            return

        self._destroy_func()
        self._on_accept_func(name)

    def _delete(self):
        self._destroy_func()
        self._on_delete_func()

    def _reject(self):
        self._destroy_func()
