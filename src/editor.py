import constants
import dialogs.load_project_dialog
import dialogs.new_project_dialog
import dialogs.save_project_as_dialog
import drawing
import history_manager
import library
import modal_dialog
import project
import project_manager
import timeline
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
        self._project_name = None
        self._project = None
        self._history_manager = None

        self._constants = Constants()

        self._root_stack_widget = widget.StackWidget()
        widget_manager.get().set_root_widget(self._root_stack_widget)

        self._root_background = widget.BackgroundWidget()
        self._root_stack_widget.push_child(self._root_background)
        self._root_background.color.value = self._constants.ROOT_BACKGROUND_COLOR

        self._root_layout = widget.HStackedLayoutWidget()
        self._root_background.set_child(self._root_layout)

        self._file_menu_widget = self._build_file_menu_widget()

        # Holds all project-related widgets so we can easily clear the whole list
        self._project_widgets = None
        self._library = None
        self._timeline = None

        # This will set up the appropriate "no project loaded" layout
        self._close_project()

        self._update_buttons_enabled(False)

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
        self._new_project_button.action_func = self._new_project_button_clicked

        layout.add_padding(self._constants.MENU_PADDING)

        self._load_project_button = widget.IconButtonWidget()
        layout.add_child(self._load_project_button)
        self._load_project_button.icon_name = "metronome" # $TODO
        self._load_project_button.action_func = self._load_project_button_clicked

        layout.add_padding(self._constants.MENU_PADDING)

        self._save_project_button = widget.IconButtonWidget()
        layout.add_child(self._save_project_button)
        self._save_project_button.icon_name = "metronome" # $TODO
        self._save_project_button.action_func = self._save_project_button_clicked

        layout.add_padding(self._constants.MENU_PADDING)

        self._save_project_as_button = widget.IconButtonWidget()
        layout.add_child(self._save_project_as_button)
        self._save_project_as_button.icon_name = "metronome" # $TODO
        self._save_project_as_button.action_func = self._save_project_as_button_clicked

        layout.add_padding(self._constants.MENU_PADDING)

        self._settings_button = widget.IconButtonWidget()
        layout.add_child(self._settings_button)
        self._settings_button.icon_name = "metronome" # $TODO
        self._settings_button.action_func = self._settings_button_clicked

        layout.add_padding(0.0, weight = 1.0)

        self._quit_button = widget.IconButtonWidget()
        layout.add_child(self._quit_button)
        self._quit_button.icon_name = "metronome" # $TODO
        self._quit_button.action_func = self._quit_button_clicked

        return background

    def _build_project_widgets(self):
        class ProjectWidgets:
            pass
        project_widgets = ProjectWidgets()

        project_widgets.root_layout = widget.HStackedLayoutWidget()

        timeline_library_layout = widget.VStackedLayoutWidget()
        project_widgets.root_layout.add_child(timeline_library_layout, weight = 1.0)

        timeline_library_layout.add_padding(0.0, weight = 1.0)

        timeline_library_divider = widget.RectangleWidget()
        timeline_library_layout.add_child(timeline_library_divider)
        timeline_library_divider.desired_height = self._constants.DIVIDER_SIZE
        timeline_library_divider.color.value = self._constants.MENU_BACKGROUND_COLOR
        timeline_library_divider.border_thickness.value = points(2.0)
        timeline_library_divider.border_color.value = constants.Color.BLACK
        timeline_library_divider.left_open = True
        timeline_library_divider.right_open = True

        self._library = library.Library(self._root_stack_widget, self._project, self._history_manager)
        timeline_library_layout.add_child(self._library.root_layout, weight = 1.0)

        edit_menu_widget = self._build_edit_menu_widget(project_widgets)
        project_widgets.root_layout.add_child(edit_menu_widget)

        return project_widgets

    def _build_edit_menu_widget(self, project_widgets):
        # $TODO enable/disable buttons based on whether a project is open, also disable/enable the save button based on pending changes
        background = widget.BackgroundWidget()
        background.color.value = self._constants.MENU_BACKGROUND_COLOR
        background.border_thickness.value = points(2.0)
        background.border_color.value = constants.Color.BLACK

        layout = widget.VStackedLayoutWidget()
        background.set_child(layout)
        layout.margin = self._constants.MENU_PADDING

        project_widgets.play_pause_button = widget.IconButtonWidget()
        layout.add_child(project_widgets.play_pause_button)
        project_widgets.play_pause_button.icon_name = "metronome" # $TODO

        layout.add_padding(self._constants.MENU_PADDING)

        project_widgets.stop_button = widget.IconButtonWidget()
        layout.add_child(project_widgets.stop_button)
        project_widgets.stop_button.icon_name = "metronome" # $TODO

        layout.add_padding(self._constants.MENU_PADDING)

        project_widgets.metronome_button = widget.IconButtonWidget()
        layout.add_child(project_widgets.metronome_button)
        project_widgets.metronome_button.icon_name = "metronome" # $TODO

        layout.add_padding(0.0, weight = 1.0)

        project_widgets.undo_button = widget.IconButtonWidget()
        layout.add_child(project_widgets.undo_button)
        project_widgets.undo_button.icon_name = "undo"
        project_widgets.undo_button.action_func = self._undo

        layout.add_padding(self._constants.MENU_PADDING)

        project_widgets.redo_button = widget.IconButtonWidget()
        layout.add_child(project_widgets.redo_button)
        project_widgets.redo_button.icon_name = "redo"
        project_widgets.redo_button.action_func = self._redo

        return background

    def _new_project_button_clicked(self):
        def on_save_complete(success):
            if success:
                dialogs.new_project_dialog.NewProjectDialog(self._root_stack_widget, self._load_project)

        self._ask_to_save_pending_changes(on_save_complete)

    def _load_project_button_clicked(self):
        def on_save_complete(success):
            if success:
                dialogs.load_project_dialog.LoadProjectDialog(self._root_stack_widget, self._load_project)

        self._ask_to_save_pending_changes(on_save_complete)

    def _save_project_button_clicked(self):
        # $TODO enable/disable this based on whether there are pending changes
        self._save_project()

    def _save_project_as_button_clicked(self):
        def on_name_chosen(name):
            self._project_name = name
            self._history_manager.clear_save_state()
            self._save_project()

        dialogs.save_project_as_dialog.SaveProjectAsDialog(self._root_stack_widget, on_name_chosen)

    def _settings_button_clicked(self):
        pass # $TODO

    def _quit_button_clicked(self):
        def on_save_complete(success):
            if success:
                exit(0) # $TODO do better than this

        self._ask_to_save_pending_changes(on_save_complete)

    def _close_project(self):
        self._project_name = None
        self._project = None
        if self._history_manager is not None:
            self._history_manager.destroy()
            self._history_manager = None

        self._root_layout.clear_children()
        if self._project_widgets is not None:
            self._project_widgets.root_layout.destroy()
            self._project_widgets = None

        self._library = None
        self._timeline = None

        self._root_layout.add_child(self._file_menu_widget)
        self._root_layout.add_padding(0.0, weight = 1.0)

        self._root_background.layout_widget(
            (0.0, 0.0),
            widget_manager.get().display_size,
            widget.HorizontalPlacement.FILL,
            widget.VerticalPlacement.FILL)

        self._update_buttons_enabled()

    def _load_project(self, project_name):
        pm = project_manager.get()
        new_project = project.Project()

        try:
            new_project.load(pm.get_project_directory(project_name) / project.PROJECT_FILENAME)
        except:
            modal_dialog.show_simple_modal_dialog(
                self._root_stack_widget,
                "Failed to load project",
                "An error was encountered trying to load the project '{}'.".format(project_name),
                ["OK"],
                None)
            return False

        self._project_name = project_name
        self._project = new_project
        if self._history_manager is not None:
            self._history_manager.destroy()
            self._history_manager = None
        self._history_manager = history_manager.HistoryManager(self._update_buttons_enabled)

        self._root_layout.clear_children()
        if self._project_widgets is not None:
            self._project_widgets.root_layout.destroy()
            self._project_widgets = None

        self._root_layout.add_child(self._file_menu_widget)

        self._project_widgets = self._build_project_widgets()
        self._root_layout.add_child(self._project_widgets.root_layout, weight = 1.0)

        self._root_background.layout_widget(
            (0.0, 0.0),
            widget_manager.get().display_size,
            widget.HorizontalPlacement.FILL,
            widget.VerticalPlacement.FILL)

        self._update_buttons_enabled()

        return True

    def _save_project(self):
        try:
            project_directory = project_manager.get().get_project_directory(self._project_name)
            self._project.save(project_directory / project.PROJECT_FILENAME)
            self._history_manager.save()
            return True
        except:
            modal_dialog.show_simple_modal_dialog(
                self._root_stack_widget,
                "Failed to save project",
                "An error was encountered trying to save the project.",
                ["OK"],
                None)
            return False

    # on_complete_func takes a single success argument
    # Returns True on success: either no current project, no pending changes, user doesn't want to save, or saved successfully
    # Returns False on cancel or failure
    def _ask_to_save_pending_changes(self, on_complete_func):
        if (self._project is None
            or not self._history_manager.has_unsaved_changes()):
            on_complete_func(True)
        else:
            def on_dialog_close(button):
                if button == 0: # Yes
                    on_complete_func(self._save_project())
                elif button == 1: # No
                    on_complete_func(True)
                else:
                    assert button == 2 # Cancel
                    on_complete_func(False)

            modal_dialog.show_simple_modal_dialog(
                self._root_stack_widget,
                "Unsaved pending changes",
                "Would you like to save pending changes before closing the project?",
                ["Yes", "No", "Cancel"],
                on_dialog_close)

    def _undo(self):
        if self._history_manager.can_undo():
            self._history_manager.undo()

    def _redo(self):
        if self._history_manager.can_redo():
            self._history_manager.redo()

    def _update_buttons_enabled(self, animate = True):
        can_save_as = self._project is not None
        can_save = can_save_as and self._history_manager.has_unsaved_changes()
        self._save_project_button.set_enabled(can_save, animate)
        self._save_project_as_button.set_enabled(can_save_as, animate)

        if self._project is not None:
            # $TODO disable all if playing
            self._project_widgets.undo_button.set_enabled(self._history_manager.can_undo(), animate)
            self._project_widgets.redo_button.set_enabled(self._history_manager.can_redo(), animate)
