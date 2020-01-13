from enum import Enum
import math

import constants
import drawing
import layout
import parameter
import timer
import transform
from units import *
import widget_event
import widget_manager

class HorizontalPlacement(Enum):
    FILL = 0
    LEFT = 1
    CENTER = 2
    RIGHT = 3

class VerticalPlacement(Enum):
    FILL = 0
    TOP = 1
    MIDDLE = 2
    BOTTOM = 3

class Widget:
    def __init__(self):
        self._visible = True
        self._parent = None

        self.x = parameter.AnimatableParameter(0.0)
        self.y = parameter.AnimatableParameter(0.0)
        self.x.add_change_listener(lambda x: self.invalidate_placement())
        self.y.add_change_listener(lambda x: self.invalidate_placement())

    @property
    def parent(self):
        return self._parent

    @parent.setter
    def parent(self, parent):
        self._parent = parent

    def destroy(self):
        widget_manager.get().destroy_widget(self)

    def invalidate_placement(self):
        widget_manager.get().invalidate_widget_placements()

    @property
    def is_captured(self):
        return widget_manager.get().captured_widget is self

    def capture(self):
        widget_manager.get().capture_widget(self)

    def release_capture(self):
        widget_manager.get().release_captured_widget(self)

    @property
    def is_focused(self):
        return widget_manager.get().focused_widget is self

    def focus(self):
        widget_manager.get().focus_widget(self)

    def release_focus(self):
        widget_manager.get().release_focused_widget(self)

    @property
    def is_under_mouse(self):
        return widget_manager.get().widget_under_mouse is self

    def get_transform(self):
        return transform.Transform(self.x.value, self.y.value)

    def get_full_transform(self):
        transform = self.get_transform()
        if self.parent is not None:
            transform = self.parent.get_full_transform() * transform
        return transform

    def add_overlay(self, draw_func):
        widget_manager.get().add_overlay(draw_func)

    def draw(self, parent_transform):
        if self._visible:
            self.draw_visible(parent_transform)

    # Can be overridden
    def layout_widget(self, layout_position, layout_size, horizontal_placement, vertical_placement):
        self.x.value = {
            HorizontalPlacement.FILL: layout_position[0] + layout_size[0] * 0.5,
            HorizontalPlacement.LEFT: layout_position[0],
            HorizontalPlacement.CENTER: layout_position[0] + layout_size[0] * 0.5,
            HorizontalPlacement.RIGHT: layout_position[0] + layout_size[0]
        }[horizontal_placement]

        self.y.value = {
            VerticalPlacement.FILL: layout_position[1] + layout_size[1] * 0.5,
            VerticalPlacement.TOP: layout_position[1] + layout_size[1],
            VerticalPlacement.MIDDLE: layout_position[1] + layout_size[1] * 0.5,
            VerticalPlacement.BOTTOM: layout_position[1]
        }[vertical_placement]

    # Can be overridden
    def get_widget_for_point(self, parent_transform, x, y):
        return None

    # Returns whether the event was consumed
    def process_event(self, event):
        raise NotImplementedError()

    def get_desired_size(self):
        raise NotImplementedError()

    def draw_visible(self, parent_transform):
        raise NotImplementedError()

class WidgetWithSize(Widget):
    def __init__(self):
        super().__init__()
        self.width = parameter.AnimatableParameter(0.0)
        self.height = parameter.AnimatableParameter(0.0)
        self.width.add_change_listener(lambda x: self.invalidate_placement())
        self.width.add_change_listener(lambda x: self.invalidate_placement())

    def layout_widget(self, layout_position, layout_size, horizontal_placement, vertical_placement):
        desired_size = self.get_desired_size()

        self.x.value = {
            HorizontalPlacement.FILL: layout_position[0],
            HorizontalPlacement.LEFT: layout_position[0],
            HorizontalPlacement.CENTER: layout_position[0] + (layout_size[0] - desired_size[0]) * 0.5,
            HorizontalPlacement.RIGHT: layout_position[0] + layout_size[0] - desired_size[0]
        }[horizontal_placement]

        self.y.value = {
            VerticalPlacement.FILL: layout_position[1],
            VerticalPlacement.TOP: layout_position[1] + layout_size[1] - desired_size[1],
            VerticalPlacement.MIDDLE: layout_position[1] + (layout_size[1] - desired_size[1]) * 0.5,
            VerticalPlacement.BOTTOM: layout_position[1]
        }[vertical_placement]

        self.width.value = layout_size[0] if horizontal_placement is HorizontalPlacement.FILL else desired_size[0]
        self.height.value = layout_size[1] if vertical_placement is VerticalPlacement.FILL else desired_size[1]

    def get_widget_for_point(self, parent_transform, x, y):
        transform = parent_transform * self.get_transform()
        x, y = transform.inverse().transform_point((x, y))
        if x >= 0.0 and y >= 0.0 and x < self.width.value and y < self.height.value:
            return self
        return None

class ContainerWidget(WidgetWithSize):
    def __init__(self):
        super().__init__()

    def get_children(self):
        raise NotImplementedError()

    def destroy(self):
        super().destroy()
        for child in self.get_children():
            child.destroy()

    def process_event(self, event):
        return False

    def layout_children(self):
        raise NotImplementedError()

    def layout_widget(self, layout_position, layout_size, horizontal_placement, vertical_placement):
        super().layout_widget(layout_position, layout_size, horizontal_placement, vertical_placement)
        self.layout_children()

    def get_widget_for_point(self, parent_transform, x, y):
        widget = super().get_widget_for_point(parent_transform, x, y)
        if widget is None:
            return None

        transform = parent_transform * self.get_transform()
        for child in reversed([x for x in self.get_children()]): # Iterate in reverse to respect drawing order
            child_widget = child.get_widget_for_point(transform, x, y)
            if child_widget is not None:
                return child_widget

        return widget

    def draw_visible(self, parent_transform):
        transform  = parent_transform * self.get_transform()
        for child in self.get_children():
            child.draw(transform)

class StackWidget(ContainerWidget):
    def __init__(self):
        super().__init__()
        self._children = []

    def get_children(self):
        return (x for x in self._children)

    def push_child(self, child):
        child.parent = self
        self._children.append(child)

    def add_child(self, child, index):
        child.parent = self
        self._children.insert(index, child)

    def pop_child(self):
        self._children.pop().parent = None

    def remove_child(self, child):
        child.parent = None
        self._children.remove(child)

    def layout_widget(self, layout_position, layout_size, horizontal_placement, vertical_placement):
        assert False # This widget should only be used at root level

    def get_desired_size(self):
        assert False

    def get_widget_for_point(self, parent_transform, x, y):
        if len(self._children) == 0:
            return None

        # Only the top of the stack responds to events
        transform = parent_transform * self.get_transform()
        return self._children[-1].get_widget_for_point(transform, x, y)

    def draw_visible(self, parent_transform):
        transform  = parent_transform * self.get_transform()
        for child in self.get_children():
            child.draw(transform)

class AbsoluteLayoutWidget(ContainerWidget):
    def __init__(self):
        super().__init__()
        self.desired_width = 0.0
        self.desired_height = 0.0
        self._children = []

    def get_children(self):
        return (x for x in self._children)

    def add_child(self, child, index = None):
        if index is None:
            index = len(self._children)
        child.parent = self
        self._children.insert(index, child)

    def remove_child(self, child):
        child.parent = None
        self._children.remove(child)

    def remove_child_at_index(self, index):
        self._children.pop(index).parent = None

    def clear_children(self):
        for child in self._children:
            child.parent = None
        self._children.clear()

    def layout_children(self):
        for child in self.get_children():
            child.layout_widget(
                (child.x.value, child.y.value),
                child.get_desired_size(),
                HorizontalPlacement.LEFT,
                VerticalPlacement.BOTTOM)

    def get_desired_size(self):
        return (self.desired_width, self.desired_height)

class StackedLayoutWidget(ContainerWidget):
    class _Child:
        def __init__(self):
            self.widget = None
            self.padding = None
            self.weight = 0.0
            self.horizontal_placement = None
            self.vertical_placement = None

    def __init__(self, direction):
        super().__init__()
        self.desired_width = None
        self.desired_height = None
        self.margin = None
        self._children = []
        self._direction = direction

    def get_children(self):
        return (x.widget for x in self._children if x.widget is not None)

    def add_child(self, child, weight = 0.0, horizontal_placement = HorizontalPlacement.FILL, vertical_placement = VerticalPlacement.FILL):
        entry = self._Child()
        entry.widget = child
        entry.weight = weight
        entry.horizontal_placement = horizontal_placement
        entry.vertical_placement = vertical_placement
        child.parent = self
        self._children.append(entry)

    def add_padding(self, padding, weight = 0.0):
        entry = self._Child()
        entry.padding = padding
        entry.weight = weight
        self._children.append(entry)

    # Clear and rebuild children if they need to be modified
    # Note that destroy() must explicitly be called on children
    def clear_children(self):
        for child in self._children:
            child.parent = None
        self._children.clear()

    def get_desired_size(self):
        stacked_layout = self._build_stacked_layout()
        desired_size = stacked_layout.compute_desired_size()
        return (
            desired_size[0] if self.desired_width is None else self.desired_width,
            desired_size[1] if self.desired_height is None else self.desired_height)

    def layout_children(self):
        stacked_layout = self._build_stacked_layout()
        layout_rect = layout.LayoutRect((0.0, 0.0), (self.width.value, self.height.value))
        stacked_layout.compute_layout(layout_rect)

    def _build_stacked_layout(self):
        stacked_layout = layout.StackedLayout(self._direction, self.margin)
        for entry in self._children:
            if entry.widget is not None:
                def layout_child(rect, entry = entry):
                    entry.widget.layout_widget(
                        rect.position,
                        rect.size,
                        entry.horizontal_placement,
                        entry.vertical_placement)
                stacked_layout.add_entry(entry.widget.get_desired_size, entry.weight, layout_child)
            else:
                stacked_layout.add_padding(entry.padding, entry.weight)
        return stacked_layout

class HStackedLayoutWidget(StackedLayoutWidget):
    def __init__(self):
        super().__init__(layout.Direction.HORIZONTAL)

class VStackedLayoutWidget(StackedLayoutWidget):
    def __init__(self):
        super().__init__(layout.Direction.VERTICAL)

class GridLayoutWidget(ContainerWidget):
    class _Child:
        def __init__(self):
            self.widget = None
            self.row = None
            self.column = None
            self.horizontal_placement = None
            self.vertical_placement = None

    def __init__(self):
        super().__init__()
        self.desired_width = None
        self.desired_height = None
        self.margin = None
        self._children = []
        self._row_sizes = {}
        self._column_sizes = {}
        self._row_weights = {}
        self._column_weights = {}

    def get_children(self):
        return (x.widget for x in self._children)

    def add_child(self, row, column, child, horizontal_placement = HorizontalPlacement.FILL, vertical_placement = VerticalPlacement.FILL):
        entry = self._Child()
        entry.row = row
        entry.column = column
        entry.widget = child
        entry.horizontal_placement = horizontal_placement
        entry.vertical_placement = vertical_placement
        child.parent = self
        self._children.append(entry)

    def set_row_size(self, row, size):
        self._row_sizes[row] = size

    def set_column_size(self, column, size):
        self._column_sizes[column] = size

    def set_row_weight(self, row, weight):
        self._row_weights[row] = weight

    def set_column_weight(self, column, weight):
        self._column_weights[column] = weight

    # Clear and rebuild children if they need to be modified
    # Note that destroy() must explicitly be called on children
    def clear_children(self):
        for child in self._children:
            child.parent = None
        self._children.clear()
        self._row_sizes.clear()
        self._column_sizes.clear()
        self._row_weights.clear()
        self._column_weights.clear()

    def get_desired_size(self):
        grid_layout = self._build_grid_layout()
        desired_size = grid_layout.compute_desired_size()
        return (
            desired_size[0] if self.desired_width is None else self.desired_width,
            desired_size[1] if self.desired_height is None else self.desired_height)

    def layout_children(self):
        grid_layout = self._build_grid_layout()
        layout_rect = layout.LayoutRect((0.0, 0.0), (self.width.value, self.height.value))
        grid_layout.compute_layout(layout_rect)

    def _build_grid_layout(self):
        grid_layout = layout.GridLayout(self.margin)
        for entry in self._children:
            def layout_child(rect, entry = entry):
                entry.widget.layout_widget(
                    rect.position,
                    rect.size,
                    entry.horizontal_placement,
                    entry.vertical_placement)
            grid_layout.add_entry(entry.row, entry.column, entry.widget.get_desired_size, layout_child)
        for i, size in self._row_sizes.items():
            grid_layout.set_row_size(i, size)
        for i, size in self._column_sizes.items():
            grid_layout.set_column_size(i, size)
        for i, weight in self._row_weights.items():
            grid_layout.set_row_weight(i, weight)
        for i, weight in self._column_weights.items():
            grid_layout.set_column_weight(i, weight)
        return grid_layout

class ScrollAreaWidget(ContainerWidget):
    def __init__(self):
        super().__init__()
        self.desired_width = 0.0
        self.desired_height = 0.0
        self.width.add_change_listener(lambda x: self._update_scroll_area())
        self.height.add_change_listener(lambda x: self._update_scroll_area())

        # If we don't have a scrollbar in certain directions, this is how the child placement will behave
        self.child_nonscrolling_horizontal_placement = HorizontalPlacement.FILL
        self.child_nonscrolling_vertical_placement = VerticalPlacement.FILL

        self._child = None
        self._horizontal_scrollbar = None
        self._vertical_scrollbar = None
        self._previous_height = 0.0
        self._previous_child_height = 0.0

    def destroy(self):
        self.horizontal_scrollbar = None
        self.vertical_scrollbar = None
        super().destroy()

    @property
    def horizontal_scrollbar(self):
        return self._horizontal_scrollbar

    @horizontal_scrollbar.setter
    def horizontal_scrollbar(self, horizontal_scrollbar):
        if self._horizontal_scrollbar is not None:
            self._horizontal_scrollbar.on_scroll_func = None
        self._horizontal_scrollbar = horizontal_scrollbar
        if self._horizontal_scrollbar is not None:
            self._update_scrollbar(self._horizontal_scrollbar)
            self._horizontal_scrollbar.on_scroll_func = self._on_scroll_horizontal

    @property
    def vertical_scrollbar(self):
        return self._vertical_scrollbar

    @vertical_scrollbar.setter
    def vertical_scrollbar(self, vertical_scrollbar):
        if self._vertical_scrollbar is not None:
            self._vertical_scrollbar.on_scroll_func = None
        self._vertical_scrollbar = vertical_scrollbar
        if self._vertical_scrollbar is not None:
            self._update_scrollbar(self._vertical_scrollbar)
            self._vertical_scrollbar.on_scroll_func = self._on_scroll_vertical

    def get_children(self):
        if self._child is not None:
            yield self._child

    def set_child(self, child):
        if self._child is not None:
            self._child.parent = None
            self._child.width.remove_change_listener(self._child_size_changed)
            self._child.height.remove_change_listener(self._child_size_changed)
        self._child = child
        if self._child is not None:
            self._child.parent = self
            self._child.width.add_change_listener(self._child_size_changed)
            self._child.height.add_change_listener(self._child_size_changed)

        self._child.x.value = 0.0
        self._child.y.value = self.height.value - self._child.height.value
        self._update_scroll_area()

    def process_event(self, event):
        return False # $TODO middle-click scrolling perhaps?

    def get_desired_size(self):
        return (self.desired_width, self.desired_height)

    def layout_children(self):
        for child in self.get_children():
            child_desired_size = child.get_desired_size()

            if self._horizontal_scrollbar is None:
                child_x = 0.0
                child_width = self.width.value
                horizontal_placement = self.child_nonscrolling_horizontal_placement
            else:
                child_x = child.x.value
                child_width = child_desired_size[0]
                horizontal_placement = HorizontalPlacement.LEFT

            if self._vertical_scrollbar is None:
                child_y = 0.0
                child_height = self.height.value
                vertical_placement = self.child_nonscrolling_vertical_placement
            else:
                child_y = child.y.value
                child_height = child_desired_size[1]
                vertical_placement = VerticalPlacement.BOTTOM

            child.layout_widget(
                (child_x, child_y),
                (child_width, child_height),
                horizontal_placement,
                vertical_placement)

        self._update_scroll_area()

    def draw_visible(self, parent_transform):
        transform = parent_transform * self.get_transform()
        with drawing.scissor(0.0, 0.0, self.width.value, self.height.value, transform = transform):
            super().draw_visible(parent_transform)

    def _child_size_changed(self, size_unused):
        self._update_scroll_area()

    def _update_scroll_area(self):
        height_difference = self.height.value - self._previous_height
        self._previous_height = self.height.value
        if self._child is None:
            self._previous_child_height = 0.0
            return

        child_height_difference = self._child.height.value - self._previous_child_height
        self._previous_child_height = self._child.height.value

        if self._horizontal_scrollbar is not None:
            visible_width = self.width.value
            scrollable_width = self._child.width.value
            child_min_x = min(visible_width - scrollable_width, 0.0)
            child_x = max(self._child.x.value, child_min_x)

            self._child.x.value = child_x
            self._update_scrollbar(self._horizontal_scrollbar)

        if self._vertical_scrollbar is not None:
            # Stick the child to the top when we resize
            self._child.y.value += height_difference - child_height_difference

            visible_height = self.height.value
            scrollable_height = self._child.height.value
            child_min_y = min(visible_height - scrollable_height, 0.0)

            # Prefer scrolling to the top for y
            child_y = self.height.value - (self._child.y.value + self._child.height.value)
            child_y = max(child_y, child_min_y)
            child_y = self.height.value - (child_y + self._child.height.value)

            self._child.y.value = child_y
            self._update_scrollbar(self._vertical_scrollbar)

    def _update_scrollbar(self, scrollbar):
        if self._child is None:
            visible_ratio = 1.0
            position = 0.0
        else:
            if scrollbar.orientation is ScrollbarOrientation.HORIZONTAL:
                visible_size = self.width.value
                scrollable_size = self._child.width.value
                child_position = self._child.x.value
            else:
                assert scrollbar.orientation is ScrollbarOrientation.VERTICAL
                visible_size = self.height.value
                scrollable_size = self._child.height.value
                child_position = self.height.value - (self._child.y.value + self._child.height.value)
            child_min_position = min(visible_size - scrollable_size, 0.0)
            visible_ratio = 1.0 if scrollable_size == 0.0 else min(visible_size / scrollable_size, 1.0)
            position = 0.0 if child_min_position == 0.0 else child_position / child_min_position
            if scrollbar.orientation is ScrollbarOrientation.VERTICAL:
                position = 1.0 - position
        scrollbar.set_properties(visible_ratio, position)

    def _on_scroll_horizontal(self):
        if self._child is None:
            return

        position = self._horizontal_scrollbar.position
        visible_size = self.width.value
        scrollable_size = self._child.width.value
        child_min_position = min(visible_size - scrollable_size, 0.0)
        self._child.x.value = child_min_position * position

    def _on_scroll_vertical(self):
        if self._child is None:
            return

        position = self._vertical_scrollbar.position
        visible_size = self.height.value
        scrollable_size = self._child.height.value
        child_min_position = min(visible_size - scrollable_size, 0.0)

        # Prefer scrolling to the top for y
        child_y = child_min_position * (1.0 - position)
        self._child.y.value = self.height.value - (child_y + self._child.height.value)

class ScrollbarOrientation(Enum):
    HORIZONTAL = 0
    VERTICAL = 1

class ScrollbarWidget(WidgetWithSize):
    class _State(Enum):
        DEFAULT = 0
        HOVER = 1
        PRESSED = 2

    _COLOR_OUTER = (0.25, 0.25, 0.25, 1.0)
    _COLOR_INNER = (0.625, 0.625, 0.625, 1.0)

    def __init__(self, orientation):
        super().__init__()
        self.desired_width = points(20.0) if orientation is ScrollbarOrientation.VERTICAL else 0.0
        self.desired_height = points(20.0) if orientation is ScrollbarOrientation.HORIZONTAL else 0.0
        self.on_scroll_func = None
        self._orientation = orientation
        self._pressed_xyp = None # x, y, position at time of press
        self._state = self._State.DEFAULT
        self._color_inner = parameter.AnimatableParameter(self._COLOR_INNER)
        self._padding_inner = points(2.0)
        self._visible_ratio = 1.0
        self._position = 0.0 # From 0 to 1

    @property
    def orientation(self):
        return self._orientation

    @property
    def position(self):
        return self._position

    def set_properties(self, visible_ratio, position):
        self._visible_ratio = visible_ratio
        self._position = position

    def process_event(self, event):
        result = False
        hover = False
        if isinstance(event, widget_event.MouseEvent):
            x, y = self.get_full_transform().inverse().transform_point((event.x, event.y))
            outer_size = self._outer_size()
            inner_size = self._inner_size()
            inner_outer_space = outer_size - inner_size
            inner_offset = inner_outer_space * self._position
            if self._orientation is ScrollbarOrientation.HORIZONTAL:
                hover = x >= inner_offset and x < inner_offset + inner_size and y >= 0.0 and y < outer_size
            else:
                assert self._orientation is ScrollbarOrientation.VERTICAL
                hover = y >= inner_offset and y < inner_offset + inner_size and x >= 0.0 and x < outer_size

            if event.button is widget_event.MouseButton.LEFT:
                if event.event_type is widget_event.MouseEventType.PRESS:
                    if hover:
                        self._pressed_xyp = (x, y, self._position)
                        self.capture()
                        self.focus()
                    result = True
                elif event.event_type is widget_event.MouseEventType.RELEASE:
                    self.release_capture()
                    self._pressed_xyp = None
                    result = True
            elif event.event_type is widget_event.MouseEventType.MOVE:
                if self._pressed_xyp is not None:
                    p_x, p_y, p_pos = self._pressed_xyp
                    delta = x - p_x if self._orientation is ScrollbarOrientation.HORIZONTAL else y - p_y
                    position_delta = 0.0 if inner_outer_space == 0.0 else delta / inner_outer_space
                    self._position = min(max(p_pos + position_delta, 0.0), 1.0)
                    if self.on_scroll_func is not None:
                        self.on_scroll_func()
                result = True
        elif isinstance(event, widget_event.MouseLeaveEvent):
            result = True # Handle mouse leave to leave the hover state

        if result:
            self._update_color_state(hover)
        return result

    def get_desired_size(self):
        return (self.desired_width, self.desired_height)

    def draw_visible(self, parent_transform):
        transform = parent_transform * self.get_transform()
        with transform:
            outer_thickness = self._thickness()
            outer_radius = outer_thickness * 0.5
            drawing.draw_rectangle(
                0.0,
                0.0,
                self.width.value,
                self.height.value,
                self._COLOR_OUTER,
                radius = outer_radius)

            inner_radius = outer_radius - self._padding_inner
            outer_size = self._outer_size()
            inner_size = self._inner_size()
            inner_offset = (outer_size - inner_size) * self._position

            if self._orientation is ScrollbarOrientation.HORIZONTAL:
                drawing.draw_rectangle(
                    self._padding_inner + inner_offset,
                    self._padding_inner,
                    inner_offset + inner_size - self._padding_inner,
                    outer_thickness - self._padding_inner,
                    self._color_inner.value,
                    radius = inner_radius)
            else:
                assert self._orientation is ScrollbarOrientation.VERTICAL
                drawing.draw_rectangle(
                    self._padding_inner,
                    self._padding_inner + inner_offset,
                    outer_thickness - self._padding_inner,
                    inner_offset + inner_size - self._padding_inner,
                    self._color_inner.value,
                    radius = inner_radius)

    def _thickness(self):
        return self.width.value if self._orientation is ScrollbarOrientation.VERTICAL else self.height.value

    def _outer_size(self):
        return self.width.value if self._orientation is ScrollbarOrientation.HORIZONTAL else self.height.value

    def _inner_size(self):
        return max(self._outer_size() * self._visible_ratio, self._thickness())

    def _update_color_state(self, hover):
        if self._pressed_xyp is not None:
            new_state = self._State.PRESSED
        else:
            new_state = self._State.HOVER if hover else self._State.DEFAULT

        if new_state is not self._state:
            self._state = new_state
            color = {
                self._State.DEFAULT: self._COLOR_INNER,
                self._State.HOVER: drawing.lighten_color(self._COLOR_INNER, 0.5),
                self._State.PRESSED: drawing.darken_color(self._COLOR_INNER, 0.5)
            }[self._state]
            self._color_inner.transition().target(color).duration(0.125).ease_out()

class HScrollbarWidget(ScrollbarWidget):
    def __init__(self):
        super().__init__(ScrollbarOrientation.HORIZONTAL)

class VScrollbarWidget(ScrollbarWidget):
    def __init__(self):
        super().__init__(ScrollbarOrientation.VERTICAL)

# Make this widget a parent of a layout to give the layout a background
class BackgroundWidget(ContainerWidget):
    def __init__(self):
        super().__init__()
        self._child = None
        self.color = parameter.AnimatableParameter(constants.Color.WHITE)
        self.border_thickness = parameter.AnimatableParameter(0.0)
        self.border_color = parameter.AnimatableParameter(constants.Color.BLACK)
        self.radius = parameter.AnimatableParameter(0.0)
        self.left_open = False
        self.right_open = False
        self.top_open = False
        self.bottom_open = False

    def get_children(self):
        if self._child is not None:
            yield self._child

    def set_child(self, child):
        if self._child is not None:
            self._child.parent = None
        self._child = child
        if self._child is not None:
            self._child.parent = self

    def process_event(self, event):
        return False

    def get_desired_size(self):
        return (0.0, 0.0) if self._child is None else self._child.get_desired_size()

    def layout_widget(self, layout_position, layout_size, horizontal_placement, vertical_placement):
        if self._child is None:
            return

        self._child.layout_widget(layout_position, layout_size, horizontal_placement, vertical_placement)
        self.x.value = self._child.x.value
        self.y.value = self._child.y.value
        self._child.x.value = 0.0
        self._child.y.value = 0.0
        self.width.value = self._child.width.value
        self.height.value = self._child.height.value

    def draw_visible(self, parent_transform):
        transform = parent_transform * self.get_transform()
        with transform:
            drawing.draw_rectangle(
                0.0,
                0.0,
                self.width.value,
                self.height.value,
                self.color.value,
                border_thickness = self.border_thickness.value,
                border_color = self.border_color.value,
                radius = self.radius.value,
                left_open = self.left_open,
                right_open = self.right_open,
                top_open = self.top_open,
                bottom_open = self.bottom_open)

        super().draw_visible(parent_transform)

class RectangleWidget(WidgetWithSize):
    def __init__(self):
        super().__init__()
        self.desired_width = 0.0
        self.desired_height = 0.0
        self.color = parameter.AnimatableParameter((1.0, 1.0, 1.0, 1.0))
        self.border_thickness = parameter.AnimatableParameter(0.0)
        self.border_color = parameter.AnimatableParameter((0.0, 0.0, 0.0, 1.0))
        self.radius = parameter.AnimatableParameter(0.0)
        self.left_open = False
        self.right_open = False
        self.top_open = False
        self.bottom_open = False

    def process_event(self, event):
        return False

    def get_desired_size(self):
        return (self.desired_width, self.desired_height)

    def draw_visible(self, parent_transform):
        transform = parent_transform * self.get_transform()
        with transform:
            drawing.draw_rectangle(
                0.0,
                0.0,
                self.width.value,
                self.height.value,
                self.color.value,
                border_thickness = self.border_thickness.value,
                border_color = self.border_color.value,
                radius = self.radius.value,
                left_open = self.left_open,
                right_open = self.right_open,
                top_open = self.top_open,
                bottom_open = self.bottom_open)

class TextWidget(Widget):
    def __init__(self):
        super().__init__()
        self.text = ""
        self.font_name = "arial"
        self.size = parameter.AnimatableParameter(points(12))
        self.horizontal_alignment = drawing.HorizontalAlignment.LEFT
        self.vertical_alignment = drawing.VerticalAlignment.BASELINE
        self.color = parameter.AnimatableParameter((0.0, 0.0, 0.0, 1.0))

    def process_event(self, event):
        return False

    def get_desired_size(self):
        width, ascent, descent = drawing.measure_text(self.text, self.font_name, self.size.value)
        return (width, ascent - descent)

    def draw_visible(self, parent_transform):
        transform = parent_transform * self.get_transform()
        with transform:
            drawing.draw_text(
                self.text,
                self.font_name,
                self.size.value,
                0.0,
                0.0,
                self.horizontal_alignment,
                self.vertical_alignment,
                self.color.value)

class ButtonWidget(WidgetWithSize):
    class _State(Enum):
        DEFAULT = 0
        HOVER = 1
        PRESSED = 2
        PRESSED_HOVER = 3
        DISABLED = 4

    def __init__(self):
        super().__init__()
        self.desired_width = 0.0
        self.desired_height = 0.0
        self.action_func = None
        self._color_default = None
        self._enabled = True
        self._pressed = False
        self._state = self._State.DEFAULT
        self._color = parameter.AnimatableParameter(constants.Color.WHITE)

    @property
    def color(self):
        return self._color_default

    @color.setter
    def color(self, color):
        self._color_default = color
        self._color.value = color

    @property
    def enabled(self):
        return self._enabled

    def set_enabled(self, enabled, animate = True):
        if enabled != self._enabled:
            self._enabled = enabled
            if not enabled:
                self._pressed = False
                self.release_capture()
                self.release_focus()
            self._update_color_state(animate)

    # Returns whether the event was consumed
    def process_event(self, event):
        result = False
        if isinstance(event, widget_event.MouseEvent) and event.button is widget_event.MouseButton.LEFT:
            if event.event_type is widget_event.MouseEventType.PRESS:
                if self.enabled:
                    self._pressed = True
                    self.capture()
                    self.focus()
                result = True
            elif event.event_type is widget_event.MouseEventType.RELEASE:
                self.release_capture()
                if self._pressed:
                    self._pressed = False
                    if self.is_under_mouse and self.action_func is not None:
                        self.action_func()
                result = True
        elif isinstance(event, widget_event.MouseEnterEvent) or isinstance(event, widget_event.MouseLeaveEvent):
            result = True

        if result:
            self._update_color_state()
        return result

    def _update_color_state(self, animate = True):
        if not self._enabled:
            new_state = self._State.DISABLED
        elif self._pressed:
            new_state = self._State.PRESSED_HOVER if self.is_under_mouse else self._State.PRESSED
        else:
            new_state = self._State.HOVER if self.is_under_mouse else self._State.DEFAULT

        if new_state is not self._state:
            self._state = new_state
            color = {
                self._State.DEFAULT: self.color,
                self._State.HOVER: drawing.lighten_color(self.color, 0.5),
                self._State.PRESSED: self.color,
                self._State.PRESSED_HOVER: drawing.darken_color(self.color, 0.5),
                self._State.DISABLED: drawing.darken_color(self.color, 0.5)
            }[self._state]
            if animate:
                self._color.transition().target(color).duration(0.125).ease_out()
            else:
                self._color.value = color

class TextButtonWidget(ButtonWidget):
    def __init__(self):
        super().__init__()
        self.desired_width = None
        self.desired_height = points(20.0)
        self.color = (0.5, 0.5, 0.5, 1.0)
        self.text = ""
        self.font_name = "arial"
        self.text_size = points(12.0)

    def get_desired_size(self):
        desired_width = self.desired_width
        if desired_width is None:
            desired_width = drawing.measure_text(self.text, self.font_name, self.text_size)[0]
            # Add some padding
            desired_width += self.desired_height - self.text_size
        return (desired_width, self.desired_height)

    def draw_visible(self, parent_transform):
        transform = parent_transform * self.get_transform()
        with transform:
            drawing.draw_rectangle(
                0.0,
                0.0,
                self.width.value,
                self.height.value,
                self._color.value,
                border_thickness = points(1.0),
                border_color = constants.Color.BLACK,
                radius = points(8.0))
            drawing.draw_text(
                self.text,
                self.font_name,
                self.text_size,
                self.width.value * 0.5,
                self.height.value * 0.5,
                drawing.HorizontalAlignment.CENTER,
                drawing.VerticalAlignment.MIDDLE,
                constants.Color.BLACK)

class IconButtonWidget(ButtonWidget):
    def __init__(self):
        super().__init__()
        self.desired_width = inches(1.0)
        self.desired_height = inches(1.0)
        self.color = constants.Ui.ICON_BUTTON_COLOR
        self.icon_name = None

    def get_desired_size(self):
        return (self.desired_width, self.desired_height)

    def draw_visible(self, parent_transform):
        transform = parent_transform * self.get_transform()
        with transform:
            drawing.draw_icon(
                self.icon_name,
                0.0,
                0.0,
                self.width.value,
                self.height.value,
                self._color.value)

class DropdownWidget(WidgetWithSize):
    class _State(Enum):
        DEFAULT = 0
        HOVER = 1
        PRESSED = 2
        PRESSED_HOVER = 3

    _COLOR_DEFAULT = (0.9, 0.9, 0.9, 1.0)
    _COLOR_HOVER = drawing.lighten_color(_COLOR_DEFAULT, 1.0)
    _COLOR_PRESSED = drawing.darken_color(_COLOR_DEFAULT, 0.25)

    _COLOR_OPTION_STRIPE_A = (0.8, 0.8, 0.8, 1.0)
    _COLOR_OPTION_STRIPE_B = (0.9, 0.9, 0.9, 1.0)
    _COLOR_OPTION_HOVER = (0.6, 0.6, 1.0, 1.0)
    _COLOR_OPTION_PRESSED = (0.3, 0.3, 0.5, 1.0)

    def __init__(self):
        super().__init__()
        self.desired_width = inches(2.0)
        self.desired_height = points(20.0)
        self.font_name = "arial"
        self.text_size = points(12.0)
        self.selected_option_changed_func = None

        self._pressed = False
        self._options_visible = False
        self._dropdown_ratio = parameter.AnimatableParameter(0.0)

        self._value_state = self._State.DEFAULT
        self._value_color = parameter.AnimatableParameter(self._COLOR_DEFAULT)

        self._options = None # Tuple of (value, string)
        self._option_states = None
        self._option_colors = None
        self._selected_option_index = None

    @property
    def selected_option_index(self):
        return self._selected_option_index

    @selected_option_index.setter
    def selected_option_index(self, selected_option_index):
        assert selected_option_index is None or (selected_option_index >= 0 and selected_option_index < len(self._options))
        self._selected_option_index = selected_option_index

    def set_options(self, options):
        self._options = [(v, t) for v, t in options]
        self._option_states = [self._State.DEFAULT for x in options]
        self._option_colors = []
        for i in range(len(options)):
            color = self._COLOR_OPTION_STRIPE_A if i % 2 == 0 else self._COLOR_OPTION_STRIPE_B
            self._option_colors.append(parameter.AnimatableParameter(color))
        if self._selected_option_index is not None and self._selected_option_index >= len(options):
            self._selected_option_index = None

    # Returns whether the event was consumed
    def process_event(self, event):
        result = False
        option_index = None
        if not self._options_visible:
            if isinstance(event, widget_event.MouseEvent) and event.button is widget_event.MouseButton.LEFT:
                if event.event_type is widget_event.MouseEventType.PRESS:
                    self._pressed = True
                    self.capture()
                    self.focus()
                    result = True
                elif event.event_type is widget_event.MouseEventType.RELEASE:
                    if self._pressed:
                        self._pressed = False
                        if self.is_under_mouse:
                            self._options_visible = True
                            self._dropdown_ratio.transition().target(1.0).duration(0.125).ease_out()
                        else:
                            self.release_capture()
                    result = True
            elif isinstance(event, widget_event.MouseEnterEvent) or isinstance(event, widget_event.MouseLeaveEvent):
                result = True
        else:
            close_options = False
            if isinstance(event, widget_event.MouseEvent):
                option_index = self._get_option_index_for_mouse_position(event.x, event.y)
                if event.button is widget_event.MouseButton.LEFT:
                    if event.event_type is widget_event.MouseEventType.PRESS:
                        if option_index is None:
                            close_options = True
                        else:
                            self._pressed = True
                            self.capture()
                        result = True
                    elif event.event_type is widget_event.MouseEventType.RELEASE:
                        if self._pressed:
                            self._pressed = False
                            close_options = True
                            if option_index is not None and option_index >= 0:
                                self._selected_option_index = option_index
                                if self.selected_option_changed_func is not None:
                                    self.selected_option_changed_func()
                        result = True
                elif event.event_type is widget_event.MouseEventType.MOVE:
                    result = True

            if close_options:
                self.release_capture()
                self._options_visible = False
                self._dropdown_ratio.transition().target(0.0).duration(0.125).ease_out()

        if result:
            self._update_color_state(option_index)
        return result

    def layout_widget(self, layout_position, layout_size, horizontal_placement, vertical_placement):
        if vertical_placement is VerticalPlacement.FILL:
            vertical_placement = VerticalPlacement.MIDDLE
        super().layout_widget(layout_position, layout_size, horizontal_placement, vertical_placement)

    def get_desired_size(self):
        return (self.desired_width, self.desired_height)

    def draw_visible(self, parent_transform):
        transform = parent_transform * self.get_transform()
        text_padding = (self.height.value - self.text_size) * 0.5
        icon_size = self.height.value

        def draw_selected_option_text_and_arrow(down):
            if self._selected_option_index is not None:
                with drawing.scissor(0.0, 0.0, self.width.value - icon_size - text_padding, self.height.value, transform = transform):
                    drawing.draw_text(
                        self._options[self._selected_option_index][1],
                        self.font_name,
                        self.text_size,
                        text_padding,
                        self.height.value * 0.5,
                        drawing.HorizontalAlignment.LEFT,
                        drawing.VerticalAlignment.MIDDLE,
                        constants.Color.BLACK)
            drawing.draw_icon(
                "arrow_down" if down else "arrow_up",
                self.width.value - icon_size,
                0.0,
                self.width.value,
                self.height.value,
                constants.Color.BLACK)

        if self._dropdown_ratio.value == 0.0:
            with transform:
                drawing.draw_rectangle(
                    0.0,
                    0.0,
                    self.width.value,
                    self.height.value,
                    self._value_color.value,
                    border_thickness = points(1.0),
                    border_color = constants.Color.BLACK,
                    radius = points(8.0))
                draw_selected_option_text_and_arrow(not self._options_visible)
        else:
            def draw_overlay():
                with transform:
                    dropdown_height = self.height.value * self._dropdown_ratio.value * len(self._options)

                    p1 = transform.transform_point((0.0, 0.0))
                    p2 = transform.transform_point((self.width.value, self.height.value))
                    p1 = (p1[0] - 1.0, p1[1])
                    p2 = (p2[0] + 1.0, p2[1] + 1.0)
                    with drawing.scissor(p1[0], p1[1], p2[0], p2[1]):
                        drawing.draw_rectangle(
                            0.0,
                            -dropdown_height,
                            self.width.value,
                            self.height.value,
                            self._value_color.value,
                            border_thickness = points(1.0),
                            border_color = constants.Color.BLACK,
                            radius = points(8.0))

                    for i, color in enumerate(self._option_colors):
                        p1 = transform.transform_point((0.0, (-i - 1) * self.height.value))
                        p2 = transform.transform_point((self.width.value, -i * self.height.value))
                        p1 = (p1[0] - 1.0, p1[1] - (1.0 if i + 1 == len(self._option_colors) else 0.0))
                        p2 = (p2[0] + 1.0, p2[1])
                        with drawing.scissor(p1[0], p1[1], p2[0], p2[1]):
                            drawing.draw_rectangle(
                                0.0,
                                -dropdown_height,
                                self.width.value,
                                self.height.value,
                                color.value,
                                border_thickness = points(1.0),
                                border_color = constants.Color.BLACK,
                                radius = points(8.0))

                    draw_selected_option_text_and_arrow(not self._options_visible)

                    # Draw option text
                    with drawing.scissor(0.0, -dropdown_height, self.width.value - text_padding, 0.0, transform):
                        for i, (value, text) in enumerate(self._options):
                            drawing.draw_text(
                                text,
                                self.font_name,
                                self.text_size,
                                text_padding,
                                (-i - 0.5) * self.height.value,
                                drawing.HorizontalAlignment.LEFT,
                                drawing.VerticalAlignment.MIDDLE,
                                constants.Color.BLACK)

            self.add_overlay(draw_overlay)

    def _get_option_index_for_mouse_position(self, x, y):
        transform = self.get_full_transform()
        x, y = transform.inverse().transform_point((x, y))
        if x < 0.0 or x >= self.width.value:
            return None
        if y >= 0.0 and y < self.height.value:
            return -1
        dropdown_height = self.height.value * self._dropdown_ratio.value * len(self._options)
        option_index = -int(math.floor(y / self.height.value)) - 1
        if y >= -dropdown_height and option_index >= 0 and option_index < len(self._options):
            return option_index
        return None

    def _update_color_state(self, hover_option_index):
        new_option_states = [self._State.DEFAULT for x in self._options]
        if not self._options_visible:
            if self._pressed:
                new_value_state = self._State.PRESSED_HOVER if self.is_under_mouse else self._State.PRESSED
            else:
                new_value_state = self._State.HOVER if self.is_under_mouse else self._State.DEFAULT
        else:
            new_value_state = self._State.DEFAULT

        if hover_option_index is not None and hover_option_index >= 0:
            new_option_states[hover_option_index] = self._State.PRESSED_HOVER if self._pressed else self._State.HOVER

        if new_value_state is not self._value_state:
            self._value_state = new_value_state
            color = {
                self._State.DEFAULT: self._COLOR_DEFAULT,
                self._State.HOVER: self._COLOR_HOVER,
                self._State.PRESSED: self._COLOR_DEFAULT,
                self._State.PRESSED_HOVER: self._COLOR_PRESSED
            }[self._value_state]
            self._value_color.transition().target(color).duration(0.125).ease_out()

        for i in range(len(self._option_states)):
            if new_option_states[i] is not self._option_states[i]:
                self._option_states[i] = new_option_states[i]
                stripe_color = self._COLOR_OPTION_STRIPE_A if i % 2 == 0 else self._COLOR_OPTION_STRIPE_B
                color = {
                    self._State.DEFAULT: stripe_color,
                    self._State.HOVER: self._COLOR_OPTION_HOVER,
                    self._State.PRESSED: stripe_color,
                    self._State.PRESSED_HOVER: self._COLOR_OPTION_PRESSED
                }[self._option_states[i]]
                self._option_colors[i].transition().target(color).duration(0.125).ease_out()

class SpinnerWidget(WidgetWithSize):
    class _State(Enum):
        DEFAULT = 0
        HOVER = 1
        PRESSED = 2

    _COLOR_INNER = constants.Color.WHITE
    _COLOR_OUTER_DEFAULT = (0.5, 0.5, 0.5, 1.0)
    _COLOR_OUTER_HOVER = drawing.lighten_color(_COLOR_OUTER_DEFAULT, 0.5)
    _COLOR_OUTER_BACKGROUND = (0.25, 0.25, 0.25, 1.0)
    _RATIO_START = 0.125
    _RATIO_END = 0.875

    def __init__(self):
        super().__init__()
        self.desired_size = points(40.0)
        self.min_value = 0.0
        self.max_value = 1.0
        self.value = 0.0
        self.decimals = 1
        self.round_to_decimals = True
        self.font_name = "arial"
        self.text_size = points(12.0)
        self.on_value_changed_func = None
        self._pressed = False
        self._state = self._State.DEFAULT
        self._outer_thickness = points(4.0)
        self._pressed_outer_thickness = points(20.0)
        self._color_outer = parameter.AnimatableParameter(self._COLOR_OUTER_DEFAULT)
        self._outer_ratio = parameter.AnimatableParameter(0.0)

    def process_event(self, event):
        result = False
        if isinstance(event, widget_event.MouseEvent):
            if event.button is widget_event.MouseButton.LEFT:
                if event.event_type is widget_event.MouseEventType.PRESS:
                    self._pressed = True
                    self.capture()
                    self.focus()
                    result = True
                elif event.event_type is widget_event.MouseEventType.RELEASE:
                    self.release_capture()
                    self._pressed = False
                    result = True
            elif event.event_type is widget_event.MouseEventType.MOVE:
                if self._pressed:
                    # Rotate by 90 degrees CW
                    xy = self.get_full_transform().inverse().transform_point((event.x, event.y))
                    relative_x = xy[0] - self.width.value * 0.5
                    relative_y = xy[1] - self.height.value * 0.5
                    distance2 = relative_x * relative_x + relative_y * relative_y
                    inner_radius = self.desired_size * 0.5 - self._outer_thickness
                    if distance2 >= inner_radius * inner_radius:
                        angle = math.atan2(-relative_x, relative_y)
                        ratio = 0.5 - angle * (0.5 / math.pi)
                        ratio = (ratio - self._RATIO_START) / (self._RATIO_END - self._RATIO_START)
                        ratio = min(max(ratio, 0.0), 1.0)
                        self.value = self.min_value + ratio * (self.max_value - self.min_value)
                        if self.round_to_decimals:
                            multiplier = 10 ** self.decimals
                            self.value = round(self.value * multiplier) / multiplier
                            self.value = min(max(self.value, self.min_value), self.max_value)

                        if self.on_value_changed_func is not None:
                            self.on_value_changed_func()
                    result = True
        elif isinstance(event, widget_event.MouseEnterEvent) or isinstance(event, widget_event.MouseLeaveEvent):
            result = True

        if result:
            self._update_color_and_size_state()
        return result

    def get_desired_size(self):
        return (self.desired_size, self.desired_size)

    def draw_visible(self, parent_transform):
        transform = parent_transform * self.get_transform()
        def draw():
            with transform:
                inner_radius = self.desired_size * 0.5 - self._outer_thickness
                outer_thickness = self._outer_thickness + self._outer_ratio.value * (self._pressed_outer_thickness - self._outer_thickness)
                outer_radius = inner_radius + outer_thickness
                ratio = (self.value - self.min_value) / (self.max_value - self.min_value)
                drawing.draw_spinner(
                    self.width.value * 0.5,
                    self.height.value * 0.5,
                    self._COLOR_INNER,
                    self._color_outer.value,
                    self._COLOR_OUTER_BACKGROUND,
                    inner_radius,
                    outer_radius,
                    ratio)

                text = "{:,.{d}f}".format(self.value, d = self.decimals)
                drawing.draw_text(
                    text,
                    self.font_name,
                    self.text_size,
                    self.width.value * 0.5,
                    self.height.value * 0.5,
                    drawing.HorizontalAlignment.CENTER,
                    drawing.VerticalAlignment.MIDDLE,
                    constants.Color.BLACK)

        if self._pressed:
            self.add_overlay(draw)
        else:
            draw()

    def _update_color_and_size_state(self):
        if self._pressed:
            new_state = self._State.PRESSED
        else:
            new_state = self._State.HOVER if self.is_under_mouse else self._State.DEFAULT

        if new_state is not self._state:
            self._state = new_state
            color = {
                self._State.DEFAULT: self._COLOR_OUTER_DEFAULT,
                self._State.HOVER: self._COLOR_OUTER_HOVER,
                self._State.PRESSED: self._COLOR_OUTER_HOVER
            }[self._state]
            self._color_outer.transition().target(color).duration(0.125).ease_out()

            ratio = {
                self._State.DEFAULT: 0.0,
                self._State.HOVER: 0.0,
                self._State.PRESSED: 1.0
            }[self._state]
            self._outer_ratio.transition().target(ratio).duration(0.125).ease_out()

class InputWidget(WidgetWithSize):
    _COLOR = (0.9, 0.9, 0.9, 1.0)
    _COLOR_DISABLED = drawing.darken_color(_COLOR, 0.5)
    _CURSOR_PHASE_DURATION = 2.0 / 3.0

    def __init__(self):
        super().__init__()
        self.desired_width = inches(2.0)
        self.desired_height = points(20.0)
        self.text = ""
        self.font_name = "arial"
        self.text_size = points(12.0)
        self.text_changed_func = None
        self._color = parameter.AnimatableParameter(self._COLOR)
        self._enabled = True
        self._cursor_phase = 0.0
        self._cursor_updater = None

    def destroy(self):
        if self._cursor_updater is not None:
            self._cursor_updater.cancel()
        super().destroy()

    @property
    def enabled(self):
        return self._enabled

    def set_enabled(self, enabled, animate = True):
        if enabled != self._enabled:
            self._enabled = enabled
            if not enabled:
                self.release_capture()
                self.release_focus()
            self._update_color_state(animate)

    def process_event(self, event):
        result = False
        if isinstance(event, widget_event.MouseEvent):
            if event.button is widget_event.MouseButton.LEFT and event.event_type is widget_event.MouseEventType.PRESS:
                self.focus()
                if self._cursor_updater is None:
                    def _update_cursor_phase(dt):
                        self._cursor_phase = (self._cursor_phase + dt) % self._CURSOR_PHASE_DURATION
                    self._cursor_phase = 0.0
                    self._cursor_updater = timer.Updater(_update_cursor_phase)
                result = True
        elif isinstance(event, widget_event.KeyEvent) and event.event_type is widget_event.KeyEventType.PRESS:
            if event.key_code is widget_event.KeyCode.BACKSPACE:
                self.text = self.text[:-1]
                result = True
            elif event.char_code is not None and len(event.char_code) > 0:
                # $TODO filter out characters like ESC
                self.text += event.char_code
                result = True
            if result and self.text_changed_func is not None:
                self.text_changed_func()
        elif isinstance(event, widget_event.FocusLostEvent):
            if self._cursor_updater is not None:
                self._cursor_updater.cancel()
                self._cursor_updater = None
            result = True

        return result

    def layout_widget(self, layout_position, layout_size, horizontal_placement, vertical_placement):
        if vertical_placement is VerticalPlacement.FILL:
            vertical_placement = VerticalPlacement.MIDDLE
        super().layout_widget(layout_position, layout_size, horizontal_placement, vertical_placement)

    def get_desired_size(self):
        return (self.desired_width, self.desired_height)

    def draw_visible(self, parent_transform):
        transform = parent_transform * self.get_transform()
        text_padding = (self.height.value - self.text_size) * 0.5

        with transform:
            drawing.draw_rectangle(
                0.0,
                0.0,
                self.width.value,
                self.height.value,
                self._color.value,
                border_thickness = points(1.0),
                border_color = constants.Color.BLACK,
                radius = points(8.0))

            def draw_text(x, horizontal_alignment):
                drawing.draw_text(
                    self.text,
                    self.font_name,
                    self.text_size,
                    x,
                    self.height.value * 0.5,
                    horizontal_alignment,
                    drawing.VerticalAlignment.MIDDLE,
                    constants.Color.BLACK)

            width, ascent, descent = drawing.measure_text(self.text, self.font_name, self.text_size)
            if width <= self.width.value - text_padding * 2.0:
                draw_text(text_padding, drawing.HorizontalAlignment.LEFT)
                cursor_position = text_padding + width
            else:
                with drawing.scissor(text_padding, 0.0, self.width.value, self.height.value, transform = transform):
                    draw_text(self.width.value - text_padding, drawing.HorizontalAlignment.RIGHT)
                cursor_position = self.width.value - text_padding

            if self.is_focused:
                alpha = abs(math.cos(self._cursor_phase * math.pi / self._CURSOR_PHASE_DURATION))
                drawing.draw_rectangle(
                    cursor_position,
                    (self.height.value - ascent) * 0.5,
                    cursor_position + 1.0,
                    (self.height.value + ascent) * 0.5,
                    (0.0, 0.0, 0.0, alpha))

    def _update_color_state(self, animated = True):
        color = self._COLOR if self._enabled else self._COLOR_DISABLED
        if animated:
            self.color.transition().target(color).duration(0.125).ease_out()
        else:
            self.color.value = color
