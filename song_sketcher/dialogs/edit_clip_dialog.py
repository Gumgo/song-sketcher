from enum import Enum

from song_sketcher import constants
from song_sketcher import drawing
from song_sketcher import engine
import math
from song_sketcher import modal_dialog
from song_sketcher import project
from song_sketcher import settings
from song_sketcher import song_timing
from song_sketcher import time_bar
from song_sketcher import timer
from song_sketcher.units import *
from song_sketcher import waveform_texture
from song_sketcher import widget
from song_sketcher import widget_event

_LATEST_WAVEFORM_SAMPLES_COUNT = 128
_MAX_WAVEFORM_SAMPLES = 1024

# $TODO improve the waveform texture to be a 2D texture containing (min,max) sample height instead of just one value

class EditClipDialog:
    # on_accept_func takes a clip as its argument
    def __init__(self, stack_widget, project, clip, on_accept_func, on_delete_func):
        self._stack_widget = stack_widget
        self._project = project
        self._clip = clip
        self._on_accept_func = on_accept_func
        self._on_delete_func = on_delete_func

        layout = widget.VStackedLayoutWidget()

        title = widget.TextWidget()
        if clip is None:
            title.text = "Record clip"
        else:
            title.text = "Edit clip"
        title.size.value = points(20.0)
        title.horizontal_alignment = drawing.HorizontalAlignment.CENTER
        title.vertical_alignment = drawing.VerticalAlignment.MIDDLE
        layout.add_child(title)

        layout.add_padding(points(12.0))

        name_gain_layout = widget.HStackedLayoutWidget()
        layout.add_child(name_gain_layout, horizontal_placement = widget.HorizontalPlacement.CENTER)

        name_title = widget.TextWidget()
        name_gain_layout.add_child(name_title, horizontal_placement = widget.HorizontalPlacement.RIGHT)
        name_title.text = "Name:"
        name_title.horizontal_alignment = drawing.HorizontalAlignment.RIGHT
        name_title.vertical_alignment = drawing.VerticalAlignment.MIDDLE

        name_gain_layout.add_padding(points(4.0))

        self._name = widget.InputWidget()
        name_gain_layout.add_child(self._name)
        if clip is not None:
            self._name.text = clip.name

        name_gain_layout.add_padding(points(4.0))

        self._gain_spinner = widget.SpinnerWidget()
        name_gain_layout.add_child(self._gain_spinner)
        self._gain_spinner.min_value = 0.0
        self._gain_spinner.max_value = 1.0
        self._gain_spinner.value = 1.0 if clip is None else clip.gain
        self._gain_spinner.decimals = 2

        layout.add_padding(points(12.0))

        self._time_bar = time_bar.TimeBarWidget()
        layout.add_child(self._time_bar, horizontal_placement = widget.HorizontalPlacement.CENTER)
        self._time_bar.desired_width = inches(8.0) - _get_waveform_border_thickness() * 2.0
        self._time_bar.desired_height = points(20.0)
        self._time_bar.on_sample_changed_func = self._on_time_bar_sample_changed

        layout.add_padding(points(4.0))

        self._waveform_viewer = WaveformWidget()
        layout.add_child(self._waveform_viewer)
        self._waveform_viewer.desired_width = inches(8.0)
        self._waveform_viewer.desired_height = inches(2.0)
        if clip is None:
            self._waveform_viewer.set_waveform_samples([0.0])
            self._waveform_viewer.sample_count = 0
            self._waveform_viewer.enabled = False
        else:
            self._waveform_viewer.set_waveform_samples(engine.get_clip_samples(clip.engine_clip, _MAX_WAVEFORM_SAMPLES))
            self._waveform_viewer.sample_count = clip.sample_count
            self._waveform_viewer.start_sample_index = clip.start_sample_index
            self._waveform_viewer.end_sample_index = clip.end_sample_index

        layout.add_padding(points(12.0))

        measures_layout = widget.HStackedLayoutWidget()
        layout.add_child(measures_layout)

        self._intro_checkbox = widget.CheckboxWidget()
        measures_layout.add_child(self._intro_checkbox, vertical_placement = widget.VerticalPlacement.MIDDLE)
        self._intro_checkbox.set_checked(True if self._clip is None else self._clip.has_intro, False)
        self._intro_checkbox.action_func = self._update_measures_text

        measures_layout.add_padding(points(4.0))

        intro_text = widget.TextWidget()
        measures_layout.add_child(intro_text, horizontal_placement = widget.HorizontalPlacement.LEFT, vertical_placement = widget.VerticalPlacement.MIDDLE)
        intro_text.text = "Intro measure"
        intro_text.horizontal_alignment = drawing.HorizontalAlignment.LEFT
        intro_text.vertical_alignment = drawing.VerticalAlignment.MIDDLE

        self._measures_text = widget.TextWidget()
        measures_layout.add_child(self._measures_text, weight = 1.0, vertical_placement = widget.VerticalPlacement.MIDDLE)
        self._measures_text.horizontal_alignment = drawing.HorizontalAlignment.CENTER
        self._measures_text.vertical_alignment = drawing.VerticalAlignment.MIDDLE

        outro_text = widget.TextWidget()
        measures_layout.add_child(outro_text, horizontal_placement = widget.HorizontalPlacement.RIGHT, vertical_placement = widget.VerticalPlacement.MIDDLE)
        outro_text.text = "Outro measure"
        outro_text.horizontal_alignment = drawing.HorizontalAlignment.RIGHT
        outro_text.vertical_alignment = drawing.VerticalAlignment.MIDDLE

        measures_layout.add_padding(points(4.0))

        self._outro_checkbox = widget.CheckboxWidget()
        measures_layout.add_child(self._outro_checkbox, vertical_placement = widget.VerticalPlacement.MIDDLE)
        self._outro_checkbox.set_checked(True if self._clip is None else self._clip.has_outro, False)
        self._outro_checkbox.action_func = self._update_measures_text

        layout.add_padding(points(12.0))

        buttons_layout = widget.HStackedLayoutWidget()
        layout.add_child(buttons_layout)

        self._record_button = widget.IconButtonWidget()
        buttons_layout.add_child(self._record_button)
        self._record_button.color = (0.75, 0.0, 0.0, 1.0)
        self._record_button.icon_name = "record"
        self._record_button.action_func = self._record

        buttons_layout.add_padding(points(4.0))

        self._play_pause_button = widget.IconButtonWidget()
        buttons_layout.add_child(self._play_pause_button)
        self._play_pause_button.icon_name = "play"
        self._play_pause_button.action_func = self._play_pause
        self._play_pause_button.set_enabled(clip is not None, False)

        buttons_layout.add_padding(points(4.0))

        self._stop_button = widget.IconButtonWidget()
        buttons_layout.add_child(self._stop_button)
        self._stop_button.icon_name = "stop"
        self._stop_button.action_func = self._stop
        self._stop_button.set_enabled(clip is not None, False)

        buttons_layout.add_padding(points(4.0))

        self._metronome_button = widget.IconButtonWidget()
        buttons_layout.add_child(self._metronome_button)
        self._metronome_button.icon_name = self._get_metronome_icon()
        self._metronome_button.action_func = self._toggle_metronome

        if clip is not None:
            buttons_layout.add_padding(points(4.0))

            self._delete_button = widget.IconButtonWidget()
            buttons_layout.add_child(self._delete_button)
            self._delete_button.icon_name = "delete"
            self._delete_button.action_func = self._delete

        buttons_layout.add_padding(points(4.0), weight = 1.0)

        self._accept_button = widget.IconButtonWidget()
        buttons_layout.add_child(self._accept_button)
        self._accept_button.color = constants.Ui.ACCEPT_BUTTON_COLOR
        self._accept_button.icon_name = "accept"
        self._accept_button.action_func = self._accept

        buttons_layout.add_padding(points(4.0))

        self._reject_button = widget.IconButtonWidget()
        buttons_layout.add_child(self._reject_button)
        self._reject_button.color = constants.Ui.REJECT_BUTTON_COLOR
        self._reject_button.icon_name = "reject"
        self._reject_button.action_func = self._reject

        self._engine_clip = None
        self._is_recording = False
        self._recording_updater = None
        self._is_playing = False
        self._playback_updater = None
        self._last_clicked_sample_index = None

        self._update_time_bar()
        self._update_measures_text()

        self._destroy_func = modal_dialog.show_modal_dialog(stack_widget, layout)

    def _record(self):
        if not self._is_recording:
            s = settings.get()
            if s.input_device_index is None:
                modal_dialog.show_simple_modal_dialog(
                    self._stack_widget,
                    "Input device not set",
                    "The input device must be set before recording.",
                    ["OK"],
                    None)
                return
            if s.output_device_index is None:
                modal_dialog.show_simple_modal_dialog(
                    self._stack_widget,
                    "Output device not set",
                    "The output device must be set before recording.",
                    ["OK"],
                    None)
                return

            if self._engine_clip is not None:
                engine.delete_clip(self._engine_clip)

            if s.recording_metronome_enabled:
                samples_per_beat = song_timing.get_samples_per_beat(
                    self._project.sample_rate,
                    self._project.beats_per_minute)
                engine.set_metronome_samples_per_beat(samples_per_beat)
            else:
                engine.set_metronome_samples_per_beat(0.0)

            self._engine_clip = engine.start_recording_clip(
                s.input_device_index,
                s.output_device_index,
                s.frames_per_buffer)
            self._is_recording = True
            self._recording_updater = timer.Updater(self._recording_update)

            self._record_button.icon_name = "stop"
            self._play_pause_button.set_enabled(False)
            self._stop_button.set_enabled(False)
            self._accept_button.set_enabled(False)
            self._reject_button.set_enabled(False)
            self._intro_checkbox.set_enabled(False)
            self._outro_checkbox.set_enabled(False)
            self._gain_spinner.set_enabled(False)
            self._update_time_bar()

            self._waveform_viewer.enabled = False

            self._update_measures_text()
        else:
            engine.stop_recording_clip()
            self._is_recording = False
            self._recording_updater.cancel()
            self._recording_updater = None

            self._record_button.icon_name = "record"
            self._play_pause_button.set_enabled(True)
            self._stop_button.set_enabled(True)
            self._accept_button.set_enabled(True)
            self._reject_button.set_enabled(True)
            self._intro_checkbox.set_enabled(True)
            self._outro_checkbox.set_enabled(True)
            self._gain_spinner.set_enabled(True)
            self._update_time_bar()

            self._waveform_viewer.set_waveform_samples(engine.get_clip_samples(self._engine_clip, _MAX_WAVEFORM_SAMPLES))
            self._waveform_viewer.sample_count = engine.get_clip_sample_count(self._engine_clip)
            self._waveform_viewer.start_sample_index = 0
            self._waveform_viewer.end_sample_index = self._waveform_viewer.sample_count
            self._waveform_viewer.enabled = True

            self._update_measures_text()

    def _play_pause(self):
        if not self._is_playing:
            engine_clip = self._engine_clip
            if engine_clip is None:
                assert self._clip is not None
                engine_clip = self._clip.engine_clip

            assert engine_clip is not None

            s = settings.get()
            if s.output_device_index is None:
                modal_dialog.show_simple_modal_dialog(
                    self._stack_widget,
                    "Output device not set",
                    "The output device must be set before playback.",
                    ["OK"],
                    None)
                return

            start_sample_index = self._waveform_viewer.start_sample_index
            end_sample_index = self._waveform_viewer.end_sample_index
            gain = self._gain_spinner.value
            engine.playback_builder_begin()
            engine.playback_builder_add_clip(engine_clip, start_sample_index, end_sample_index, start_sample_index, gain)
            engine.playback_builder_finalize()

            if s.recording_metronome_enabled:
                samples_per_beat = song_timing.get_samples_per_beat(
                    self._project.sample_rate,
                    self._project.beats_per_minute)
                engine.set_metronome_samples_per_beat(samples_per_beat)
            else:
                engine.set_metronome_samples_per_beat(0.0)

            engine.start_playback(
                s.output_device_index,
                s.frames_per_buffer,
                int(self._time_bar.sample))
            self._is_playing = True
            self._playback_updater = timer.Updater(self._playback_update)

            self._record_button.set_enabled(False)
            self._play_pause_button.icon_name = "pause"
        else:
            engine.stop_playback()
            self._is_playing = False
            self._playback_updater.cancel()
            self._playback_updater = None

            self._record_button.set_enabled(True)
            self._play_pause_button.icon_name = "play"

    def _stop(self):
        if self._is_playing:
            self._play_pause()
            assert not self._is_playing

        if self._time_bar.sample == self._last_clicked_sample_index:
            self._time_bar.sample = 0.0
            self._last_clicked_sample_index = None
        else:
            self._time_bar.sample = self._last_clicked_sample_index or 0.0

    def _get_metronome_icon(self):
        return "metronome" if settings.get().recording_metronome_enabled else "metronome_disabled"

    def _toggle_metronome(self):
        s = settings.get()
        s.recording_metronome_enabled = not s.recording_metronome_enabled
        if s.recording_metronome_enabled:
            samples_per_beat = song_timing.get_samples_per_beat(
                self._project.sample_rate,
                self._project.beats_per_minute)
            engine.set_metronome_samples_per_beat(samples_per_beat)
        else:
            engine.set_metronome_samples_per_beat(0.0)
        self._metronome_button.icon_name = self._get_metronome_icon()

    def _accept(self):
        assert not self._is_recording
        if self._is_playing:
            engine.stop_playback()
            self._is_playing = False
            self._playback_updater.cancel()
            self._playback_updater = None

        name = self._name.text.strip()
        if len(name) == 0:
            modal_dialog.show_simple_modal_dialog(
                self._stack_widget,
                "Invalid name",
                "The clip name cannot be empty.",
                ["OK"],
                None)
            return

        sample_count = self._waveform_viewer.sample_count
        start_sample_index = self._waveform_viewer.start_sample_index
        end_sample_index = self._waveform_viewer.end_sample_index
        measure_count = self._calculate_measure_count(sample_count)
        has_intro = self._intro_checkbox.checked
        has_outro = self._outro_checkbox.checked
        gain = self._gain_spinner.value

        if sample_count == 0:
            modal_dialog.show_simple_modal_dialog(
                self._stack_widget,
                "Empty clip",
                "No clip data has been recorded.",
                ["OK"],
                None)
            return

        if measure_count == 0:
            modal_dialog.show_simple_modal_dialog(
                self._stack_widget,
                "Clip is too short",
                "The clip must be at least one measure long, not including the intro and outro.",
                ["OK"],
                None)
            return

        if self._clip is not None and measure_count != self._clip.measure_count:
            modal_dialog.show_simple_modal_dialog(
                self._stack_widget,
                "Measure count changed",
                "The measure count must not change when re-recording a clip.",
                ["OK"],
                None)
            return

        edited_clip = project.Clip()
        edited_clip.name = name
        edited_clip.sample_count = sample_count
        edited_clip.start_sample_index = start_sample_index
        edited_clip.end_sample_index = end_sample_index
        edited_clip.measure_count = measure_count
        edited_clip.has_intro = has_intro
        edited_clip.has_outro = has_outro
        edited_clip.gain = gain
        if self._engine_clip is not None:
            edited_clip.engine_clip = self._engine_clip
        else:
            # We would have already returned if both the engine clip and the clip were None
            assert self._clip is not None
            edited_clip.engine_clip = self._clip.engine_clip

        self._destroy_func()
        self._on_accept_func(edited_clip)

    def _delete(self):
        assert not self._is_recording
        if self._is_playing:
            engine.stop_playback()
            self._is_playing = False
            self._playback_updater.cancel()
            self._playback_updater = None

        self._destroy_func()
        self._on_delete_func()

    def _reject(self):
        assert not self._is_recording
        if self._is_playing:
            engine.stop_playback()
            self._is_playing = False
            self._playback_updater.cancel()
            self._playback_updater = None

        if self._engine_clip is not None:
            engine.delete_clip(self._engine_clip)

        self._destroy_func()

    def _calculate_measure_count(self, sample_count):
        measure_count = math.ceil(
            song_timing.get_measure_count(
                self._project.sample_rate,
                self._project.beats_per_minute,
                self._project.beats_per_measure,
                sample_count))
        if self._intro_checkbox.checked:
            measure_count = max(0, measure_count - 1)
        if self._outro_checkbox.checked:
            measure_count = max(0, measure_count - 1)
        return measure_count

    def _recording_update(self, dt):
        self._waveform_viewer.set_waveform_samples(engine.get_latest_recorded_samples(_LATEST_WAVEFORM_SAMPLES_COUNT))
        self._waveform_viewer.sample_count = 0
        self._waveform_viewer.start_sample_index = 0
        self._waveform_viewer.end_sample_index = 0

        self._update_measures_text()

    def _playback_update(self, dt):
        playback_sample_index = engine.get_playback_sample_index()
        self._time_bar.sample = playback_sample_index

        engine_clip = self._engine_clip
        if engine_clip is None:
            assert self._clip is not None
            engine_clip = self._clip.engine_clip

        assert engine_clip is not None

        # Stop playback if we reach the end
        if playback_sample_index >= engine.get_clip_sample_count(engine_clip):
            self._stop()

    def _update_time_bar(self):
        if self._is_recording or (self._engine_clip is None and self._clip is None):
            self._time_bar.enabled = False
            self._time_bar.sample = None
            self._last_clicked_sample_index = None
        else:
            self._time_bar.enabled = True

            engine_clip = self._engine_clip
            if engine_clip is None:
                assert self._clip is not None
                engine_clip = self._clip.engine_clip

            sample_count = engine.get_clip_sample_count(engine_clip)
            self._time_bar.end_sample = float(sample_count)
            self._time_bar.max_sample = float(sample_count)
            if self._time_bar.sample is None:
                self._time_bar.sample = 0.0

    def _update_measures_text(self):
        if self._is_recording:
            sample_count = engine.get_recorded_sample_count()
        else:
            sample_count = self._waveform_viewer.sample_count
        measure_count = self._calculate_measure_count(sample_count)
        self._measures_text.text = "Measures: {}".format(measure_count)

        if measure_count == 0 or (self._clip is not None and measure_count != self._clip.measure_count):
            self._measures_text.color.value = (0.75, 0.0, 0.0, 1.0)
        else:
            self._measures_text.color.value = constants.Color.BLACK

    def _on_time_bar_sample_changed(self):
        sample_index = self._time_bar.sample
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

def _get_waveform_border_thickness():
    return points(2.0)

class WaveformWidget(widget.WidgetWithSize):
    class _EditMode(Enum):
        START_SAMPLE_INDEX = 0
        END_SAMPLE_INDEX = 1

    _BACKGROUND_COLOR = (0.5, 0.5, 0.5, 1.0)
    _DISABLED_BACKGROUND_COLOR = constants.darken_color(_BACKGROUND_COLOR, 0.5)
    _WAVEFORM_COLOR = (0.25, 0.25, 1.0, 1.0)
    _DISABLED_WAVEFORM_COLOR = constants.darken_color(_WAVEFORM_COLOR, 0.5)

    def __init__(self):
        super().__init__()
        self.desired_width = 0.0
        self.desired_height = 0.0
        self.start_sample_index = 0
        self.end_sample_index = 0
        self._enabled = True
        self._edit_mode = None
        self._waveform_texture = None
        self._displayed_sample_count = 0

    @property
    def enabled(self):
        return self._enabled

    @enabled.setter
    def enabled(self, enabled):
        self._enabled = enabled
        if not self._enabled:
            self._edit_mode = None
            self.release_capture()
            self.release_focus()

    def destroy(self):
        if self._waveform_texture is not None:
            self._waveform_texture.destroy()
        super().destroy()

    def set_waveform_samples(self, samples):
        if len(samples) == 0:
            samples = [0.0]
        if self._waveform_texture is None or len(samples) != self._displayed_sample_count:
            if self._waveform_texture is not None:
                self._waveform_texture.destroy()
            self._waveform_texture = waveform_texture.WaveformTexture(samples = samples)
        else:
            self._waveform_texture.update_samples(samples)
        self._displayed_sample_count = len(samples)

    def process_event(self, event):
        if not self._enabled:
            return False

        result = False
        if isinstance(event, widget_event.MouseEvent):
            x, y = self.get_full_transform().inverse().transform_point((event.x, event.y))
            border_thickness = _get_waveform_border_thickness()
            width_without_border = self.width.value - border_thickness * 2.0

            if event.button is widget_event.MouseButton.LEFT:
                if event.event_type is widget_event.MouseEventType.PRESS:
                    start_x = border_thickness + (self.start_sample_index / self.sample_count) * width_without_border
                    end_x = border_thickness + (self.end_sample_index / self.sample_count) * width_without_border

                    drag_threshold = points(20.0)
                    closest_dist = float("inf")
                    start_dist = abs(x - start_x)
                    end_dist = abs(x - end_x)

                    if start_dist <= drag_threshold and start_dist < closest_dist:
                        closest_dist = start_dist
                        self._edit_mode = self._EditMode.START_SAMPLE_INDEX

                    if end_dist <= drag_threshold and end_dist < closest_dist:
                        closest_dist = end_dist
                        self._edit_mode = self._EditMode.END_SAMPLE_INDEX

                    self.capture()
                    self.focus()
                    result = True
                elif event.event_type is widget_event.MouseEventType.RELEASE:
                    self.release_capture()
                    self._edit_mode = None
                    result = True
            elif event.event_type is widget_event.MouseEventType.MOVE:
                result = True
                sample_ratio = (x - border_thickness) / width_without_border
                sample_index = min(max(round(self.sample_count * sample_ratio), 0), self.sample_count)
                if self._edit_mode is self._EditMode.START_SAMPLE_INDEX:
                    self.start_sample_index = min(sample_index, self.end_sample_index)
                elif self._edit_mode is self._EditMode.END_SAMPLE_INDEX:
                    self.end_sample_index = max(sample_index, self.start_sample_index)

        return result

    def get_desired_size(self):
        return (self.desired_width, self.desired_height)

    def draw_visible(self, parent_transform):
        transform = parent_transform * self.get_transform()
        with transform:
            def draw_waveform(background_color, color):
                drawing.draw_waveform(
                    0.0,
                    0.0,
                    self.width.value,
                    self.height.value,
                    self._waveform_texture.waveform_texture,
                    background_color,
                    color,
                    border_thickness = _get_waveform_border_thickness(),
                    border_color = constants.Color.BLACK)

            pad = 10.0
            active_start_x = -pad
            active_end_x = self.width.value + pad

            border_thickness = _get_waveform_border_thickness()
            width_without_border = self.width.value - border_thickness * 2.0

            if self.start_sample_index > 0:
                active_start_x = border_thickness + (self.start_sample_index / self.sample_count) * width_without_border
                with drawing.scissor(-pad, -pad, active_start_x, self.height.value + pad, transform = transform):
                    draw_waveform(self._DISABLED_BACKGROUND_COLOR, self._DISABLED_WAVEFORM_COLOR)

            if self.end_sample_index < self.sample_count:
                active_end_x = border_thickness + (self.end_sample_index / self.sample_count) * width_without_border
                with drawing.scissor(active_end_x, -pad, self.width.value + pad, self.height.value + pad, transform = transform):
                    draw_waveform(self._DISABLED_BACKGROUND_COLOR, self._DISABLED_WAVEFORM_COLOR)

            with drawing.scissor(active_start_x, -pad, active_end_x, self.height.value + pad, transform = transform):
                draw_waveform(self._BACKGROUND_COLOR, self._WAVEFORM_COLOR)
