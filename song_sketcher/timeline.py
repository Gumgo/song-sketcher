from song_sketcher import constants
from song_sketcher.dialogs import edit_track_dialog
from song_sketcher import drawing
from song_sketcher import history_manager
from song_sketcher import project
from song_sketcher import song_timing
from song_sketcher import time_bar
from song_sketcher.units import *
from song_sketcher import widget
from song_sketcher import widget_event

_SONG_LENGTH_MEASURE_PADDING = 3

class Timeline:
    def __init__(self, root_stack_widget, project, history_manager, get_selected_clip_id_func, on_time_bar_sample_changed_func):
        self._root_stack_widget = root_stack_widget
        self._project = project
        self._history_manager = history_manager
        self._get_selected_clip_id_func = get_selected_clip_id_func

        self._padding = _get_measure_padding()

        self._root_layout = widget.GridLayoutWidget()
        self._root_layout.set_row_weight(1, 1.0)
        self._root_layout.set_column_weight(0, 1.0)

        time_bar_layout = widget.HStackedLayoutWidget()
        self._root_layout.add_child(0, 0, time_bar_layout)

        # The measure layout has a total extra size of padding, therefore pad by padding/2 on each side
        # Inset on left by (padding : track : padding : padding/2)
        # Inset on right by (padding/2)
        left_padding = _get_track_width() + self._padding * 2.5
        right_padding = self._padding * 0.5

        time_bar_layout.margin = (left_padding, points(4.0), right_padding, points(4.0))

        self._time_bar = time_bar.TimeBarWidget()
        time_bar_layout.add_child(self._time_bar, weight = 1.0)
        self._time_bar.desired_height = points(20.0)
        self._time_bar.max_sample = 1.0
        self._time_bar.end_sample = 1.0
        self._time_bar.on_sample_changed_func = on_time_bar_sample_changed_func

        h_scrollbar = widget.HScrollbarWidget()
        self._root_layout.add_child(2, 0, h_scrollbar)

        v_scrollbar = widget.VScrollbarWidget()
        self._root_layout.add_child(1, 1, v_scrollbar)

        vertical_scroll_area = widget.ScrollAreaWidget()
        self._root_layout.add_child(1, 0, vertical_scroll_area)
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

        # Update the time bar when we scroll
        self._time_bar.width.add_change_listener(lambda x: self._update_time_bar())
        self._measures_layout.x.add_change_listener(lambda x: self._update_time_bar())

        self._layout_widgets(False)

    @property
    def root_layout(self):
        return self._root_layout

    def set_enabled(self, enabled):
        for widget in self._track_widgets.values():
            widget.enabled = enabled
        self._add_track_widget.set_enabled(enabled)
        for widget in self._measure_widgets.values():
            widget.enabled = enabled

    def update_tracks(self):
        self._layout_widgets(True)

    def get_song_length_samples(self):
        samples_per_measure = song_timing.get_samples_per_measure(
            self._project.sample_rate,
            self._project.beats_per_minute,
            self._project.beats_per_measure)
        return self._get_song_length_measures() * samples_per_measure

    def get_playback_sample_index(self):
        return self._time_bar.sample

    def set_playback_sample_index(self, sample):
        self._time_bar.sample = sample

    def _layout_widgets(self, animate = True):
        self._tracks_layout.clear_children()
        self._tracks_layout.margin = (self._padding, 0.0, self._padding, 0.0) # Side padding

        self._measures_layout.clear_children()

        # Remove old tracks
        removed_tracks = [x for x in self._track_widgets if x not in self._project.tracks]
        for removed_track in removed_tracks:
            self._track_widgets.pop(removed_track).destroy()

        # Determine song length in measures
        song_length_measures = self._get_song_length_measures()

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
                    overlap = self._project.get_clip_by_id(track.measure_clip_ids[i]).measure_count

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
            # This produces weird border blending, could fix if desired
            # Avoid weird alpha transitions
            #if old_color[3] == 0.0:
            #    old_color = (*new_color[0:3], 0.0)
            #if new_color[3] == 0.0:
            #    new_color = (*old_color[0:3], 0.0)
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

        self._update_time_bar()

    def _add_track(self):
        def on_accept(name):
            new_track = project.Track()
            new_track.name = name

            def do():
                self._project.tracks.append(new_track)
                self._layout_widgets()

            def undo():
                self._project.tracks.remove(new_track)
                self._project.update_track_length()
                self._layout_widgets()

            do()

            entry = history_manager.Entry()
            entry.undo_func = undo
            entry.redo_func = do
            self._history_manager.add_entry(entry)

        edit_track_dialog.EditTrackDialog(self._root_stack_widget, None, on_accept, None)

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
                self._project.update_track_length()
                self._layout_widgets()

            def undo():
                self._project.tracks.insert(track_index, track)
                self._project.update_track_length()
                self._layout_widgets()

            do()

            entry = history_manager.Entry()
            entry.undo_func = undo
            entry.redo_func = do
            self._history_manager.add_entry(entry)

        edit_track_dialog.EditTrackDialog(self._root_stack_widget, track, on_accept, on_delete)

    def _add_or_remove_measure(self, track, index):
        if index < len(track.measure_clip_ids):
            has_clip = track.measure_clip_ids[index] is not None
        else:
            has_clip = False

        if has_clip:
            # Remove the existing clip
            old_clip_id = track.measure_clip_ids[index]

            def do():
                track.measure_clip_ids[index] = None
                self._project.update_track_length()
                self._layout_widgets()

            def undo():
                self._project.ensure_track_length(index + 1)
                track.measure_clip_ids[index] = old_clip_id
                self._project.update_track_length()
                self._layout_widgets()

            do()

            entry = history_manager.Entry()
            entry.undo_func = undo
            entry.redo_func = do
            self._history_manager.add_entry(entry)
        else:
            # Add the selected clip
            new_clip_id = self._get_selected_clip_id_func()
            if new_clip_id is None:
                return

            # Make sure there's enough space for this clip
            new_clip = self._project.get_clip_by_id(new_clip_id)
            for i in range(new_clip.measure_count):
                measure_index = index + i
                if measure_index < len(track.measure_clip_ids) and track.measure_clip_ids[measure_index] is not None:
                    # No space - # $TODO indicate this somehow?
                    return

            def do():
                self._project.ensure_track_length(index + 1)
                track.measure_clip_ids[index] = new_clip_id
                self._project.update_track_length()
                self._layout_widgets()

            def undo():
                track.measure_clip_ids[index] = None
                self._project.update_track_length()
                self._layout_widgets()

            do()

            entry = history_manager.Entry()
            entry.undo_func = undo
            entry.redo_func = do
            self._history_manager.add_entry(entry)

    def _get_song_length_measures(self):
        song_length_measures = 0
        for track in self._project.tracks:
            for i, clip_id in enumerate(track.measure_clip_ids):
                if clip_id is not None:
                    clip = self._project.get_clip_by_id(clip_id)
                    song_length_measures = max(song_length_measures, i + clip.measure_count)
        song_length_measures += _SONG_LENGTH_MEASURE_PADDING
        return song_length_measures

    def _update_time_bar(self):
        # Determine song length in measures
        song_length_measures = self._get_song_length_measures()

        measure_width = _get_measure_width(None) + self._padding
        samples_per_measure = song_timing.get_samples_per_measure(
            self._project.sample_rate,
            self._project.beats_per_minute,
            self._project.beats_per_measure)
        time_bar_width_samples = self._time_bar.width.value * samples_per_measure / measure_width
        start_measure = -self._measures_layout.x.value / measure_width

        self._time_bar.start_sample = start_measure * samples_per_measure
        self._time_bar.end_sample = self._time_bar.start_sample + time_bar_width_samples
        self._time_bar.min_sample = 0.0
        self._time_bar.max_sample = song_length_measures * samples_per_measure
        self._time_bar.sample = self._time_bar.sample # The setter performs min/max clamping

def _get_measure_padding():
    return points(4.0)

def _get_measure_width(clip):
    measures = 1 if clip is None else clip.measure_count
    return inches(1.5) * measures + _get_measure_padding() * (measures - 1)

def _get_measure_color(category):
    return drawing.rgba255(*category.color) if category is not None else (0.0, 0.0, 0.0, 0.0)

def _get_track_width():
    return inches(1.5)

def _get_track_height():
    return inches(1.0)

class AddTrackWidget(widget.AbsoluteLayoutWidget):
    def __init__(self, add_func):
        super().__init__()
        self.desired_width = _get_track_width()
        self.desired_height = _get_track_height()

        background = widget.RectangleWidget()
        background.desired_width = self.desired_width
        background.desired_height = self.desired_height
        background.color.value = (0.0, 0.0, 0.0, 0.0)
        background.border_thickness.value = points(1.0)
        background.border_color.value = (0.5, 0.5, 0.5, 1.0)
        background.radius.value = points(4.0)
        self.add_child(background)

        self._button = widget.IconButtonWidget()
        self._button.icon_name = "plus"
        self._button.desired_width = inches(0.75)
        self._button.desired_height = inches(0.75)
        self._button.x.value = (self.desired_width - self._button.desired_width) * 0.5
        self._button.y.value = (self.desired_height - self._button.desired_height) * 0.5
        self._button.action_func = add_func
        self.add_child(self._button)

    def set_enabled(self, enabled):
        self._button.set_enabled(enabled)

class TrackWidget(widget.AbsoluteLayoutWidget):
    _COLOR = (0.75, 0.75, 0.75, 1.0)

    def __init__(self, track, on_double_click_func):
        super().__init__()
        self.track = track
        self.on_double_click_func = on_double_click_func
        self.enabled = True

        self.desired_width = _get_track_width()
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
        if not self.enabled:
            return False

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
        self.enabled = True

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
        self.name.x.value = self.desired_width * 0.5

    def process_event(self, event):
        if not self.enabled:
            return False

        if (isinstance(event, widget_event.MouseEvent)
            and event.button is widget_event.MouseButton.LEFT
            and event.event_type is widget_event.MouseEventType.PRESS):
            self.on_click_func()
            return True

        return False
