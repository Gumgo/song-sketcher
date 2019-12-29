from enum import Enum

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

        offset = parent_rect.position[direction_index] + self._margin[direction_index]
        alt_offset = parent_rect.position[alt_direction_index] + self._margin[alt_direction_index]
        alt_size = parent_rect.size[alt_direction_index] - self._margin[alt_direction_index] - self._margin[alt_direction_index + 2]
        for entry, absolute_size in zip(entries, absolute_sizes):
            size = absolute_size + (total_weighted_size * entry.weight / total_weight)

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
