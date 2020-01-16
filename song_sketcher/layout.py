from enum import Enum

from song_sketcher.units import *

class LayoutRect:
    def __init__(self, position = None, size = None):
        self.position = [0.0, 0.0] if position is None else [x for x in position]
        self.size = [0.0, 0.0] if size is None else [x for x in size]

class Direction(Enum):
    HORIZONTAL = 0
    VERTICAL = 1

class StackedLayout:
    class _Entry:
        def __init__(self):
            self.get_desired_size_func = None
            self.weight = None
            self.rect = None
            self.on_compute_layout_func = None

    # margin can be a single value, a tuple of (l,b,r,t), or None
    def __init__(self, direction, margin = None):
        self._direction = direction
        if margin is None:
            self._margin = tuple([0.0] * 4)
        elif isinstance(margin, int) or isinstance(margin, float):
            self._margin = tuple([margin] * 4)
        else:
            self._margin = tuple(margin)
        self._entries = []

    # on_compute_layout_func gets passed the resolved rect
    def add_entry(
        self,
        size,
        weight = 0.0,
        on_compute_layout_func = None):
        entry = self._Entry()
        entry.get_desired_size_func = lambda: size() if callable(size) else size
        entry.weight = weight
        entry.rect = LayoutRect()
        entry.on_compute_layout_func = on_compute_layout_func
        self._entries.append(entry)
        return entry.rect

    def add_padding(self, padding, weight = 0.0):
        entry = self._Entry()
        size = [None, None]
        size[self._direction.value] = padding
        size[1 - self._direction.value] = 0.0
        entry.get_desired_size_func = lambda: size
        entry.weight = weight
        entry.rect = LayoutRect()
        self._entries.append(entry)
        return entry.rect

    def compute_layout(self, parent_rect):
        if self._direction is Direction.HORIZONTAL:
            entries = self._entries
        else:
            assert self._direction is Direction.VERTICAL
            # Reverse entries in vertical mode so we can build top down rather than bottom up
            entries = [x for x in reversed(self._entries)]

        direction_index = self._direction.value
        alt_direction_index = 1 - direction_index

        absolute_sizes = [entry.get_desired_size_func()[direction_index] for entry in entries]
        total_absolute_size = self._margin[direction_index] + self._margin[direction_index + 2] + sum(absolute_sizes)
        total_weight = sum(entry.weight for entry in entries)
        total_weight = 1.0 if total_weight == 0.0 else total_weight
        total_weighted_size = max(0.0, parent_rect.size[direction_index] - total_absolute_size)

        weighted_sizes = [total_weighted_size * entry.weight / total_weight for entry in entries]
        sizes = [a + w for a, w in zip(absolute_sizes, weighted_sizes)]
        if SNAP_TO_PIXELS:
            sizes = _snap_sizes_to_pixels(sizes)

        offset = parent_rect.position[direction_index] + self._margin[direction_index]
        alt_offset = parent_rect.position[alt_direction_index] + self._margin[alt_direction_index]
        alt_size = parent_rect.size[alt_direction_index] - self._margin[alt_direction_index] - self._margin[alt_direction_index + 2]
        for entry, size in zip(entries, sizes):
            entry.rect.position[direction_index] = offset
            entry.rect.position[1 - direction_index] = alt_offset
            entry.rect.size[direction_index] = size
            entry.rect.size[1 - direction_index] = alt_size
            if entry.on_compute_layout_func is not None:
                entry.on_compute_layout_func(entry.rect)

            offset += size

    def compute_desired_size(self):
        direction_index = self._direction.value
        alt_direction_index = 1 - direction_index
        desired_size = [0.0, 0.0]
        for entry in self._entries:
            entry_desired_size = entry.get_desired_size_func()
            desired_size[direction_index] += entry_desired_size[direction_index]
            desired_size[alt_direction_index] = max(desired_size[alt_direction_index], entry_desired_size[alt_direction_index])
        desired_size[0] += self._margin[0] + self._margin[2]
        desired_size[1] += self._margin[1] + self._margin[3]
        return tuple(desired_size)

class GridLayout:
    class _Entry:
        def __init__(self):
            self.row = None
            self.column = None
            self.get_desired_size_func = None
            self.rect = None
            self.on_compute_layout_func = None

    # margin can be a single value, a tuple of (l,b,r,t), or None
    def __init__(self, margin = None):
        if margin is None:
            self._margin = tuple([0.0] * 4)
        elif isinstance(margin, int) or isinstance(margin, float):
            self._margin = tuple([margin] * 4)
        else:
            self._margin = tuple(margin)
        self._entries = []
        self._row_sizes = {}
        self._column_sizes = {}
        self._row_weights = {}
        self._column_weights = {}

    # on_compute_layout_func gets passed the resolved rect
    def add_entry(self, row, column, size, on_compute_layout_func = None):
        entry = self._Entry()
        entry.row = row
        entry.column = column
        entry.get_desired_size_func = lambda: size() if callable(size) else size
        entry.rect = LayoutRect()
        entry.on_compute_layout_func = on_compute_layout_func
        self._entries.append(entry)
        return entry.rect

    def set_row_size(self, row, size):
        self._row_sizes[row] = size

    def set_column_size(self, column, size):
        self._column_sizes[column] = size

    def set_row_weight(self, row, weight):
        self._row_weights[row] = weight

    def set_column_weight(self, column, weight):
        self._column_weights[column] = weight

    def compute_layout(self, parent_rect):
        absolute_column_sizes, absolute_row_sizes = self._get_absolute_column_and_row_sizes()
        column_count = len(absolute_column_sizes)
        row_count = len(absolute_row_sizes)

        total_absolute_width = self._margin[0] + self._margin[2] + sum(absolute_column_sizes)
        total_absolute_height = self._margin[1] + self._margin[3] + sum(absolute_row_sizes)
        total_column_weight = sum(self._column_weights.values())
        total_row_weight = sum(self._row_weights.values())
        total_column_weight = 1.0 if total_column_weight == 0.0 else total_column_weight
        total_row_weight = 1.0 if total_row_weight == 0.0 else total_row_weight
        total_weighted_width = max(0.0, parent_rect.size[0] - total_absolute_width)
        total_weighted_height = max(0.0, parent_rect.size[1] - total_absolute_height)

        column_weight_multiplier = total_weighted_width / total_column_weight
        column_sizes = [x + self._column_weights.get(i, 0.0) * column_weight_multiplier for i, x in enumerate(absolute_column_sizes)]
        if SNAP_TO_PIXELS:
            column_sizes = _snap_sizes_to_pixels(column_sizes)

        row_weight_multiplier = total_weighted_height / total_row_weight
        row_sizes = [x + self._row_weights.get(i, 0.0) * row_weight_multiplier for i, x in enumerate(absolute_row_sizes)]
        if SNAP_TO_PIXELS:
            row_sizes = _snap_sizes_to_pixels(row_sizes)

        offset_x = parent_rect.position[0] + self._margin[0]
        column_xs = [0.0] * column_count
        for i, size in enumerate(column_sizes):
            column_xs[i] = offset_x
            offset_x += size

        offset_y = parent_rect.position[1] + self._margin[1]
        row_ys = [0.0] * row_count
        for i in range(row_count):
            row_ys[row_count - i - 1] = offset_y
            offset_y += row_sizes[row_count - i - 1]

        for entry in self._entries:
            entry.rect.position[0] = column_xs[entry.column]
            entry.rect.position[1] = row_ys[entry.row]
            entry.rect.size[0] = column_sizes[entry.column]
            entry.rect.size[1] = row_sizes[entry.row]
            if entry.on_compute_layout_func is not None:
                entry.on_compute_layout_func(entry.rect)

    def compute_desired_size(self):
        absolute_column_sizes, absolute_row_sizes = self._get_absolute_column_and_row_sizes()
        total_absolute_width = self._margin[0] + self._margin[2] + sum(absolute_column_sizes)
        total_absolute_height = self._margin[1] + self._margin[3] + sum(absolute_row_sizes)
        return (total_absolute_width, total_absolute_height)

    def _get_absolute_column_and_row_sizes(self):
        column_count = max(
            max((x.column for x in self._entries), default = -1) + 1,
            max(self._column_sizes.keys(), default = -1) + 1)
        row_count = max(
            max((x.row for x in self._entries), default = -1) + 1,
            max(self._row_sizes.keys(), default = -1) + 1)

        absolute_column_sizes = [0.0] * column_count
        absolute_row_sizes = [0.0] * row_count
        for column, size in self._column_sizes.items():
            absolute_column_sizes[column] = size
        for row, size in self._row_sizes.items():
            absolute_row_sizes[row] = size
        for entry in self._entries:
            size = entry.get_desired_size_func()
            absolute_column_sizes[entry.column] = max(absolute_column_sizes[entry.column], size[0])
            absolute_row_sizes[entry.row] = max(absolute_row_sizes[entry.row], size[1])

        return (absolute_column_sizes, absolute_row_sizes)

def _snap_sizes_to_pixels(sizes):
    offsets = []
    offset = 0.0
    for x in sizes:
        offsets.append(offset)
        offset += x
    offsets.append(offset)
    offsets = [float(round(x)) for x in offsets]

    snapped_sizes = []
    for i in range(len(sizes)):
        snapped_sizes.append(offsets[i + 1] - offsets[i])
    return snapped_sizes
