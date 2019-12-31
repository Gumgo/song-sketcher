import constants
import drawing
import history_manager
import project
from units import *
import widget

class Library:
    def __init__(self, project, history_manager):
        self._project = project
        self._history_manager = history_manager

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
        prev_add_category_position = (self._add_category_widget.x.value, self._add_category_widget.y.value)
        prev_clip_positions = dict((c, (w.x.value, w.y.value)) for c, w in self._clip_widgets.items())
        prev_clip_colors = dict((c, w.color.value) for c, w in self._clip_widgets.items())
        prev_add_clip_positions = dict((c, (w.x.value, w.y.value)) for c, w in self._add_clip_widgets.items())

        # Add new categories
        for category in self._project.clip_categories:
            if category not in self._category_widgets:
                self._category_widgets[category] = CategoryWidget(category)
            if category not in self._add_clip_widgets:
                self._add_clip_widgets[category] = AddWidget(lambda category = category: self._add_clip(category))

            # Add new clips
            for clip_id in category.clip_ids:
                clip = self._project.get_clip_by_id(clip_id)
                if clip not in self._clip_widgets:
                    self._clip_widgets[clip] = ClipWidget(category, clip)

        self._categories_layout.add_padding(self._padding)
        self._clips_layout.set_row_size(0, self._padding)
        self._clips_layout.set_column_size(0, self._padding)

        # Layout categories in order
        for y, category in enumerate(self._project.clip_categories):
            self._categories_layout.add_child(self._category_widgets[category])
            self._categories_layout.add_padding(self._padding)

            # Layout clips in order
            for x, clip_id in enumerate(category.clip_ids):
                clip = self._project.get_clip_by_id(clip_id)
                self._clips_layout.add_child(y * 2 + 1, x * 2 + 1, self._clip_widgets[clip])
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
            new_color = widget.background.color.value
            widget.background.color.value = old_color
            widget.background.color.transition().target(new_color).duration(0.125).ease_out()

        # Revert categories to their original y positions and animate them
        for category, widget in self._category_widgets.items():
            old_position = prev_category_positions.get(category, None)
            if old_position is not None:
                animate_position(widget, old_position)
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

    def _layout_clip_widgets(self, animate = True):
        pass

    def _add_category(self):
        new_category = project.ClipCategory()

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

    def _add_clip(self, category):
        pass

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

        button = widget.IconButtonWidget()
        button.icon_name = "plus"
        button.desired_width = inches(0.75)
        button.desired_height = inches(0.75)
        button.x.value = (self.desired_width - button.desired_width) * 0.5
        button.y.value = (self.desired_height - button.desired_height) * 0.5
        button.action_func = add_func
        self.add_child(button)

class CategoryWidget(widget.AbsoluteLayoutWidget):
    def __init__(self, category):
        super().__init__()
        self.category = category

        self.desired_width = inches(1.5)
        self.desired_height = inches(1.0)

        self.background = widget.RectangleWidget()
        self.background.desired_width = self.desired_width
        self.background.desired_height = self.desired_height
        self.background.color.value = drawing.rgba255(*self.category.color)
        self.background.border_thickness.value = points(1.0)
        self.background.border_color.value = constants.Color.BLACK
        self.background.radius.value = points(4.0)
        self.add_child(self.background)

        # $TODO clip text
        self.name = widget.TextWidget()
        self.name.text = self.category.name
        self.name.x.value = self.desired_width * 0.5
        self.name.y.value = self.desired_height * 0.5
        self.name.horizontal_alignment = drawing.HorizontalAlignment.CENTER
        self.name.vertical_alignment = drawing.VerticalAlignment.MIDDLE
        self.add_child(self.name)

class ClipWidget(widget.AbsoluteLayoutWidget):
    def __init__(self, category, clip):
        super().__init__()
        self.category = category
        self.clip = clip

        self.desired_width = inches(1.5)
        self.desired_height = inches(1.0)

        self.background = widget.RectangleWidget()
        self.background.desired_width = self.desired_width
        self.background.desired_height = self.desired_height
        self.background.color.value = drawing.rgba255(*self.category.color)
        self.background.border_thickness.value = points(1.0)
        self.background.border_color.value = constants.Color.BLACK
        self.background.radius.value = points(4.0)
        self.add_child(self.background)

        # $TODO clip text
        self.name = widget.TextWidget()
        self.name.text = self.clip.name
        self.name.x.value = self.desired_width * 0.5
        self.name.y.value = self.desired_height * 0.5
        self.name.horizontal_alignment = drawing.HorizontalAlignment.CENTER
        self.name.vertical_alignment = drawing.VerticalAlignment.MIDDLE
        self.add_child(self.name)
