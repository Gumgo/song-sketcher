import constants
import dialogs.edit_track_dialog
import drawing
import history_manager
import project
from units import *
import widget
import widget_event

_SONG_LENGTH_MEASURE_PADDING = 3

class Timeline:
    def __init__(self, root_stack_widget, project, history_manager):
        self._root_stack_widget = root_stack_widget
        self._project = project
        self._history_manager = history_manager

        self._padding = _get_measure_padding()

        self._root_layout = widget.GridLayoutWidget()
        self._root_layout.set_row_weight(0, 1.0)
        self._root_layout.set_column_weight(0, 1.0)

        h_scrollbar = widget.HScrollbarWidget()
        self._root_layout.add_child(1, 0, h_scrollbar)

        v_scrollbar = widget.VScrollbarWidget()
        self._root_layout.add_child(0, 1, v_scrollbar)

        vertical_scroll_area = widget.ScrollAreaWidget()
        self._root_layout.add_child(0, 0, vertical_scroll_area)
        vertical_scroll_area.vertical_scrollbar = v_scrollbar

        vertical_scroll_area_layout = widget.HStackedLayoutWidget()
        vertical_scroll_area.set_child(vertical_scroll_area_layout)

        self._tracks_layout = widget.VStackedLayoutWidget()
        vertical_scroll_area_layout.add_child(self._tracks_layout)

        horizontal_scroll_area = widget.ScrollAreaWidget()
        vertical_scroll_area_layout.add_child(horizontal_scroll_area, weight = 1.0)
        horizontal_scroll_area.horizontal_scrollbar = h_scrollbar

        self._measures_layout = widget.AbsoluteLayoutWidget() # Can't use a grid because measure can span, unfortunately
        horizontal_scroll_area.set_child(self._measures_layout)

        self._track_widgets = {}                                    # Maps Track -> TrackWidget
        self._add_track_widget = AddTrackWidget(self._add_track)    # AddTrackWidget at the end of tracks
        self._measure_widgets = {}                                  # Maps (Track, index) -> MeasureWidget

        self._layout_widgets(False)

    @property
    def root_layout(self):
        return self._root_layout

    def _layout_widgets(self, animate = True):
        self._tracks_layout.clear_children()
        self._tracks_layout.margin = (self._padding, 0.0, self._padding, 0.0) # Side padding

        self._measures_layout.clear_children()

        # Remove old tracks
        removed_tracks = [x for x in self._track_widgets if x not in self._project.tracks]
        for removed_track in removed_tracks:
            self._track_widgets.pop(removed_track).destroy()

        # Determine song length in measures
        song_length_measures = 0
        for track in self._project.tracks:
            for i, clip_id in enumerate(track.measure_clip_ids):
                if clip_id is not None:
                    clip = self._project.get_clip_by_id(clip_id)
                    song_length_measures = max(song_length_measures, i + clip.measures)
        song_length_measures += _SONG_LENGTH_MEASURE_PADDING

        # Determine which measures are still valid
        # Valid measures are ones which aren't overlapped by a clip
        valid_measures = set() # Holds (Track, index) tuples
        for track in self._project.tracks:
            overlap = 0
            for i in range(song_length_measures):
                overlap = max(0, overlap - 1)
                if overlap == 0:
                    valid_measures.add((track, i))
                if i < len(track.measure_clip_ids) and track.measure_clip_ids[i] is not None:
                    overlap = self._project.get_clip_by_id(clip_id).measures

        # Remove old measures
        removed_measures = [x for x in self._measure_widgets if x not in valid_measures]
        for removed_measure in removed_measures:
            self._measure_widgets.pop(removed_measure).destroy()

        # Backup current positions and colors for animation
        prev_layout_height = self._tracks_layout.height.value
        prev_track_positions = dict((t, (w.x.value, w.y.value)) for t, w in self._track_widgets.items())
        prev_add_track_position = (self._add_track_widget.x.value, self._add_track_widget.y.value)
        prev_measure_positions = dict((m, (w.x.value, w.y.value)) for m, w in self._measure_widgets.items())
        prev_measure_widths = dict((m, w.width.value) for m, w in self._measure_widgets.items())
        prev_measure_text_xs = dict((m, w.name.x.value) for m, w in self._measure_widgets.items())
        prev_measure_colors = dict((m, w.background.color.value) for m, w in self._measure_widgets.items())

        # Add new tracks
        for track in self._project.tracks:
            if track not in self._track_widgets:
                self._track_widgets[track] = TrackWidget(track, lambda track = track: self._edit_track(track))

            # Add new measures and update existing ones
            for i in range(song_length_measures):
                key = (track, i)
                if key in valid_measures:
                    widget = self._measure_widgets.get(key, None)
                    if widget is None:
                        widget = MeasureWidget(lambda key = key: self._add_or_remove_measure(key[0], key[1]))
                        self._measure_widgets[key] = widget

                    clip_id = track.measure_clip_ids[i] if i < len(track.measure_clip_ids) else None
                    if clip_id is None:
                        clip = None
                        category = None
                    else:
                        clip = self._project.get_clip_by_id(clip_id)
                        category = clip.category
                    widget.set_category_and_clip(category, clip)

        self._tracks_layout.add_padding(self._padding)

        column_width = _get_measure_width(None) + self._padding
        row_height = _get_track_height() + self._padding
        total_rows = len(self._project.tracks) + 1 # 1 extra row for "add track"
        total_height = row_height * total_rows + self._padding
        self._measures_layout.desired_width = column_width * song_length_measures + self._padding
        self._measures_layout.desired_height = total_height

        # Layout tracks in order
        for y, track in enumerate(self._project.tracks):
            track_widget = self._track_widgets[track]
            track_widget.name.text = track.name
            self._tracks_layout.add_child(track_widget)
            self._tracks_layout.add_padding(self._padding)

            # Layout measures in order
            for i in range(song_length_measures):
                key = (track, i)
                measure_widget = self._measure_widgets.get(key, None)
                if measure_widget is not None:
                    self._measures_layout.add_child(measure_widget)
                    measure_widget.x.value = self._padding + column_width * i
                    measure_widget.y.value = self._padding + row_height * (total_rows - y - 1)

        self._tracks_layout.add_child(self._add_track_widget)
        self._tracks_layout.add_padding(self._padding)

        self._root_layout.layout_children()

        def animate_position(widget, old_position):
            if old_position is None:
                return
            new_x = widget.x.value
            new_y = widget.y.value
            widget.x.value = old_position[0]
            widget.x.transition().target(new_x).duration(0.125).ease_out()
            widget.y.value = old_position[1] + (self._tracks_layout.height.value - prev_layout_height)
            widget.y.transition().target(new_y).duration(0.125).ease_out()

        def animate_width(widget, old_width):
            if old_width is None:
                return
            new_width = widget.width.value
            widget.width.value = old_width
            widget.background.width.value = old_width
            widget.width.transition().target(new_width).duration(0.125).ease_out()
            widget.background.width.transition().target(new_width).duration(0.125).ease_out()

        def animate_text_x(widget, old_x):
            if old_x is None:
                return
            new_x = widget.name.x.value
            widget.name.x.value = old_x
            widget.name.x.transition().target(new_x).duration(0.125).ease_out()

        def animate_color(widget, old_color):
            if old_color is None:
                return
            new_color = widget.background.color.value
            # Avoid weird alpha transitions
            if old_color[3] == 0.0:
                old_color = (*new_color[0:3], 0.0)
            if new_color[3] == 0.0:
                new_color = (*old_color[0:3], 0.0)
            widget.background.color.value = old_color
            widget.background.color.transition().target(new_color).duration(0.125).ease_out()

        # Revert tracks and measures to their original positions and colors and animate them
        for track, widget in self._track_widgets.items():
            animate_position(widget, prev_track_positions.get(track, None))
        animate_position(self._add_track_widget, prev_add_track_position)

        for key, widget in self._measure_widgets.items():
            animate_position(widget, prev_measure_positions.get(key, None))
            animate_width(widget, prev_measure_widths.get(key, None))
            animate_text_x(widget, prev_measure_text_xs.get(key, None))
            animate_color(widget, prev_measure_colors.get(key, None))

    def _add_track(self):
        def on_accept(name):
            new_track = project.Track()
            new_track.name = name

            def do():
                self._project.tracks.append(new_track)
                self._layout_widgets()

            def undo():
                self._project.tracks.remove(new_track)
                self._layout_widgets()

            do()

            entry = history_manager.Entry()
            entry.undo_func = undo
            entry.redo_func = do
            self._history_manager.add_entry(entry)

        dialogs.edit_track_dialog.EditTrackDialog(self._root_stack_widget, None, on_accept, None)

    def _edit_track(self, track):
        def on_accept(name):
            if name == track.name:
                return # Nothing changed

            old_name = track.name

            def do():
                track.name = name
                self._layout_widgets()

            def undo():
                track.name = old_name
                self._layout_widgets()

            do()

            entry = history_manager.Entry()
            entry.undo_func = undo
            entry.redo_func = do
            self._history_manager.add_entry(entry)

        def on_delete():
            track_index = self._project.tracks.index(track)

            def do():
                self._project.tracks.remove(track)
                self._layout_widgets()

            def undo():
                self._project.tracks.insert(track_index, track)
                self._layout_widgets()

            do()

            entry = history_manager.Entry()
            entry.undo_func = undo
            entry.redo_func = do
            self._history_manager.add_entry(entry)

        dialogs.edit_track_dialog.EditTrackDialog(self._root_stack_widget, track, on_accept, on_delete)

    def _add_or_remove_measure(self, track, index):
        # $TODO query clip, add/remove it, adjust song length

        def do():
            self._layout_widgets()

        def undo():
            self._layout_widgets()

        do()

        entry = history_manager.Entry()
        entry.undo_func = undo
        entry.redo_func = do
        self._history_manager.add_entry(entry)

def _get_measure_padding():
    return points(4.0)

def _get_measure_width(clip):
    measures = 1 if clip is None else clip.measures
    return inches(1.5) * measures + _get_measure_padding() * (measures - 1)

def _get_measure_color(category):
    return drawing.rgba255(*category.color) if category is not None else (0.0, 0.0, 0.0, 0.0)

def _get_track_height():
    return inches(1.0)

class AddTrackWidget(widget.AbsoluteLayoutWidget):
    def __init__(self, add_func):
        super().__init__()
        self.desired_width = inches(1.5)
        self.desired_height = _get_track_height()

        background = widget.RectangleWidget()
        background.desired_width = self.desired_width
        background.desired_height = self.desired_height
        background.color.value = (0.0, 0.0, 0.0, 0.0)
        background.border_thickness.value = points(1.0)
        background.border_color.value = (0.5, 0.5, 0.5, 1.0)
        background.radius.value = points(4.0)
        self.add_child(background)

        button = widget.IconButtonWidget()
        button.icon_name = "plus"
        button.desired_width = inches(0.75)
        button.desired_height = inches(0.75)
        button.x.value = (self.desired_width - button.desired_width) * 0.5
        button.y.value = (self.desired_height - button.desired_height) * 0.5
        button.action_func = add_func
        self.add_child(button)

class TrackWidget(widget.AbsoluteLayoutWidget):
    _COLOR = (0.75, 0.75, 0.75, 1.0)

    def __init__(self, track, on_double_click_func):
        super().__init__()
        self.track = track
        self.on_double_click_func = on_double_click_func

        self.desired_width = inches(1.5)
        self.desired_height = _get_track_height()

        self.background = widget.RectangleWidget()
        self.background.desired_width = self.desired_width
        self.background.desired_height = self.desired_height
        self.background.color.value = self._COLOR
        self.background.border_thickness.value = points(1.0)
        self.background.border_color.value = constants.Color.BLACK
        self.background.radius.value = points(4.0)
        self.add_child(self.background)

        self.name = widget.TextWidget()
        self.name.text = self.track.name
        self.name.x.value = self.desired_width * 0.5
        self.name.y.value = self.desired_height * 0.5
        self.name.horizontal_alignment = drawing.HorizontalAlignment.CENTER
        self.name.vertical_alignment = drawing.VerticalAlignment.MIDDLE
        self.add_child(self.name)

    def process_event(self, event):
        if isinstance(event, widget_event.MouseEvent) and event.button is widget_event.MouseButton.LEFT:
            if event.event_type is widget_event.MouseEventType.PRESS:
                return True
            elif event.event_type is widget_event.MouseEventType.DOUBLE_CLICK:
                self.on_double_click_func()
                return True

        return False

class MeasureWidget(widget.AbsoluteLayoutWidget):
    def __init__(self, on_click_func):
        super().__init__()
        self.on_click_func = on_click_func

        self.desired_width = _get_measure_width(None)
        self.desired_height = _get_track_height() # Measures line up with tracks

        self.background = widget.RectangleWidget()
        self.background.desired_width = self.desired_width
        self.background.desired_height = self.desired_height
        self.background.color.value = _get_measure_color(None)
        self.background.border_thickness.value = points(1.0)
        self.background.border_color.value = constants.Color.BLACK
        self.background.radius.value = points(4.0)
        self.add_child(self.background)

        self.name = widget.TextWidget()
        self.name.text = ""
        self.name.x.value = self.desired_width * 0.5
        self.name.y.value = self.desired_height * 0.5
        self.name.horizontal_alignment = drawing.HorizontalAlignment.CENTER
        self.name.vertical_alignment = drawing.VerticalAlignment.MIDDLE
        self.add_child(self.name)

    def set_category_and_clip(self, category, clip):
        self.desired_width = _get_measure_width(clip)
        self.background.desired_width = self.desired_width
        self.background.color.value = _get_measure_color(category)
        if category is None:
            self.name.text = ""
        else:
            self.name.text = "{}: {}".format(category.name, clip.name) # $TODO separate lines

    def process_event(self, event):
        if (isinstance(event, widget_event.MouseEvent)
            and event.button is widget_event.MouseButton.LEFT
            and event.event_type is widget_event.MouseEventType.PRESS):
            self.on_click_func()
            return True

        return False
