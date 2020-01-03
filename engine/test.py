import engine
import faulthandler
import time

faulthandler.enable()

print(engine.initialize())

for i in range(engine.get_input_device_count()):
    print(engine.get_input_device_name(i))

for i in range(engine.get_output_device_count()):
    print(engine.get_output_device_name(i))

engine.set_sample_rate(44100)
clip_id = engine.start_recording_clip(
    engine.get_default_input_device_index(),
    engine.get_default_output_device_index(),
    1024)

time.sleep(1.5)
x = engine.get_latest_recorded_samples(100000)
print(x[:50])
print(x[len(x)-50:])
time.sleep(1.5)

engine.stop_recording_clip()
engine.save_clip(clip_id, "test.wav")
engine.delete_clip(clip_id)
new_clip_id = engine.load_clip("test.wav")
engine.save_clip(new_clip_id, "test2.wav")

print(engine.get_clip_sample_count(new_clip_id))
print(engine.get_clip_samples(new_clip_id, 128))
print(len(engine.get_clip_samples(new_clip_id, 0)))

print(engine.shutdown())
