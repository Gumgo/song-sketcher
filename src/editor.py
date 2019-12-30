import constants
import drawing
import new_project_dialog
from units import *
import widget
import widget_manager

class Constants:
    # Don't make this static because we can't initialize some values (e.g. points) until units are initialized
    def __init__(self):
        self.ROOT_BACKGROUND_COLOR = drawing.rgba255(45, 53, 85)

        self.MENU_PADDING = points(12.0)
        self.MENU_BACKGROUND_COLOR = drawing.rgba255(20, 24, 39)

        self.DIVIDER_SIZE = points(20.0)

class Editor:
    def __init__(self):
        self._constants = Constants()

        # Holds all project-related widgets so we can easily clear the whole list
        self._project_widgets = None

        self._root_stack_widget = widget.StackWidget()
        widget_manager.get().set_root_widget(self._root_stack_widget)

        root_background = widget.BackgroundWidget()
        self._root_stack_widget.push_child(root_background)
        root_background.color.value = self._constants.ROOT_BACKGROUND_COLOR

        self._root_layout = widget.HStackedLayoutWidget()
        root_background.set_child(self._root_layout)

        self._file_menu_widget = self._build_file_menu_widget()

        self._project_widgets = self._build_project_widget() # $TODO temporary - construct this on new project

        self._root_layout.add_child(self._file_menu_widget)
        self._root_layout.add_child(self._project_widgets.root_layout, weight = 1.0)

        root_background.layout_widget(
            (0.0, 0.0),
            widget_manager.get().display_size,
            widget.HorizontalPlacement.FILL,
            widget.VerticalPlacement.FILL)

    def shutdown(self):
        pass

    def update(self, dt):
        pass

    def _build_file_menu_widget(self):
        background = widget.BackgroundWidget()
        background.color.value = self._constants.MENU_BACKGROUND_COLOR
        background.border_thickness.value = points(2.0)
        background.border_color.value = constants.Color.BLACK

        layout = widget.VStackedLayoutWidget()
        background.set_child(layout)
        layout.margin = self._constants.MENU_PADDING

        self._new_project_button = widget.IconButtonWidget()
        layout.add_child(self._new_project_button)
        self._new_project_button.icon_name = "metronome" # $TODO
        self._new_project_button.action_func = lambda: new_project_dialog.NewProjectDialog(self._root_stack_widget)

        layout.add_padding(self._constants.MENU_PADDING)

        self._open_project_button = widget.IconButtonWidget()
        layout.add_child(self._open_project_button)
        self._open_project_button.icon_name = "metronome" # $TODO

        layout.add_padding(self._constants.MENU_PADDING)

        self._save_project_button = widget.IconButtonWidget()
        layout.add_child(self._save_project_button)
        self._save_project_button.icon_name = "metronome" # $TODO

        layout.add_padding(self._constants.MENU_PADDING)

        self._save_project_as_button = widget.IconButtonWidget()
        layout.add_child(self._save_project_as_button)
        self._save_project_as_button.icon_name = "metronome" # $TODO

        layout.add_padding(self._constants.MENU_PADDING)

        self._settings_button = widget.IconButtonWidget()
        layout.add_child(self._settings_button)
        self._settings_button.icon_name = "metronome" # $TODO

        layout.add_padding(0.0, weight = 1.0)

        self._quit_button = widget.IconButtonWidget()
        layout.add_child(self._quit_button)
        self._quit_button.icon_name = "metronome" # $TODO
        self._quit_button.action_func = lambda: exit(0) # $TODO this is just temporary

        return background

    def _build_project_widget(self):
        class ProjectWidgets:
            pass
        project_widgets = ProjectWidgets()

        project_widgets.root_layout = widget.HStackedLayoutWidget()

        timeline_library_layout = widget.VStackedLayoutWidget()
        project_widgets.root_layout.add_child(timeline_library_layout, weight = 1.0)

        timeline_library_layout.add_child(self._build_timeline_widget(), weight = 1.0)

        timeline_library_divider = widget.RectangleWidget()
        timeline_library_layout.add_child(timeline_library_divider)
        timeline_library_divider.desired_height = self._constants.DIVIDER_SIZE
        timeline_library_divider.color.value = self._constants.MENU_BACKGROUND_COLOR
        timeline_library_divider.border_thickness.value = points(2.0)
        timeline_library_divider.border_color.value = constants.Color.BLACK
        timeline_library_divider.left_open = True
        timeline_library_divider.right_open = True

        timeline_library_layout.add_padding(0.0, weight = 1.0)

        project_widgets.edit_menu_widget = self._build_edit_menu_widget()
        project_widgets.root_layout.add_child(project_widgets.edit_menu_widget)

        return project_widgets

    def _build_timeline_widget(self):
        test1 = widget.RectangleWidget()
        test1.border_thickness.value = points(4.0)
        test1.radius.value = points(4.0)
        test1.desired_width = inches(1.0)
        test1.desired_height = inches(10.0)

        test2 = widget.RectangleWidget()
        test2.border_thickness.value = points(4.0)
        test2.radius.value = points(4.0)
        test2.desired_width = inches(10.0)
        test2.desired_height = inches(10.0)

        return self._build_separate_horizontal_vertical_scroll_areas(test1, test2)

    def _build_library_widget(self):
        pass

    def _build_separate_horizontal_vertical_scroll_areas(self, vertical_layout, horizontal_layout):
        h_layout = widget.HStackedLayoutWidget()
        v_layout = widget.VStackedLayoutWidget()
        v_scrollbar_layout = widget.VStackedLayoutWidget()

        h_scrollbar = widget.HScrollbarWidget()
        v_scrollbar = widget.VScrollbarWidget()

        h_layout.add_child(v_layout, weight = 1.0)
        h_layout.add_child(v_scrollbar_layout)
        v_scrollbar_layout.add_child(v_scrollbar, weight = 1.0)
        v_scrollbar_layout.add_padding(h_scrollbar.desired_height)

        vertical_scroll_area = widget.ScrollAreaWidget()
        vertical_scroll_area.vertical_scrollbar = v_scrollbar
        v_layout.add_child(vertical_scroll_area, weight = 1.0)
        v_layout.add_child(h_scrollbar)

        vertical_scroll_area_layout = widget.HStackedLayoutWidget()
        vertical_scroll_area.set_child(vertical_scroll_area_layout)
        vertical_scroll_area_layout.add_child(vertical_layout)

        horizontal_scroll_area = widget.ScrollAreaWidget()
        horizontal_scroll_area.horizontal_scrollbar = h_scrollbar
        vertical_scroll_area_layout.add_child(horizontal_scroll_area, weight = 1.0)

        horizontal_scroll_area_layout = widget.HStackedLayoutWidget()
        horizontal_scroll_area.set_child(horizontal_scroll_area_layout)
        horizontal_scroll_area_layout.add_child(horizontal_layout)

        return h_layout

    def _build_edit_menu_widget(self):
        background = widget.BackgroundWidget()
        background.color.value = self._constants.MENU_BACKGROUND_COLOR
        background.border_thickness.value = points(2.0)
        background.border_color.value = constants.Color.BLACK

        layout = widget.VStackedLayoutWidget()
        background.set_child(layout)
        layout.margin = self._constants.MENU_PADDING

        self._play_pause_button = widget.IconButtonWidget()
        layout.add_child(self._play_pause_button)
        self._play_pause_button.icon_name = "metronome" # $TODO

        layout.add_padding(self._constants.MENU_PADDING)

        self._stop_button = widget.IconButtonWidget()
        layout.add_child(self._stop_button)
        self._stop_button.icon_name = "metronome" # $TODO

        layout.add_padding(self._constants.MENU_PADDING)

        self._metronome_button = widget.IconButtonWidget()
        layout.add_child(self._metronome_button)
        self._metronome_button.icon_name = "metronome" # $TODO

        layout.add_padding(0.0, weight = 1.0)

        self._undo_button = widget.IconButtonWidget()
        layout.add_child(self._undo_button)
        self._undo_button.icon_name = "metronome" # $TODO

        layout.add_padding(self._constants.MENU_PADDING)

        self._redo_button = widget.IconButtonWidget()
        layout.add_child(self._redo_button)
        self._redo_button.icon_name = "metronome" # $TODO

        return background