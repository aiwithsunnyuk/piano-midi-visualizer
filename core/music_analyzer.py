import os
import re
import subprocess
import librosa
import numpy as np
import pretty_midi
from music21 import meter, stream, note, chord, duration, musicxml, clef
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

PITCH_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
MAJOR_PROFILE = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
MINOR_PROFILE = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])

def detect_tempo_and_beats(audio_path: str):
    y, sr = librosa.load(audio_path, sr=22050)
    tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
    return float(np.round(tempo, 1)), len(beats)

def detect_scale_and_key(audio_path: str):
    y, sr = librosa.load(audio_path, sr=22050)
    chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
    chroma_avg = np.mean(chroma, axis=1)

    best_score = -np.inf
    best_key = ""
    for i in range(12):
        major_corr = np.corrcoef(chroma_avg, np.roll(MAJOR_PROFILE, i))[0, 1]
        minor_corr = np.corrcoef(chroma_avg, np.roll(MINOR_PROFILE, i))[0, 1]
        if major_corr > best_score:
            best_score = major_corr
            best_key = f"{PITCH_NAMES[i]} Major"
        if minor_corr > best_score:
            best_score = minor_corr
            best_key = f"{PITCH_NAMES[i]} Minor"
    return best_key, chroma_avg

def generate_musicxml_and_pdf(midi_path: str, output_xml_path: str, output_pdf_path: str):
    try:
        pm = pretty_midi.PrettyMIDI(midi_path)
        all_notes = []
        for inst in pm.instruments:
            if not inst.is_drum:
                all_notes.extend(inst.notes)
        if not all_notes:
            return "Error: No notes detected in MIDI.", None

        all_notes.sort(key=lambda n: n.start)
        bpm = pm.estimate_tempo()
        if bpm <= 0:
            bpm = 120.0
        sec_per_quarter = 60.0 / bpm

        part = stream.Part()
        part.append(meter.TimeSignature('4/4'))
        for pm_note in all_notes:
            ql_start = round((pm_note.start / sec_per_quarter) * 4.0) / 4.0
            ql_dur = max(0.25, round(((pm_note.end - pm_note.start) / sec_per_quarter) * 4.0) / 4.0)
            n = note.Note(pm_note.pitch)
            n.duration = duration.Duration(ql_dur)
            n.addLyric(f"{n.pitch.name}{n.pitch.octave}")
            part.insert(ql_start, n)

        clean_part = part.makeMeasures(inPlace=False)
        final_score = stream.Score([clean_part])
        exporter = musicxml.m21ToXml.GeneralObjectExporter()
        xml_bytes = exporter.parse(final_score)
        with open(output_xml_path, "wb") as f:
            f.write(xml_bytes)

        musescore_paths = [
            r"C:\Program Files\MuseScore 4\bin\MuseScore4.exe",
            r"C:\Program Files\MuseScore 3\bin\MuseScore3.exe",
            r"C:\Program Files (x86)\MuseScore 4\bin\MuseScore4.exe",
            "MuseScore4.exe",
            "mscore.exe"
        ]
        mscore_exe = next((p for p in musescore_paths if os.path.exists(p)), None)
        if mscore_exe:
            subprocess.run([mscore_exe, "-f", "-o", output_pdf_path, output_xml_path], check=True)
            return xml_bytes.decode('utf-8'), output_pdf_path
        return xml_bytes.decode('utf-8'), None
    except Exception as e:
        return f"Error: {e}", None

def parse_note_string(raw_bar_text: str):
    """Extracts clean pitch names from text like 'FFFF' or 'FGAA#'."""
    if not raw_bar_text or raw_bar_text.strip() == "-":
        return []
    pattern = r'([A-Ga-g][#b]?\d?)'
    matches = re.findall(pattern, raw_bar_text.strip())
    clean = []
    for m in matches:
        p = m.upper()
        if not any(char.isdigit() for char in p):
            p += "4"
        clean.append(p)
    return clean

def chunk_notes_to_bars(raw_notes_string: str, notes_per_bar: int = 8) -> list:
    """Takes continuous notes (like FFFFFGA#AA#...) and breaks them into clean 4-8 note bars."""
    pattern = r'([A-Ga-g][#b]?)'
    individual_notes = re.findall(pattern, raw_notes_string)
    if not individual_notes:
        return ["-"]
    
    bars = []
    for i in range(0, len(individual_notes), notes_per_bar):
        chunk = "".join(individual_notes[i:i + notes_per_bar])
        bars.append(chunk)
    return bars

def create_lead_sheet_pdf(lh_bars, rh_bars, lyrics_list, out_pdf_path, song_title="Korg EK-50 IN Performance"):
    """Generates an organized, readable 8-key-per-measure Song Sheet PDF."""
    doc = SimpleDocTemplate(out_pdf_path, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=18, leading=22, textColor=colors.HexColor("#0f172a"), alignment=1)
    sub_style = ParagraphStyle('SubStyle', parent=styles['Normal'], fontSize=9, leading=13, textColor=colors.HexColor("#64748b"), alignment=1)
    header_style = ParagraphStyle('HeaderStyle', parent=styles['Normal'], fontSize=9, fontName='Helvetica-Bold', textColor=colors.HexColor("#334155"))
    cell_lh = ParagraphStyle('LHStyle', parent=styles['Normal'], fontSize=11, fontName='Helvetica-Bold', textColor=colors.HexColor("#0284c7"))
    cell_rh = ParagraphStyle('RHStyle', parent=styles['Normal'], fontSize=11, fontName='Helvetica-Bold', textColor=colors.HexColor("#16a34a"))
    cell_lyr = ParagraphStyle('LyrStyle', parent=styles['Normal'], fontSize=10, fontName='Helvetica-Oblique', textColor=colors.HexColor("#334155"))

    elements = [
        Paragraph(song_title, title_style),
        Paragraph("Structured 8-Note Measure Notation Sheet (Left Hand & Right Hand Split)", sub_style),
        Spacer(1, 14)
    ]

    total_bars = max(len(lh_bars), len(rh_bars))
    table_data = [[
        Paragraph("Bar #", header_style),
        Paragraph("Left Hand (Chord)", header_style),
        Paragraph("Right Hand (Melody Keys: Max 8)", header_style),
        Paragraph("Matching Lyrics / Phrase", header_style)
    ]]

    for i in range(total_bars):
        lh = lh_bars[i] if i < len(lh_bars) and lh_bars[i].strip() else "-"
        rh = rh_bars[i] if i < len(rh_bars) and rh_bars[i].strip() else "-"
        lyr = lyrics_list[i] if i < len(lyrics_list) and lyrics_list[i].strip() else ""
        table_data.append([
            Paragraph(f"Bar {i+1}", header_style),
            Paragraph(str(lh), cell_lh),
            Paragraph(str(rh), cell_rh),
            Paragraph(str(lyr), cell_lyr)
        ])

    col_widths = [45, 105, 230, 160]
    t = Table(table_data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#f8fafc")),
        ('LINEBELOW', (0, 0), (-1, 0), 1.5, colors.HexColor("#94a3b8")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(t)
    doc.build(elements)
    return out_pdf_path

def create_pdf_from_recording(rh_bars_list: list, output_xml_path: str, output_pdf_path: str):
    """Creates a measure-accurate Grand Staff PDF via MuseScore CLI."""
    try:
        score = stream.Score()
        part = stream.Part()
        part.append(clef.TrebleClef())
        part.append(meter.TimeSignature('4/4'))

        for raw_bar in rh_bars_list:
            m = stream.Measure()
            notes = parse_note_string(raw_bar)
            if not notes:
                m.append(note.Rest(type='whole'))
            else:
                dur_per_note = 4.0 / len(notes)
                for p_str in notes:
                    n = note.Note(p_str)
                    n.duration = duration.Duration(dur_per_note)
                    n.addLyric(n.pitch.name)
                    m.append(n)
            part.append(m)

        score.append(part)
        exporter = musicxml.m21ToXml.GeneralObjectExporter()
        xml_bytes = exporter.parse(score)
        with open(output_xml_path, "wb") as f:
            f.write(xml_bytes)

        musescore_paths = [
            r"C:\Program Files\MuseScore 4\bin\MuseScore4.exe",
            r"C:\Program Files\MuseScore 3\bin\MuseScore3.exe",
            r"C:\Program Files (x86)\MuseScore 4\bin\MuseScore4.exe",
            "MuseScore4.exe",
            "mscore.exe"
        ]
        mscore_exe = next((p for p in musescore_paths if os.path.exists(p)), None)
        if mscore_exe:
            subprocess.run([mscore_exe, "-f", "-o", output_pdf_path, output_xml_path], check=True)
            return output_pdf_path
        return None
    except Exception as e:
        return None