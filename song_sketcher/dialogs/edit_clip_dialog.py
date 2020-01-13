from song_sketcher import constants
from song_sketcher import drawing
from song_sketcher import engine
import math
from song_sketcher import modal_dialog
from song_sketcher import settings
from song_sketcher import song_timing
from song_sketcher import timer
from song_sketcher.units import *
from song_sketcher import waveform_texture
from song_sketcher import widget

_LATEST_WAVEFORM_SAMPLES_COUNT = 128
_MAX_WAVEFORM_SAMPLES = 1024

class EditClipDialog:
    # on_accept_func takes name, sample_count, start_sample_index, end_sample_index, measure_count, engine_clip as arguments
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

        name_layout = widget.HStackedLayoutWidget()
        layout.add_child(name_layout, horizontal_placement = widget.HorizontalPlacement.CENTER)

        name_title = widget.TextWidget()
        name_layout.add_child(name_title, horizontal_placement = widget.HorizontalPlacement.RIGHT)
        name_title.text = "Name:"
        name_title.horizontal_alignment = drawing.HorizontalAlignment.RIGHT
        name_title.vertical_alignment = drawing.VerticalAlignment.MIDDLE

        name_layout.add_padding(points(12.0))

        self._name = widget.InputWidget()
        name_layout.add_child(self._name)
        if clip is not None:
            self._name.text = clip.name

        layout.add_padding(points(12.0))

        self._waveform_viewer = WaveformWidget()
        layout.add_child(self._waveform_viewer)
        self._waveform_viewer.desired_width = inches(8.0)
        self._waveform_viewer.desired_height = inches(2.0)
        if clip is None:
            self._waveform_viewer.set_waveform_samples([0.0])
        else:
            self._waveform_viewer.set_waveform_samples(engine.get_clip_samples(clip.engine_clip, _MAX_WAVEFORM_SAMPLES))

        layout.add_padding(points(12.0))

        buttons_layout = widget.HStackedLayoutWidget()
        layout.add_child(buttons_layout)

        if clip is None:
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
        self._stop_button.set_enabled(clip is not None, False) # $TODO you can click this anytime and it returns the cursor to the start

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

        self._destroy_func = modal_dialog.show_modal_dialog(stack_widget, layout)

    def _record(self):
        assert self._clip is None
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

            self._waveform_viewer.set_waveform_samples(engine.get_clip_samples(self._engine_clip, _MAX_WAVEFORM_SAMPLES))

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

            sample_count = engine.get_clip_sample_count(engine_clip)
            engine.playback_builder_begin()
            engine.playback_builder_add_clip(engine_clip, 0, sample_count, 0)
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
                0) # $TODO start index
            self._is_playing = True
            self._playback_updater = timer.Updater(self._playback_update)

            if self._clip is None:
                self._record_button.set_enabled(False)
            self._play_pause_button.icon = "pause"
        else:
            engine.stop_playback()
            self._is_playing = False
            self._playback_updater.cancel()
            self._playback_updater = None

            if self._clip is None:
                self._record_button.set_enabled(True)
            self._play_pause_button.icon = "play"

    def _stop(self):
        if self._is_playing:
            self._play_pause()
            assert not self._is_playing
            # $TODO restore cursor back to last clicked mouse position

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

        if self._clip is None:
            if self._engine_clip is None:
                sample_count = 0
                start_sample_index = 0
                end_sample_index = 0
                measure_count = 0
            else:
                sample_count = engine.get_clip_sample_count(self._engine_clip)
                start_sample_index = 0
                end_sample_index = sample_count
                measure_count = song_timing.get_measure_count(
                    self._project.sample_rate,
                    self._project.beats_per_minute,
                    self._project.beats_per_measure,
                    sample_count)
                measure_count = max(0, math.ceil(measure_count) - 1) # Remove the intro measure
                if measure_count > 1:
                    measure_count -= 1 # Make the last measure into the outro
        else:
            sample_count = self._clip.sample_count
            start_sample_index = self._clip.start_sample_index
            end_sample_index = self._clip.end_sample_index
            measure_count = self._clip.measure_count

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

        self._destroy_func()
        self._on_accept_func(name, sample_count, start_sample_index, end_sample_index, measure_count, self._engine_clip)

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

    def _recording_update(self, dt):
        self._waveform_viewer.set_waveform_samples(engine.get_latest_recorded_samples(_LATEST_WAVEFORM_SAMPLES_COUNT))

    def _playback_update(self, dt):
        # $TODO update time bar graphics

        engine_clip = self._engine_clip
        if engine_clip is None:
            assert self._clip is not None
            engine_clip = self._clip.engine_clip

        assert engine_clip is not None

        # Stop playback if we reach the end
        if engine.get_playback_sample_index() >= engine.get_clip_sample_count(engine_clip):
            self._stop()

class WaveformWidget(widget.WidgetWithSize):
    _BACKGROUND_COLOR = (0.25, 0.25, 0.25, 1.0)
    _WAVEFORM_COLOR = (0.25, 0.25, 1.0, 1.0)

    def __init__(self):
        super().__init__()
        self.desired_width = 0.0
        self.desired_height = 0.0
        self._waveform_texture = None
        self._sample_count = 0

    def destroy(self):
        if self._waveform_texture is not None:
            self._waveform_texture.destroy()
        super().destroy()

    def set_waveform_samples(self, samples):
        if len(samples) == 0:
            samples = [0.0]
        if self._waveform_texture is None or len(samples) != self._sample_count:
            if self._waveform_texture is not None:
                self._waveform_texture.destroy()
            self._waveform_texture = waveform_texture.WaveformTexture(samples = samples)
        else:
            self._waveform_texture.update_samples(samples)
        self._sample_count = len(samples)

    def process_event(self, event):
        return False

    def get_desired_size(self):
        return (self.desired_width, self.desired_height)

    def draw_visible(self, parent_transform):
        transform = parent_transform * self.get_transform()
        with transform:
            drawing.draw_waveform(
                0.0,
                0.0,
                self.width.value,
                self.height.value,
                self._waveform_texture.waveform_texture,
                self._BACKGROUND_COLOR,
                self._WAVEFORM_COLOR,
                border_thickness = points(2.0),
                border_color = constants.Color.BLACK)
