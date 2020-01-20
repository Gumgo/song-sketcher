from song_sketcher import engine
from song_sketcher import drawing
from song_sketcher import modal_dialog
from song_sketcher import settings
from song_sketcher.units import *
from song_sketcher import widget

class SettingsDialog:
    def __init__(self, stack_widget):
        self._stack_widget = stack_widget

        layout = widget.VStackedLayoutWidget()

        title = widget.TextWidget()
        title.text = "Settings"
        title.size.value = points(20.0)
        title.horizontal_alignment = drawing.HorizontalAlignment.CENTER
        title.vertical_alignment = drawing.VerticalAlignment.MIDDLE
        layout.add_child(title)

        layout.add_padding(points(12.0))

        options_layout = widget.GridLayoutWidget()
        layout.add_child(options_layout)

        options_layout.set_column_size(1, points(4.0))

        input_device_title = widget.TextWidget()
        options_layout.add_child(0, 0, input_device_title, horizontal_placement = widget.HorizontalPlacement.RIGHT)
        input_device_title.text = "Input device:"
        input_device_title.horizontal_alignment = drawing.HorizontalAlignment.RIGHT
        input_device_title.vertical_alignment = drawing.VerticalAlignment.MIDDLE

        input_device_count = engine.get_input_device_count()
        self._input_device = widget.DropdownWidget()
        options_layout.add_child(0, 2, self._input_device)
        self._input_device.set_options(
            [(i, engine.get_input_device_name(i)) for i in range(input_device_count)])
        self._input_device.selected_option_index = settings.get().input_device_index

        options_layout.set_row_size(1, points(12.0))

        output_device_title = widget.TextWidget()
        options_layout.add_child(2, 0, output_device_title, horizontal_placement = widget.HorizontalPlacement.RIGHT)
        output_device_title.text = "Output device:"
        output_device_title.horizontal_alignment = drawing.HorizontalAlignment.RIGHT
        output_device_title.vertical_alignment = drawing.VerticalAlignment.MIDDLE

        output_device_count = engine.get_output_device_count()
        self._output_device = widget.DropdownWidget()
        options_layout.add_child(2, 2, self._output_device)
        self._output_device.set_options(
            [(i, engine.get_output_device_name(i)) for i in range(output_device_count)])
        self._output_device.selected_option_index = settings.get().output_device_index

        layout.add_padding(points(12.0))

        buttons_layout = widget.HStackedLayoutWidget()
        layout.add_child(buttons_layout)
        buttons_layout.add_padding(0.0, weight = 1.0)

        cancel_button = widget.TextButtonWidget()
        buttons_layout.add_child(cancel_button)
        cancel_button.text = "Cancel"
        cancel_button.action_func = self._cancel

        buttons_layout.add_padding(points(4.0))

        ok_button = widget.TextButtonWidget()
        buttons_layout.add_child(ok_button)
        ok_button.text = "OK"
        ok_button.action_func = self._accept

        self._destroy_func = modal_dialog.show_modal_dialog(stack_widget, layout)

    def _cancel(self):
        self._destroy_func()

    def _accept(self):
        s = settings.get()
        s.input_device_index = self._input_device.selected_option_index
        s.output_device_index = self._output_device.selected_option_index

        self._destroy_func()
