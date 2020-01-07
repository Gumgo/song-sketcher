import constants
import drawing
from units import *
import widget
import widget_event

class TimeBarWidget(widget.WidgetWithSize):
    _COLOR = (0.25, 0.25, 0.75, 1.0)

    def __init__(self):
        super().__init__()
        self.desired_width = 0.0
        self.desired_height = 0.0
        self.start_sample = 0.0
        self.end_sample = 0.0
        self.min_sample = 0.0
        self.max_sample = 0.0
        self.sample = 0.0
        self.on_sample_changed_func = None
        self._pressed = False

    def process_event(self, event):
        result = False
        update_sample = False
        if isinstance(event, widget_event.MouseEvent):
            if event.button is widget_event.MouseButton.LEFT:
                if event.event_type is widget_event.MouseEventType.PRESS:
                    self._pressed = True
                    self.capture()
                    self.focus()
                    result = True
                    update_sample = True
                elif event.event_type is widget_event.MouseEventType.RELEASE:
                    self.release_capture()
                    self._pressed = False
                    result = True
            elif event.event_type is widget_event.MouseEventType.MOVE:
                result = True
                if self._pressed:
                    update_sample = True

        if update_sample:
            x, y = self.get_full_transform().inverse().transform_point((event.x, event.y))
            if self.width.value != 0.0:
                sample_ratio = x / self.width.value
                sample = self.start_sample + sample_ratio * (self.end_sample - self.start_sample)
                self.sample = min(max(sample, self.min_sample), self.max_sample)
                if self.on_sample_changed_func is not None:
                    self.on_sample_changed_func()

        return result

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
                self._COLOR,
                border_thickness = points(1.0),
                border_color = constants.Color.BLACK)

            with drawing.scissor(0.0, 0.0, self.width.value, self.height.value, transform = transform):
                x = self.width.value * self._sample_ratio()
                drawing.draw_rectangle(
                    x - points(0.5),
                    0.0,
                    x + points(0.5),
                    self.height.value,
                    constants.Color.BLACK)

    def _sample_ratio(self):
        if self.start_sample == self.end_sample:
            return 0.0
        else:
            return (self.sample - self.start_sample) / (self.end_sample - self.start_sample)
