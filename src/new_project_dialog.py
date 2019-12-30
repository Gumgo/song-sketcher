import drawing
import modal_dialog
from units import *
import widget

_SAMPLE_RATES = [
    (44100, "44.1khz"),
    (48000, "48khz"),
    (96000, "96khz")
]

class NewProjectDialog:
    def __init__(self, stack_widget):
        layout = widget.VStackedLayoutWidget()

        title = widget.TextWidget()
        title.text = "New project"
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

        options_layout.set_row_size(1, points(12.0))

        sample_rate_title = widget.TextWidget()
        options_layout.add_child(2, 0, sample_rate_title, horizontal_placement = widget.HorizontalPlacement.RIGHT)
        sample_rate_title.text = "Sample rate:"
        sample_rate_title.horizontal_alignment = drawing.HorizontalAlignment.RIGHT
        sample_rate_title.vertical_alignment = drawing.VerticalAlignment.MIDDLE

        self._sample_rate = widget.DropdownWidget()
        self._sample_rate.set_options(_SAMPLE_RATES)
        self._sample_rate.selected_option_index = 0
        options_layout.add_child(2, 2, self._sample_rate)

        options_layout.set_row_size(3, points(12.0))

        beats_per_minute_title = widget.TextWidget()
        options_layout.add_child(4, 0, beats_per_minute_title, horizontal_placement = widget.HorizontalPlacement.RIGHT)
        beats_per_minute_title.text = "Beats per minute:"
        beats_per_minute_title.horizontal_alignment = drawing.HorizontalAlignment.RIGHT
        beats_per_minute_title.vertical_alignment = drawing.VerticalAlignment.MIDDLE

        self._beats_per_minute = widget.SpinnerWidget()
        self._beats_per_minute.min_value = 40.0
        self._beats_per_minute.max_value = 160.0
        self._beats_per_minute.value = 60.0
        self._beats_per_minute.decimals = 1
        options_layout.add_child(4, 2, self._beats_per_minute)

        options_layout.set_row_size(5, points(12.0))

        beats_per_measure_title = widget.TextWidget()
        options_layout.add_child(6, 0, beats_per_measure_title, horizontal_placement = widget.HorizontalPlacement.RIGHT)
        beats_per_measure_title.text = "Beats per measure:"
        beats_per_measure_title.horizontal_alignment = drawing.HorizontalAlignment.RIGHT
        beats_per_measure_title.vertical_alignment = drawing.VerticalAlignment.MIDDLE

        self._beats_per_measure = widget.SpinnerWidget()
        self._beats_per_measure.min_value = 2.0
        self._beats_per_measure.max_value = 8.0
        self._beats_per_measure.value = 4.0
        self._beats_per_measure.decimals = 0
        options_layout.add_child(6, 2, self._beats_per_measure)

        layout.add_padding(points(12.0))

        buttons_layout = widget.HStackedLayoutWidget()
        layout.add_child(buttons_layout)
        buttons_layout.add_padding(0.0, weight = 1.0)

        cancel_button = widget.TextButtonWidget()
        buttons_layout.add_child(cancel_button)
        cancel_button.text = "Cancel"
        cancel_button.action_func = self._cancel

        buttons_layout.add_padding(points(4.0))

        create_button = widget.TextButtonWidget()
        buttons_layout.add_child(create_button)
        create_button.text = "Create"
        create_button.action_func = self._create

        self._destroy_func = modal_dialog.show_modal_dialog(stack_widget, layout)

    def _cancel(self):
        self._destroy_func()

    def _create(self):
        self._destroy_func()
        # $TODO
