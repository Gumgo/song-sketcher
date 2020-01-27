from song_sketcher import constants
from song_sketcher.dialogs import load_project_dialog
from song_sketcher.dialogs import new_project_dialog
from song_sketcher.dialogs import save_project_as_dialog
from song_sketcher.dialogs import settings_dialog
from song_sketcher import drawing
from song_sketcher import engine
from song_sketcher import history_manager
from song_sketcher import library
from song_sketcher import modal_dialog
from song_sketcher import project
from song_sketcher import project_manager
from song_sketcher import settings
from song_sketcher import song_timing
from song_sketcher import timeline
from song_sketcher import timer
from song_sketcher.units import *
from song_sketcher import widget
from song_sketcher import widget_manager

class Constants:
    # Don't make this static because we can't initialize some values (e.g. points) until units are initialized
    def __init__(self):
        self.MENU_PADDING = points(12.0)

        self.DIVIDER_SIZE = points(20.0)

class Editor:
    def __init__(self):
        self._project_name = None
        self._project = None
        self._history_manager = None
        self._quit = False

        self._constants = Constants()

        self._root_stack_widget = widget.StackWidget()
        widget_manager.get().set_root_widget(self._root_stack_widget)

        self._root_background = widget.BackgroundWidget()
        self._root_stack_widget.push_child(self._root_background)
        self._root_background.color.value = constants.Ui.PANEL_COLOR

        self._root_layout = widget.HStackedLayoutWidget()
        self._root_background.set_child(self._root_layout)

        self._file_menu_widget = self._build_file_menu_widget()

        # Holds all project-related widgets so we can easily clear the whole list
        self._project_widgets = None
        self._library = None
        self._timeline = None

        # Playback-related fields
        self._is_playing = False
        self._playback_updater = None

        # This will set up the appropriate "no project loaded" layout
        self._close_project()

        self._update_controls_enabled(False)

    def shutdown(self):
        pass

    def update(self, dt):
        pass

    def should_quit(self):
        return self._quit

    def request_quit(self):
        if self._is_playing:
            self._stop()

        def on_save_complete(success):
            if success:
                self._quit = True

        self._ask_to_save_pending_changes(on_save_complete)

    def _build_file_menu_widget(self):
        background = widget.BackgroundWidget()
        background.color.value = constants.Ui.MENU_COLOR
        background.border_thickness.value = points(2.0)
        background.border_color.value = constants.darken_color(constants.Ui.MENU_COLOR, 0.5)

        layout = widget.VStackedLayoutWidget()
        background.set_child(layout)
        layout.margin = self._constants.MENU_PADDING

        self._new_project_button = widget.IconButtonWidget()
        layout.add_child(self._new_project_button)
        self._new_project_button.icon_name = "new"
        self._new_project_button.action_func = self._new_project_button_clicked

        layout.add_padding(self._constants.MENU_PADDING)

        self._load_project_button = widget.IconButtonWidget()
        layout.add_child(self._load_project_button)
        self._load_project_button.icon_name = "load"
        self._load_project_button.action_func = self._load_project_button_clicked

        layout.add_padding(self._constants.MENU_PADDING)

        self._save_project_button = widget.IconButtonWidget()
        layout.add_child(self._save_project_button)
        self._save_project_button.icon_name = "save"
        self._save_project_button.action_func = self._save_project_button_clicked

        layout.add_padding(self._constants.MENU_PADDING)

        self._save_project_as_button = widget.IconButtonWidget()
        layout.add_child(self._save_project_as_button)
        self._save_project_as_button.icon_name = "save_as"
        self._save_project_as_button.action_func = self._save_project_as_button_clicked

        layout.add_padding(self._constants.MENU_PADDING)

        self._settings_button = widget.IconButtonWidget()
        layout.add_child(self._settings_button)
        self._settings_button.icon_name = "settings"
        self._settings_button.action_func = self._settings_button_clicked

        layout.add_padding(0.0, weight = 1.0)

        self._quit_button = widget.IconButtonWidget()
        layout.add_child(self._quit_button)
        self._quit_button.icon_name = "quit"
        self._quit_button.action_func = self._quit_button_clicked

        return background

    def _build_project_widgets(self):
        class ProjectWidgets:
            pass
        project_widgets = ProjectWidgets()

        project_widgets.root_layout = widget.HStackedLayoutWidget()

        timeline_library_layout = widget.VStackedLayoutWidget()
        project_widgets.root_layout.add_child(timeline_library_layout, weight = 1.0)

        self._timeline = timeline.Timeline(
            self._root_stack_widget,
            self._project,
            self._history_manager,
            lambda: self._library.selected_clip_id,
            self._on_time_bar_sample_changed)
        timeline_library_layout.add_child(self._timeline.root_layout, weight = 1.0)

        timeline_library_divider = widget.RectangleWidget()
        timeline_library_layout.add_child(timeline_library_divider)
        timeline_library_divider.desired_height = self._constants.DIVIDER_SIZE
        timeline_library_divider.color.value = constants.Ui.MENU_COLOR
        timeline_library_divider.border_thickness.value = points(2.0)
        timeline_library_divider.border_color.value = constants.darken_color(constants.Ui.MENU_COLOR, 0.5)
        timeline_library_divider.left_open = True
        timeline_library_divider.right_open = True

        self._library = library.Library(
            self._root_stack_widget,
            self._project,
            self._history_manager,
            lambda: self._timeline.update_tracks())
        timeline_library_layout.add_child(self._library.root_layout, weight = 1.0)

        edit_menu_widget = self._build_edit_menu_widget(project_widgets)
        project_widgets.root_layout.add_child(edit_menu_widget)

        self._last_clicked_sample_index = None

        return project_widgets

    def _build_edit_menu_widget(self, project_widgets):
        background = widget.BackgroundWidget()
        background.color.value = constants.Ui.MENU_COLOR
        background.border_thickness.value = points(2.0)
        background.border_color.value = constants.darken_color(constants.Ui.MENU_COLOR, 0.5)

        layout = widget.VStackedLayoutWidget()
        background.set_child(layout)
        layout.margin = self._constants.MENU_PADDING

        project_widgets.play_pause_button = widget.IconButtonWidget()
        layout.add_child(project_widgets.play_pause_button)
        project_widgets.play_pause_button.icon_name = "play"
        project_widgets.play_pause_button.action_func = self._play_pause

        layout.add_padding(self._constants.MENU_PADDING)

        project_widgets.stop_button = widget.IconButtonWidget()
        layout.add_child(project_widgets.stop_button)
        project_widgets.stop_button.icon_name = "stop"
        project_widgets.stop_button.action_func = self._stop

        layout.add_padding(self._constants.MENU_PADDING)

        project_widgets.metronome_button = widget.IconButtonWidget()
        layout.add_child(project_widgets.metronome_button)
        project_widgets.metronome_button.icon_name = self._get_metronome_icon()
        project_widgets.metronome_button.action_func = self._toggle_metronome

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
                new_project_dialog.NewProjectDialog(self._root_stack_widget, self._load_project)

        self._ask_to_save_pending_changes(on_save_complete)

    def _load_project_button_clicked(self):
        def on_save_complete(success):
            if success:
                load_project_dialog.LoadProjectDialog(self._root_stack_widget, self._load_project)

        self._ask_to_save_pending_changes(on_save_complete)

    def _save_project_button_clicked(self):
        self._save_project()

    def _save_project_as_button_clicked(self):
        def on_name_chosen(name):
            self._project_name = name
            self._history_manager.clear_save_state()
            self._save_project()

        save_project_as_dialog.SaveProjectAsDialog(self._root_stack_widget, on_name_chosen)

    def _settings_button_clicked(self):
        settings_dialog.SettingsDialog(self._root_stack_widget)

    def _quit_button_clicked(self):
        self.request_quit()

    def _close_project(self):
        if self._history_manager is not None:
            self._history_manager.destroy()
            self._history_manager = None

        if self._project is not None:
            self._project.engine_unload()

        self._project_name = None
        self._project = None

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

        self._update_controls_enabled()

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

        if self._history_manager is not None:
            self._history_manager.destroy()
            self._history_manager = None
        self._history_manager = history_manager.HistoryManager(self._update_controls_enabled)

        if self._project is not None:
            self._project.engine_unload()

        self._project_name = project_name
        self._project = new_project
        self._project.engine_load()

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

        self._update_controls_enabled()
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

    def _play_pause(self):
        if not self._is_playing:
            s = settings.get()
            if s.output_device_index is None:
                modal_dialog.show_simple_modal_dialog(
                    self._root_stack_widget,
                    "Output device not set",
                    "The output device must be set before playback.",
                    ["OK"],
                    None)
                return

            soloed_tracks = set(x for x in self._project.tracks if x.soloed and not x.muted)
            if len(soloed_tracks) > 0:
                active_tracks = [x for x in self._project.tracks if x in soloed_tracks]
            else:
                active_tracks = [x for x in self._project.tracks if not x.muted]

            # Build the playback clip
            engine.playback_builder_begin()

            samples_per_measure = song_timing.get_samples_per_measure(
                self._project.sample_rate,
                self._project.beats_per_minute,
                self._project.beats_per_measure)
            for track in active_tracks:
                for i, clip_id in enumerate(track.measure_clip_ids):
                    if clip_id is not None:
                        clip = self._project.get_clip_by_id(clip_id)
                        measure_index = i
                        if clip.has_intro:
                            measure_index -= 1
                        playback_start_sample_index = round(measure_index * samples_per_measure + clip.start_sample_index)
                        gain = clip.gain * clip.category.gain * track.gain
                        print(("ADD", track, clip, clip.engine_clip))
                        engine.playback_builder_add_clip(
                            clip.engine_clip,
                            clip.start_sample_index,
                            clip.end_sample_index,
                            playback_start_sample_index,
                            gain)

            engine.playback_builder_finalize()

            if s.playback_metronome_enabled:
                samples_per_beat = song_timing.get_samples_per_beat(
                    self._project.sample_rate,
                    self._project.beats_per_minute)
                engine.set_metronome_samples_per_beat(samples_per_beat)
            else:
                engine.set_metronome_samples_per_beat(0.0)

            engine.start_playback(
                s.output_device_index,
                s.frames_per_buffer,
                int(self._timeline.get_playback_sample_index()))
            self._is_playing = True
            self._playback_updater = timer.Updater(self._playback_update)

            self._project_widgets.play_pause_button.icon_name = "pause"
            self._update_controls_enabled()
        else:
            engine.stop_playback()
            self._is_playing = False
            self._playback_updater.cancel()
            self._playback_updater = None

            self._project_widgets.play_pause_button.icon_name = "play"
            self._update_controls_enabled()

    def _on_time_bar_sample_changed(self):
        sample_index = self._timeline.get_playback_sample_index()
        self._last_clicked_sample_index = sample_index

        if self._is_playing:
            s = settings.get()
            assert s.output_device_index is not None # Should not have changed

            # Stopping and starting the stream at the new position should be good enough
            engine.stop_playback()
            engine.start_playback(
                s.output_device_index,
                s.frames_per_buffer,
                int(sample_index))

    def _stop(self):
        if self._is_playing:
            self._play_pause()
            assert not self._is_playing

        if self._timeline.get_playback_sample_index() == self._last_clicked_sample_index:
            self._timeline.set_playback_sample_index(0.0)
            self._last_clicked_sample_index = None
        else:
            self._timeline.set_playback_sample_index(self._last_clicked_sample_index or 0.0)

    def _get_metronome_icon(self):
        return "metronome" if settings.get().playback_metronome_enabled else "metronome_disabled"

    def _toggle_metronome(self):
        s = settings.get()
        s.playback_metronome_enabled = not s.playback_metronome_enabled
        if s.playback_metronome_enabled:
            samples_per_beat = song_timing.get_samples_per_beat(
                self._project.sample_rate,
                self._project.beats_per_minute)
            engine.set_metronome_samples_per_beat(samples_per_beat)
        else:
            engine.set_metronome_samples_per_beat(0.0)
        self._project_widgets.metronome_button.icon_name = self._get_metronome_icon()

    def _undo(self):
        if self._history_manager.can_undo():
            self._history_manager.undo()

    def _redo(self):
        if self._history_manager.can_redo():
            self._history_manager.redo()

    def _update_controls_enabled(self, animate = True):
        can_save_as = self._project is not None
        can_save = can_save_as and self._history_manager.has_unsaved_changes()

        self._new_project_button.set_enabled(not self._is_playing, animate)
        self._load_project_button.set_enabled(not self._is_playing, animate)
        self._save_project_button.set_enabled(not self._is_playing and can_save, animate)
        self._save_project_as_button.set_enabled(not self._is_playing and can_save_as, animate)
        self._settings_button.set_enabled(not self._is_playing, animate)

        if self._project is not None:
            self._library.set_enabled(not self._is_playing)
            self._timeline.set_enabled(not self._is_playing)

            self._project_widgets.undo_button.set_enabled(self._history_manager.can_undo() and not self._is_playing, animate)
            self._project_widgets.redo_button.set_enabled(self._history_manager.can_redo() and not self._is_playing, animate)

    def _playback_update(self, dt):
        playback_sample_index = engine.get_playback_sample_index()
        self._timeline.set_playback_sample_index(playback_sample_index)
        if playback_sample_index >= self._timeline.get_song_length_samples():
            self._stop()
