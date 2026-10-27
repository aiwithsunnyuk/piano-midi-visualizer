import os
import subprocess


def extract_audio_from_video(video_path: str, output_wav_path: str) -> str:
    """Extracts 16kHz mono WAV audio from a video using ffmpeg."""
    command = [
        "ffmpeg", "-y", "-i", video_path,
        "-ac", "1", "-ar", "16000",
        output_wav_path
    ]
    subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return output_wav_path


def convert_audio_to_midi(audio_path: str, output_dir: str):
    """Generates standard MIDI (.mid) from polyphonic audio using basic-pitch."""
    try:
        from basic_pitch import ICASSP_2022_MODEL_PATH
        from basic_pitch.inference import predict_and_save
    except ImportError:
        raise ImportError(
            "basic-pitch is not installed. Ensure 'basic-pitch' is listed in requirements.txt."
        )

    base_name = os.path.splitext(os.path.basename(audio_path))[0]
    existing_midi_path = os.path.join(output_dir, f"{base_name}_basic_pitch.mid")
    if os.path.exists(existing_midi_path):
        os.remove(existing_midi_path)

    predict_and_save(
        audio_path_list=[audio_path],
        output_directory=output_dir,
        save_midi=True,
        sonify_midi=False,
        save_model_outputs=False,
        save_notes=False,
        model_or_model_path=ICASSP_2022_MODEL_PATH
    )