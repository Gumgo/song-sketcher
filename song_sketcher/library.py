from song_sketcher import constants
from song_sketcher.dialogs import edit_category_dialog
from song_sketcher.dialogs import edit_clip_dialog
from song_sketcher import drawing
from song_sketcher import engine
from song_sketcher import history_manager
from song_sketcher import project
from song_sketcher.units import *
from song_sketcher import widget
from song_sketcher import widget_event

class Library:
    def __init__(self, root_stack_widget, project, history_manager, update_tracks_func):
        self._root_stack_widget = root_stack_widget
        self._project = project
        self._history_manager = history_manager
        self._update_tracks_func = update_tracks_func

        self._selected_clip_id = None

        self._padding = points(4.0)

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

        self._categories_layout = widget.VStackedLayoutWidget()
        vertical_scroll_area_layout.add_child(self._categories_layout)

        horizontal_scroll_area = widget.ScrollAreaWidget()
        vertical_scroll_area_layout.add_child(horizontal_scroll_area, weight = 1.0)
        horizontal_scroll_area.horizontal_scrollbar = h_scrollbar

        self._clips_layout = widget.GridLayoutWidget()
        horizontal_scroll_area.set_child(self._clips_layout)

        self._category_widgets = {}                                 # Maps ClipCategory -> CategoryWidget
        self._add_category_widget = AddWidget(self._add_category)   # AddWidget at the end of categories
        self._clip_widgets = {}                                     # Maps Clip -> ClipWidget
        self._add_clip_widgets = {}                                 # Maps ClipCategory -> AddWidget

        self._layout_widgets(False)

    @property
    def root_layout(self):
        return self._root_layout

    @property
    def selected_clip_id(self):
        return self._selected_clip_id

    def set_enabled(self, enabled):
        for widget in self._category_widgets.values():
            widget.enabled = enabled
        self._add_category_widget.set_enabled(enabled)
        for widget in self._clip_widgets.values():
            widget.enabled = enabled
        for widget in self._add_clip_widgets.values():
            widget.set_enabled(enabled)

    def _layout_widgets(self, animate = True):
        self._categories_layout.clear_children()
        self._categories_layout.margin = (self._padding, 0.0, self._padding, 0.0) # Side padding

        self._clips_layout.clear_children()
        self._clips_layout.margin = (0.0, 0.0, self._padding, 0.0) # Side padding

        # Remove old categories
        removed_categories = [x for x in self._category_widgets if x not in self._project.clip_categories]
        for removed_category in removed_categories:
            self._category_widgets.pop(removed_category).destroy()
            self._add_clip_widgets.pop(removed_category).destroy()

        # Remove old clips
        removed_clips = [x for x in self._clip_widgets if x not in self._project.clips]
        for removed_clip in removed_clips:
            self._clip_widgets.pop(removed_clip).destroy()

        # Backup current positions and colors for animation
        prev_layout_height = self._categories_layout.height.value
        prev_category_positions = dict((c, (w.x.value, w.y.value)) for c, w in self._category_widgets.items())
        prev_category_colors = dict((c, w.color.value) for c, w in self._category_widgets.items())
        prev_add_category_position = (self._add_category_widget.x.value, self._add_category_widget.y.value)
        prev_clip_positions = dict((c, (w.x.value, w.y.value)) for c, w in self._clip_widgets.items())
        prev_clip_colors = dict((c, w.color.value) for c, w in self._clip_widgets.items())
        prev_add_clip_positions = dict((c, (w.x.value, w.y.value)) for c, w in self._add_clip_widgets.items())

        # Add new categories
        for category in self._project.clip_categories:
            if category not in self._category_widgets:
                self._category_widgets[category] = CategoryWidget(category, lambda category = category: self._edit_category(category))
            if category not in self._add_clip_widgets:
                self._add_clip_widgets[category] = AddWidget(lambda category = category: self._add_clip(category))

            # Add new clips
            for clip_id in category.clip_ids:
                clip = self._project.get_clip_by_id(clip_id)
                if clip not in self._clip_widgets:
                    self._clip_widgets[clip] = ClipWidget(
                        category,
                        clip,
                        clip_id == self._selected_clip_id,
                        lambda clip_id = clip_id: self._select_clip(clip_id),
                        lambda clip = clip: self._edit_clip(clip))

        self._categories_layout.add_padding(self._padding)
        self._clips_layout.set_row_size(0, self._padding)
        self._clips_layout.set_column_size(0, self._padding)

        # Layout categories in order
        for y, category in enumerate(self._project.clip_categories):
            category_widget = self._category_widgets[category]
            category_widget.color.value = constants.rgba255(*category.color)
            category_widget.name.text = category.name
            self._categories_layout.add_child(category_widget)
            self._categories_layout.add_padding(self._padding)

            # Layout clips in order
            for x, clip_id in enumerate(category.clip_ids):
                clip = self._project.get_clip_by_id(clip_id)
                clip_widget = self._clip_widgets[clip]
                clip_widget.color.value = constants.rgba255(*category.color)
                clip_widget.name.text = clip.name
                self._clips_layout.add_child(y * 2 + 1, x * 2 + 1, clip_widget)
                self._clips_layout.set_column_size(x * 2 + 2, self._padding)

            self._clips_layout.add_child(y * 2 + 1, len(category.clip_ids) * 2 + 1, self._add_clip_widgets[category])
            self._clips_layout.set_column_size(len(category.clip_ids) * 2 + 2, self._padding)

            self._clips_layout.set_row_size(y * 2 + 2, self._padding)

        self._categories_layout.add_child(self._add_category_widget)
        self._categories_layout.add_padding(self._padding)

        # Do this so that the heights of the two layouts match
        self._clips_layout.set_row_size(len(self._project.clip_categories) * 2 + 1, self._add_category_widget.desired_height)
        self._clips_layout.set_row_size(len(self._project.clip_categories) * 2 + 2, self._padding)

        self._root_layout.layout_children()

        def animate_position(widget, old_position):
            new_x = widget.x.value
            new_y = widget.y.value
            widget.x.value = old_position[0]
            widget.x.transition().target(new_x).duration(0.125).ease_out()
            widget.y.value = old_position[1] + (self._categories_layout.height.value - prev_layout_height)
            widget.y.transition().target(new_y).duration(0.125).ease_out()

        def animate_color(widget, old_color):
            new_color = widget.color.value
            widget.color.value = old_color
            widget.color.transition().target(new_color).duration(0.125).ease_out()

        # Revert categories and clips to their original positions and colors and animate them
        for category, widget in self._category_widgets.items():
            old_position = prev_category_positions.get(category, None)
            if old_position is not None:
                animate_position(widget, old_position)
            old_color = prev_category_colors.get(category, None)
            if old_color is not None:
                animate_color(widget, old_color)
        animate_position(self._add_category_widget, prev_add_category_position)

        for clip, widget in self._clip_widgets.items():
            old_position = prev_clip_positions.get(clip, None)
            if old_position is not None:
                animate_position(widget, old_position)
            old_color = prev_clip_colors.get(clip, None)
            if old_color is not None:
                animate_color(widget, old_color)

        for category, widget in self._add_clip_widgets.items():
            old_position = prev_add_clip_positions.get(category, None)
            if old_position is not None:
                animate_position(widget, old_position)

        # Make sure selection color is up to date
        self._select_clip(self._selected_clip_id)

    def _add_category(self):
        def on_accept(name, color, gain):
            new_category = project.ClipCategory()
            new_category.name = name
            new_category.color = color
            new_category.gain = gain

            def do():
                self._project.clip_categories.append(new_category)
                self._layout_widgets()

            def undo():
                self._project.clip_categories.remove(new_category)
                self._layout_widgets()

            do()

            entry = history_manager.Entry()
            entry.undo_func = undo
            entry.redo_func = do
            self._history_manager.add_entry(entry)

        edit_category_dialog.EditCategoryDialog(self._root_stack_widget, None, on_accept, None)

    def _edit_category(self, category):
        def on_accept(name, color, gain):
            if name == category.name and color == category.color and gain == category.gain:
                return # Nothing changed

            old_name = category.name
            old_color = category.color
            old_gain = category.gain

            def do():
                category.name = name
                category.color = color
                category.gain = gain
                self._layout_widgets()
                self._update_tracks_func()

            def undo():
                category.name = old_name
                category.color = old_color
                category.gain = old_gain
                self._layout_widgets()
                self._update_tracks_func()

            do()

            entry = history_manager.Entry()
            entry.undo_func = undo
            entry.redo_func = do
            self._history_manager.add_entry(entry)

        def on_delete():
            old_clips = self._project.clips.copy()
            category_index = self._project.clip_categories.index(category)

            track_usages = set()
            for track in self._project.tracks:
                for i, clip_id in enumerate(track.measure_clip_ids):
                    if clip_id in category.clip_ids:
                        track_usages.add((clip_id, track, i))

            def do():
                clip_ids_to_delete = set(category.clip_ids)
                self._project.clips = [x for x in self._project.clips if x.id not in clip_ids_to_delete]
                self._project.clip_categories.remove(category)

                for clip_id, track, index in track_usages:
                    track.measure_clip_ids[index] = None
                self._project.update_track_length()

                if self._selected_clip_id in clip_ids_to_delete:
                    self._selected_clip_id = None

                self._layout_widgets()
                self._update_tracks_func()

            def undo():
                self._project.clips = old_clips
                self._project.clip_categories.insert(category_index, category)

                if len(track_usages) > 0:
                    max_index = max(i for c, t, i in track_usages)
                    self._project.ensure_track_length(max_index + 1)
                    for clip_id, track, index in track_usages:
                        track.measure_clip_ids[index] = clip_id
                    self._project.update_track_length()

                self._layout_widgets()
                self._update_tracks_func()

            def destroy(was_undone):
                if not was_undone:
                    clip_ids = set(category.clip_ids)
                    deleted_clips = [x for x in old_clips if x.id in clip_ids]
                    for clip in deleted_clips:
                        print(("DELETE C", clip.engine_clip))
                        engine.delete_clip(clip.engine_clip)

            do()

            entry = history_manager.Entry()
            entry.undo_func = undo
            entry.redo_func = do
            entry.destroy_func = destroy
            self._history_manager.add_entry(entry)

        edit_category_dialog.EditCategoryDialog(self._root_stack_widget, category, on_accept, on_delete)

    def _add_clip(self, category):
        def on_accept(new_clip):
            new_clip.id = self._project.generate_clip_id()
            new_clip.category = category

            def do():
                self._project.clips.append(new_clip)
                category.clip_ids.append(new_clip.id)
                self._layout_widgets()

            def undo():
                self._project.clips.remove(new_clip)
                category.clip_ids.remove(new_clip.id)
                if self._selected_clip_id == new_clip.id:
                    self._selected_clip_id = None
                self._layout_widgets()

            def destroy(was_undone):
                if was_undone:
                    print(("DELETE D", new_clip.engine_clip))
                    engine.delete_clip(new_clip.engine_clip)

            do()

            entry = history_manager.Entry()
            entry.undo_func = undo
            entry.redo_func = do
            entry.destroy_func = destroy
            self._history_manager.add_entry(entry)

        edit_clip_dialog.EditClipDialog(self._root_stack_widget, self._project, None, on_accept, None)

    def _edit_clip(self, clip):
        def on_accept(edited_clip):
            assert clip.measure_count == edited_clip.measure_count # Should not change when editing

            if (edited_clip.name == clip.name
                and edited_clip.sample_count == clip.sample_count
                and edited_clip.start_sample_index == clip.start_sample_index
                and edited_clip.end_sample_index == clip.end_sample_index
                and edited_clip.has_intro == clip.has_intro
                and edited_clip.has_outro == clip.has_outro
                and edited_clip.gain == clip.gain
                and edited_clip.engine_clip == clip.engine_clip):
                return # Nothing changed

            old_name = clip.name
            old_sample_count = clip.sample_count
            old_start_sample_index = clip.start_sample_index
            old_end_sample_index = clip.end_sample_index
            old_has_intro = clip.has_intro
            old_has_outro = clip.has_outro
            old_gain = clip.gain
            old_engine_clip = clip.engine_clip

            did_engine_clip_change = (edited_clip.engine_clip != clip.engine_clip)

            def do():
                clip.name = edited_clip.name
                clip.sample_count = edited_clip.sample_count
                clip.start_sample_index = edited_clip.start_sample_index
                clip.end_sample_index = edited_clip.end_sample_index
                clip.has_intro = edited_clip.has_intro
                clip.has_outro = edited_clip.has_outro
                clip.gain = edited_clip.gain
                clip.engine_clip = edited_clip.engine_clip
                self._layout_widgets()
                self._update_tracks_func()

            def undo():
                clip.name = old_name
                clip.sample_count = old_sample_count
                clip.start_sample_index = old_start_sample_index
                clip.end_sample_index = old_end_sample_index
                clip.has_intro = old_has_intro
                clip.has_outro = old_has_outro
                clip.gain = old_gain
                clip.engine_clip = old_engine_clip
                self._layout_widgets()
                self._update_tracks_func()

            def destroy(was_undone):
                if did_engine_clip_change:
                    if was_undone:
                        # We undid the edit, so delete the re-recorded engine clip
                        print(("DELETE 11", edited_clip.engine_clip))
                        engine.delete_clip(edited_clip.engine_clip)
                    else:
                        # We're holding the last reference to the original engine clip, so delete it
                        print(("DELETE 22", old_engine_clip))
                        engine.delete_clip(old_engine_clip)

            do()

            entry = history_manager.Entry()
            entry.undo_func = undo
            entry.redo_func = do
            entry.destroy_func = destroy
            self._history_manager.add_entry(entry)

        def on_delete():
            clip_index = self._project.clips.index(clip)
            category = next(x for x in self._project.clip_categories if clip.id in x.clip_ids)
            category_index = category.clip_ids.index(clip.id)

            track_usages = set()
            for track in self._project.tracks:
                for i, clip_id in enumerate(track.measure_clip_ids):
                    if clip_id == clip.id:
                        track_usages.add((track, i))

            def do():
                self._project.clips.remove(clip)
                category.clip_ids.remove(clip.id)

                for track, index in track_usages:
                    track.measure_clip_ids[index] = None
                self._project.update_track_length()

                if self._selected_clip_id == clip.id:
                    self._selected_clip_id = None

                self._layout_widgets()
                self._update_tracks_func()

            def undo():
                self._project.clips.insert(clip_index, clip)
                category.clip_ids.insert(category_index, clip.id)

                if len(track_usages) > 0:
                    max_index = max(i for t, i in track_usages)
                    self._project.ensure_track_length(max_index + 1)
                    for track, index in track_usages:
                        track.measure_clip_ids[index] = clip.id
                    self._project.update_track_length()

                self._layout_widgets()
                self._update_tracks_func()

            def destroy(was_undone):
                if not was_undone:
                    print(("DELETE AAA", clip.engine_clip))
                    engine.delete_clip(clip.engine_clip)

            do()

            entry = history_manager.Entry()
            entry.undo_func = undo
            entry.redo_func = do
            entry.destroy_func = destroy
            self._history_manager.add_entry(entry)

        edit_clip_dialog.EditClipDialog(self._root_stack_widget, self._project, clip, on_accept, on_delete)

    def _select_clip(self, clip_id):
        if self._selected_clip_id is not None:
            selected_clip_widget = self._clip_widgets[self._project.get_clip_by_id(self._selected_clip_id)]
            selected_clip_widget.background.border_color.transition().target(ClipWidget.UNSELECTED_COLOR).duration(0.125).ease_out()
        self._selected_clip_id = clip_id
        if self._selected_clip_id is not None:
            selected_clip_widget = self._clip_widgets[self._project.get_clip_by_id(self._selected_clip_id)]
            selected_clip_widget.background.border_color.transition().target(ClipWidget.SELECTED_COLOR).duration(0.125).ease_out()

class AddWidget(widget.AbsoluteLayoutWidget):
    def __init__(self, add_func):
        super().__init__()
        self.desired_width = inches(1.5)
        self.desired_height = inches(1.0)

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

class CategoryWidget(widget.AbsoluteLayoutWidget):
    def __init__(self, category, on_double_click_func):
        super().__init__()
        self.category = category
        self.on_double_click_func = on_double_click_func
        self.enabled = True

        self.desired_width = inches(1.5)
        self.desired_height = inches(1.0)

        self.background = widget.RectangleWidget()
        self.background.desired_width = self.desired_width
        self.background.desired_height = self.desired_height
        self.background.color.value = constants.Ui.CATEGORY_COLOR
        self.background.border_thickness.value = points(4.0)
        self.background.border_color.value = constants.rgba255(*self.category.color)
        self.background.radius.value = points(4.0)
        self.add_child(self.background)

        self.name = widget.TextWidget()
        self.name.text = self.category.name
        self.name.x.value = self.desired_width * 0.5
        self.name.y.value = self.desired_height * 0.5
        self.name.horizontal_alignment = drawing.HorizontalAlignment.CENTER
        self.name.vertical_alignment = drawing.VerticalAlignment.MIDDLE
        self.add_child(self.name)

    @property
    def color(self):
        return self.background.border_color

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

class ClipWidget(widget.AbsoluteLayoutWidget):
    SELECTED_COLOR = constants.Color.WHITE
    UNSELECTED_COLOR = constants.Color.BLACK

    def __init__(self, category, clip, is_selected, on_click_func, on_double_click_func):
        super().__init__()
        self.category = category
        self.clip = clip
        self.on_click_func = on_click_func
        self.on_double_click_func = on_double_click_func
        self.enabled = True

        self.desired_width = inches(1.5)
        self.desired_height = inches(1.0)

        self.background = widget.RectangleWidget()
        self.background.desired_width = self.desired_width
        self.background.desired_height = self.desired_height
        self.background.color.value = constants.rgba255(*self.category.color)
        self.background.border_thickness.value = points(1.0)
        self.background.border_color.value = self.SELECTED_COLOR if is_selected else self.UNSELECTED_COLOR
        self.background.radius.value = points(4.0)
        self.add_child(self.background)

        self.name = widget.TextWidget()
        self.name.text = self.clip.name
        self.name.x.value = self.desired_width * 0.5
        self.name.y.value = self.desired_height * 0.5
        self.name.horizontal_alignment = drawing.HorizontalAlignment.CENTER
        self.name.vertical_alignment = drawing.VerticalAlignment.MIDDLE
        self.add_child(self.name)

    @property
    def color(self):
        return self.background.color

    def process_event(self, event):
        if not self.enabled:
            return False

        if isinstance(event, widget_event.MouseEvent) and event.button is widget_event.MouseButton.LEFT:
            if event.event_type is widget_event.MouseEventType.PRESS:
                self.on_click_func()
                return True
            elif event.event_type is widget_event.MouseEventType.DOUBLE_CLICK:
                self.on_double_click_func()
                return True

        return False
