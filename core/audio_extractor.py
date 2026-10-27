import subprocess
import os
from basic_pitch import ICASSP_2022_MODEL_PATH

def extract_audio_from_video(video_path: str, output_wav_path: str) -> str:
    """Extracts 22050Hz mono WAV audio suitable for MIR analysis."""
    command = [
        "ffmpeg", "-y", "-i", video_path,
        "-vn", "-acodec", "pcm_s16le",
        "-ar", "22050", "-ac", "1", output_wav_path
    ]
    subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    return output_wav_path

def convert_audio_to_midi(audio_path: str, output_dir: str):
    """Generates standard MIDI (.mid) from polyphonic audio."""
    from basic_pitch.inference import predict_and_save, ICASSP_2022_MODEL_PATH

    # Check for existing file and delete it to prevent OSError
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