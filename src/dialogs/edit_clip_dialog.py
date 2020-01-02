import constants
import drawing
import modal_dialog
from units import *
import widget

class EditClipDialog:
    # on_accept_func takes name, $TODO as arguments
    def __init__(self, stack_widget, clip, on_accept_func, on_delete_func):
        self._stack_widget = stack_widget
        self._on_accept_func = on_accept_func
        self._on_delete_func = on_delete_func

        layout = widget.VStackedLayoutWidget()

        title = widget.TextWidget()
        if clip is None:
            title.text = "Record clip"
        else:
            title.text = "Edit clip"
        title.size.value = points(20.0)
        title.horizontal_alignment = drawing.HorizontalAlignment.CENTER
        title.vertical_alignment = drawing.VerticalAlignment.MIDDLE
        layout.add_child(title)

        layout.add_padding(points(12.0))

        name_layout = widget.HStackedLayoutWidget()
        layout.add_child(name_layout, horizontal_placement = widget.HorizontalPlacement.CENTER)

        name_title = widget.TextWidget()
        name_layout.add_child(name_title, horizontal_placement = widget.HorizontalPlacement.RIGHT)
        name_title.text = "Name:"
        name_title.horizontal_alignment = drawing.HorizontalAlignment.RIGHT
        name_title.vertical_alignment = drawing.VerticalAlignment.MIDDLE

        name_layout.add_padding(points(12.0))

        self._name = widget.InputWidget()
        name_layout.add_child(self._name)
        if clip is not None:
            self._name.text = clip.name

        layout.add_padding(points(12.0))

        waveform_viewer = widget.RectangleWidget()
        layout.add_child(waveform_viewer)
        waveform_viewer.desired_width = inches(8.0)
        waveform_viewer.desired_height = inches(2.0)
        waveform_viewer.border_thickness.value = points(1.0)
        waveform_viewer.border_color.value = constants.Color.BLACK

        layout.add_padding(points(12.0))

        buttons_layout = widget.HStackedLayoutWidget()
        layout.add_child(buttons_layout)

        record_button = widget.IconButtonWidget()
        buttons_layout.add_child(record_button)
        record_button.icon_name = "metronome" # $TODO
        record_button.action_func = self._record

        buttons_layout.add_padding(points(4.0))

        play_pause_button = widget.IconButtonWidget()
        buttons_layout.add_child(play_pause_button)
        play_pause_button.icon_name = "metronome" # $TODO
        play_pause_button.action_func = self._play_pause

        buttons_layout.add_padding(points(4.0))

        stop_button = widget.IconButtonWidget()
        buttons_layout.add_child(stop_button)
        stop_button.icon_name = "metronome" # $TODO
        stop_button.action_func = self._stop

        buttons_layout.add_padding(points(4.0))

        metronome_button = widget.IconButtonWidget()
        buttons_layout.add_child(metronome_button)
        metronome_button.icon_name = "metronome" # $TODO
        metronome_button.action_func = self._toggle_metronome

        if clip is not None:
            buttons_layout.add_padding(points(4.0))

            delete_button = widget.IconButtonWidget()
            buttons_layout.add_child(delete_button)
            delete_button.icon_name = "metronome" # $TODO
            delete_button.action_func = self._delete

        buttons_layout.add_padding(points(4.0), weight = 1.0)

        accept_button = widget.IconButtonWidget()
        buttons_layout.add_child(accept_button)
        accept_button.icon_name = "metronome" # $TODO
        accept_button.action_func = self._accept

        buttons_layout.add_padding(points(4.0))

        reject_button = widget.IconButtonWidget()
        buttons_layout.add_child(reject_button)
        reject_button.icon_name = "metronome" # $TODO
        reject_button.action_func = self._reject

        self._destroy_func = modal_dialog.show_modal_dialog(stack_widget, layout)

    def _record(self):
        pass

    def _play_pause(self):
        pass

    def _stop(self):
        pass

    def _toggle_metronome(self):
        pass

    def _accept(self):
        name = self._name.text.strip()
        if len(name) == 0:
            modal_dialog.show_simple_modal_dialog(
                self._stack_widget,
                "Invalid name",
                "The clip name cannot be empty.",
                ["OK"],
                None)
            return

        # $TODO
        sample_count = 1000
        start_sample_index = 0
        end_sample_index = 1000
        measure_count = 1

        if sample_count == 0:
            modal_dialog.show_simple_modal_dialog(
                self._stack_widget,
                "Empty clip",
                "No clip data has been recorded.",
                ["OK"],
                None)
            return

        if measure_count == 0:
            modal_dialog.show_simple_modal_dialog(
                self._stack_widget,
                "Clip is too short",
                "The clip must be at least one measure long, not including the intro and outro.",
                ["OK"],
                None)
            return

        self._destroy_func()
        self._on_accept_func(name, sample_count, start_sample_index, end_sample_index, measure_count)

    def _delete(self):
        self._destroy_func()
        self._on_delete_func()

    def _reject(self):
        # $TODO delete any pending recorded clip data

        self._destroy_func()
