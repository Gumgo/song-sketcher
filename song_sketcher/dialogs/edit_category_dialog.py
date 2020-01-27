from song_sketcher import constants
from song_sketcher import drawing
from song_sketcher import modal_dialog
from song_sketcher import parameter
from song_sketcher import project
from song_sketcher.units import *
from song_sketcher import widget
from song_sketcher import widget_event

class EditCategoryDialog:
    # on_accept_func takes name, color, gain as arguments
    def __init__(self, stack_widget, category, on_accept_func, on_delete_func):
        self._stack_widget = stack_widget
        self._on_accept_func = on_accept_func
        self._on_delete_func = on_delete_func

        layout = widget.VStackedLayoutWidget()

        title = widget.TextWidget()
        if category is None:
            title.text = "Create category"
        else:
            title.text = "Edit category"
        title.size.value = points(20.0)
        title.horizontal_alignment = drawing.HorizontalAlignment.CENTER
        title.vertical_alignment = drawing.VerticalAlignment.MIDDLE
        layout.add_child(title)

        layout.add_padding(points(12.0))

        options_layout = widget.GridLayoutWidget()
        layout.add_child(options_layout)

        options_layout.set_column_size(1, points(4.0))

        name_title = widget.TextWidget()
        options_layout.add_child(0, 0, name_title, horizontal_placement = widget.HorizontalPlacement.RIGHT)
        name_title.text = "Name:"
        name_title.horizontal_alignment = drawing.HorizontalAlignment.RIGHT
        name_title.vertical_alignment = drawing.VerticalAlignment.MIDDLE

        name_gain_layout = widget.HStackedLayoutWidget()
        options_layout.add_child(0, 2, name_gain_layout)

        self._name = widget.InputWidget()
        name_gain_layout.add_child(self._name)
        if category is not None:
            self._name.text = category.name

        name_gain_layout.add_padding(points(4.0))

        self._gain_spinner = widget.SpinnerWidget()
        name_gain_layout.add_child(self._gain_spinner)
        self._gain_spinner.min_value = 0.0
        self._gain_spinner.max_value = 1.0
        self._gain_spinner.value = 1.0 if category is None else category.gain
        self._gain_spinner.decimals = 2

        options_layout.set_row_size(1, points(12.0))

        color_title = widget.TextWidget()
        options_layout.add_child(2, 0, color_title, horizontal_placement = widget.HorizontalPlacement.RIGHT)
        color_title.text = "Color:"
        color_title.horizontal_alignment = drawing.HorizontalAlignment.RIGHT
        color_title.vertical_alignment = drawing.VerticalAlignment.MIDDLE

        selected_color = category.color if category is not None else project.CATEGORY_COLORS[0]
        self._color_picker = ColorPickerWidget(4, project.CATEGORY_COLORS, selected_color)
        options_layout.add_child(2, 2, self._color_picker)

        layout.add_padding(points(12.0))

        buttons_layout = widget.HStackedLayoutWidget()
        layout.add_child(buttons_layout)

        if category is not None:
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
                "The category name cannot be empty.",
                ["OK"],
                None)
            return

        self._destroy_func()
        self._on_accept_func(name, self._color_picker.selected_color, self._gain_spinner.value)

    def _delete(self):
        self._destroy_func()
        self._on_delete_func()

    def _reject(self):
        self._destroy_func()

class ColorPickerSquareWidget(widget.WidgetWithSize):
    def __init__(self):
        super().__init__()
        self.color255 = (0, 0, 0)
        self.on_selected_func = None
        self._selected = False
        self._border_color = parameter.AnimatableParameter(constants.Color.BLACK)

    @property
    def selected(self):
        return self._selected

    def set_selected(self, selected, animate):
        if selected != self._selected:
            border_color = constants.Color.WHITE if selected else constants.Color.BLACK
            if animate:
                self._border_color.transition().target(border_color).duration(0.125).ease_out()
            else:
                self._border_color.value = border_color
            self._selected = selected

    def process_event(self, event):
        if (isinstance(event, widget_event.MouseEvent)
            and event.event_type is widget_event.MouseEventType.PRESS
            and event.button is widget_event.MouseButton.LEFT):
            self.set_selected(True, True)
            self.on_selected_func()
        return False

    def get_desired_size(self):
        return (inches(0.5), inches(0.5))

    def draw_visible(self, parent_transform):
        transform = parent_transform * self.get_transform()
        with transform:
            drawing.draw_rectangle(
                0.0,
                0.0,
                self.width.value,
                self.height.value,
                constants.rgba255(*self.color255),
                border_thickness = points(2.0),
                border_color = self._border_color.value)

class ColorPickerWidget(widget.GridLayoutWidget):
    def __init__(self, columns, colors, selected_color):
        super().__init__()
        self.selected_color = selected_color
        padding = points(12.0)
        row = 0
        column = 0
        for color in colors:
            square = ColorPickerSquareWidget()
            square.color255 = color
            square.set_selected(color == selected_color, False)
            square.on_selected_func = lambda color = color: self._on_color_selected(color)
            self.add_child(row * 2, column * 2, square)

            if row != 0:
                self.set_row_size(row * 2 - 1, padding)
            if column != 0:
                self.set_column_size(column * 2 - 1, padding)

            column += 1
            if column == columns:
                column = 0
                row += 1

    def _on_color_selected(self, color):
        self.selected_color = color
        for child in self.get_children():
            child.set_selected(child.color255 == color, True)
