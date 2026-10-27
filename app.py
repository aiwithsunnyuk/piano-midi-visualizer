import streamlit as st
import streamlit.components.v1 as components
import os
from core.audio_extractor import extract_audio_from_video, convert_audio_to_midi
from core.music_analyzer import (
    detect_tempo_and_beats,
    detect_scale_and_key,
    generate_musicxml_and_pdf
)
from streamlit_music_score import music_score

st.set_page_config(page_title="Piano Theory Lab", layout="wide")

tab_live, tab_pipeline = st.tabs(["🎹 Live Korg Recorder & Instant Save", "📹 Video Note Extraction"])

# =========================================================
# TAB 1: LIVE RECORDING WITH DIRECT 1-CLICK SAVING
# =========================================================
with tab_live:
    st.header("🎹 Korg EK-50 IN — Live 5-Octave Studio")
    st.caption("C1 & C2 (Bass/Chords) = Left Hand | C3, C4 & C5 (Melody) = Right Hand. Play your song and hit Download anytime.")

    auto_recorder_component = """
    <!DOCTYPE html>
    <html>
    <head>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf-autotable/3.5.31/jspdf.plugin.autotable.min.js"></script>

    <style>
        body {
            margin: 0;
            padding: 8px;
            background-color: #0e1117;
            color: #ffffff;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            user-select: none;
        }
        .status-panel {
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: #1e2530;
            padding: 8px 16px;
            border-radius: 6px;
            margin-bottom: 8px;
            font-size: 13px;
        }
        .controls-row {
            display: flex;
            gap: 10px;
            align-items: center;
            margin-bottom: 8px;
            flex-wrap: wrap;
            background: #161b22;
            padding: 8px 12px;
            border-radius: 6px;
            border: 1px solid #30363d;
        }
        button.btn {
            background: #238636;
            color: white;
            border: none;
            padding: 7px 14px;
            border-radius: 5px;
            font-size: 13px;
            font-weight: 600;
            cursor: pointer;
            transition: 0.15s;
        }
        button.btn:hover { background: #2ea043; }
        button.btn-pdf { background: #0969da; }
        button.btn-pdf:hover { background: #1f6feb; }
        button.btn-clear { background: #da3633; }
        button.btn-clear:hover { background: #f85149; }

        /* Locked scrollable notes container */
        .sheet-container {
            background: #161b22;
            border: 1px solid #30363d;
            border-radius: 6px;
            padding: 10px 14px;
            margin-bottom: 8px;
            font-family: 'Courier New', Courier, monospace;
            font-size: 14px;
            line-height: 1.5;
            height: 110px;
            max-height: 110px;
            overflow-y: auto;
            scrollbar-width: thin;
        }
        .track-lh { color: #58a6ff; font-weight: bold; }
        .track-rh { color: #7ee787; font-weight: bold; }
        .bar-separator { color: #f0883e; font-weight: bold; padding: 0 4px; }

        .zone-legend {
            font-size: 12px;
            margin-bottom: 6px;
            display: flex;
            gap: 16px;
        }
        .legend-lh { color: #58a6ff; font-weight: bold; }
        .legend-rh { color: #7ee787; font-weight: bold; }

        /* Full-size unshrinkable piano */
        .piano-scroll {
            overflow-x: auto;
            padding-bottom: 6px;
            background: #111;
            border-radius: 8px;
            border: 1px solid #30363d;
        }
        .piano-wrapper {
            position: relative;
            display: inline-flex;
            height: 185px;
            padding: 6px;
        }
        .key {
            cursor: pointer;
            display: flex;
            flex-direction: column;
            justify-content: flex-end;
            align-items: center;
            padding-bottom: 6px;
            font-size: 10px;
            box-sizing: border-box;
            transition: background-color 0.05s ease;
        }
        .white-key {
            width: 36px;
            min-width: 36px;
            flex-shrink: 0;
            height: 170px;
            background: #ffffff;
            color: #222;
            border: 1px solid #ccc;
            border-radius: 0 0 4px 4px;
            z-index: 1;
        }
        .white-key.active-lh { background: #0284c7 !important; color: #fff; }
        .white-key.active-rh { background: #22c55e !important; color: #fff; }
        
        .black-key {
            width: 22px;
            min-width: 22px;
            flex-shrink: 0;
            height: 105px;
            background: #1f1f1f;
            color: #eee;
            margin-left: -11px;
            margin-right: -11px;
            z-index: 2;
            border-radius: 0 0 3px 3px;
        }
        .black-key.active-lh { background: #0369a1 !important; color: #fff; }
        .black-key.active-rh { background: #15803d !important; color: #fff; }
        .split-divider { border-right: 4px solid #f97316 !important; }
    </style>
    </head>
    <body>

    <div class="status-panel">
        <div><strong>Korg Hardware:</strong> <span id="midi-status" style="color: #ff9800;">Scanning USB...</span></div>
        <div>
            <strong>Recorded Bars:</strong> <span id="bar-counter" style="color:#00adb5; font-size:16px; font-weight:bold;">1</span>
        </div>
        <div><strong>Last Key Velocity:</strong> <span id="velocity-val" style="background:#00adb5; padding:2px 8px; border-radius:4px; font-weight:bold;">0</span></div>
    </div>

    <!-- Live Split Sheet Display -->
    <div class="sheet-container">
        <div><span class="track-lh">(LH [C1-C2])&nbsp;&nbsp;</span><span id="display-lh">-</span></div>
        <div><span class="track-rh">(RH [C3-C5])&nbsp;&nbsp;</span><span id="display-rh">-</span></div>
    </div>

    <!-- Action Toolbar (Direct Downloads) -->
    <div class="controls-row">
        <label><strong>Song Title:</strong></label>
        <input type="text" id="song-title-input" value="Korg EK-50 IN Performance" style="background:#0e1117; color:#fff; border:1px solid #30363d; padding:5px 8px; border-radius:4px; width:220px;">

        <label style="margin-left:6px;"><strong>Max Keys/Bar:</strong></label>
        <select id="max-notes-select" style="background:#0e1117; color:#fff; border:1px solid #30363d; padding:4px 6px; border-radius:4px;">
            <option value="8" selected>8 Keys (Standard 4/4)</option>
            <option value="4">4 Keys (Quarter Beats)</option>
            <option value="16">16 Keys (Double Measure)</option>
        </select>

        <!-- Direct Instant Export Buttons -->
        <button class="btn btn-pdf" id="btn-download-pdf">📄 Download Song Sheet (PDF)</button>
        <button class="btn" id="btn-download-txt">📥 Download Notes (.txt)</button>
        <button class="btn btn-clear" id="btn-clear">🗑️ Reset / New Song</button>
    </div>

    <div class="zone-legend">
        <span class="legend-lh">■ Blue = LH (C1 & C2: Bass / Chords)</span>
        <span class="legend-rh">■ Green = RH (C3, C4 & C5: Melody)</span>
        <span style="color:#f97316;">| Orange Divider = Split Point (B2 / C3)</span>
    </div>

    <div class="piano-scroll">
        <div class="piano-wrapper" id="keyboard"></div>
    </div>

    <script>
        const NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"];
        const START_MIDI = 36; // C1
        const END_MIDI = 96;   // C5
        const SPLIT_POINT_MIDI = 59; // B2 (C1-C2 = LH, C3-C5 = RH)

        const keyboardContainer = document.getElementById("keyboard");
        const midiStatus = document.getElementById("midi-status");
        const velocityLabel = document.getElementById("velocity-val");
        const displayLH = document.getElementById("display-lh");
        const displayRH = document.getElementById("display-rh");
        const barCounter = document.getElementById("bar-counter");
        const maxNotesSelect = document.getElementById("max-notes-select");
        const songTitleInput = document.getElementById("song-title-input");

        let lhBars = [[]];
        let rhBars = [[]];
        let activeNotes = new Map();
        let keyElements = {};

        // 1. Build 61 keys
        for (let midi = START_MIDI; midi <= END_MIDI; midi++) {
            const pitchClass = midi % 12;
            const noteName = NOTE_NAMES[pitchClass];
            const octave = Math.min(5, Math.floor((midi - START_MIDI) / 12) + 1);
            const isBlack = noteName.includes("#");

            const key = document.createElement("div");
            key.className = `key ${isBlack ? "black-key" : "white-key"}`;
            key.id = `k-${midi}`;
            key.innerHTML = `<span>${noteName}</span><span style="font-size:8px;">${octave}</span>`;
            
            if (midi === SPLIT_POINT_MIDI) {
                key.classList.add("split-divider");
            }
            keyboardContainer.appendChild(key);
            keyElements[midi] = key;
        }

        // 2. Web MIDI setup
        if (navigator.requestMIDIAccess) {
            navigator.requestMIDIAccess().then(access => {
                access.inputs.forEach(input => input.onmidimessage = handleMIDI);
                if (access.inputs.size > 0) {
                    const firstInput = access.inputs.values().next().value;
                    midiStatus.textContent = `Connected: ${firstInput.name}`;
                    midiStatus.style.color = "#3fb950";
                }
                access.onstatechange = e => {
                    if (e.port.state === "connected") {
                        e.port.onmidimessage = handleMIDI;
                        midiStatus.textContent = `Connected: ${e.port.name}`;
                        midiStatus.style.color = "#3fb950";
                    }
                };
            });
        }

        function handleMIDI(e) {
            const [status, noteNum, velocity] = e.data;
            const cmd = status >> 4;
            if (cmd === 9 && velocity > 0) onNoteDown(noteNum, velocity);
            else if (cmd === 8 || (cmd === 9 && velocity === 0)) onNoteUp(noteNum);
        }

        function detectChord(notes) {
            if (notes.length === 0) return "";
            if (notes.length === 1) return NOTE_NAMES[notes[0] % 12];
            const pcs = Array.from(new Set(notes.map(n => n % 12))).sort((a,b) => a - b);
            const rootName = NOTE_NAMES[pcs[0]];
            const intervals = pcs.map(p => (p - pcs[0] + 12) % 12).sort((a,b) => a - b);
            if (intervals.includes(4) && intervals.includes(7)) return rootName;
            if (intervals.includes(3) && intervals.includes(7)) return rootName + "m";
            if (intervals.includes(4)) return rootName;
            if (intervals.includes(3)) return rootName + "m";
            return rootName;
        }

        function onNoteDown(num, vel) {
            velocityLabel.textContent = vel;
            activeNotes.set(num, true);

            const pitchClass = num % 12;
            const noteLetter = NOTE_NAMES[pitchClass];
            const maxNotes = parseInt(maxNotesSelect.value) || 8;

            if (num <= SPLIT_POINT_MIDI) {
                // LH Zone (C1 & C2)
                if (keyElements[num]) keyElements[num].classList.add("active-lh");

                const lhActive = Array.from(activeNotes.keys()).filter(n => n <= SPLIT_POINT_MIDI);
                const chordName = detectChord(lhActive);
                const currentBarLH = lhBars[lhBars.length - 1];
                const currentBarRH = rhBars[rhBars.length - 1];

                if ((currentBarLH.length > 0 || currentBarRH.length > 0) && !currentBarLH.includes(chordName)) {
                    advanceBar();
                }
                const activeBar = lhBars[lhBars.length - 1];
                if (!activeBar.includes(chordName)) activeBar.push(chordName);
            } else {
                // RH Zone (C3 to C5)
                if (keyElements[num]) keyElements[num].classList.add("active-rh");

                const activeBar = rhBars[rhBars.length - 1];
                if (activeBar.length >= maxNotes) {
                    advanceBar();
                }
                const newBar = rhBars[rhBars.length - 1];
                newBar.push(noteLetter);
            }
            updateTextDisplay();
        }

        function onNoteUp(num) {
            if (keyElements[num]) {
                keyElements[num].classList.remove("active-lh");
                keyElements[num].classList.remove("active-rh");
            }
            activeNotes.delete(num);
        }

        function advanceBar() {
            lhBars.push([]);
            rhBars.push([]);
            barCounter.textContent = lhBars.length;
            updateTextDisplay();
        }

        function updateTextDisplay() {
            const lhFormatted = lhBars.map(bar => bar.join(" ") || "-").join(" <span class='bar-separator'>|</span> ");
            const rhFormatted = rhBars.map(bar => bar.join("") || "-").join(" <span class='bar-separator'>|</span> ");
            displayLH.innerHTML = lhFormatted;
            displayRH.innerHTML = rhFormatted;
        }

        // Reset
        document.getElementById("btn-clear").onclick = () => {
            lhBars = [[]];
            rhBars = [[]];
            barCounter.textContent = "1";
            updateTextDisplay();
        };

        // 1-Click Plain Text Download
        document.getElementById("btn-download-txt").onclick = () => {
            const title = songTitleInput.value.trim() || "Korg EK-50 IN Performance";
            const lhText = "(LH)  " + lhBars.map(bar => bar.join(" ") || "-").join(" | ");
            const rhText = "(RH)  " + rhBars.map(bar => bar.join("") || "-").join(" | ");
            const fileContent = `${title}\\n\\n${lhText}\\n${rhText}\\n`;

            const blob = new Blob([fileContent], { type: "text/plain;charset=utf-8" });
            const link = document.createElement("a");
            link.href = URL.createObjectURL(blob);
            link.download = `${title.toLowerCase().replace(/\\s+/g, '_')}_notes.txt`;
            link.click();
        };

        // 1-Click Formatted Lead Sheet PDF Download
        document.getElementById("btn-download-pdf").onclick = () => {
            const { jsPDF } = window.jspdf;
            const doc = new jsPDF();
            const title = songTitleInput.value.trim() || "Korg EK-50 IN Performance";

            // Header
            doc.setFontSize(18);
            doc.setTextColor(30, 41, 59);
            doc.text(title, 14, 20);

            doc.setFontSize(10);
            doc.setTextColor(100, 116, 139);
            doc.text("Structured Bar-by-Bar Notation Sheet (LH: C1-C2 | RH: C3-C5)", 14, 27);

            // Build Table Data from live played bars
            const totalBars = Math.max(lhBars.length, rhBars.length);
            const tableRows = [];

            for (let i = 0; i < totalBars; i++) {
                const lh = (lhBars[i] && lhBars[i].length > 0) ? lhBars[i].join(" ") : "-";
                const rh = (rhBars[i] && rhBars[i].length > 0) ? rhBars[i].join("") : "-";
                tableRows.push([`Bar ${i + 1}`, lh, rh]);
            }

            doc.autoTable({
                startY: 34,
                head: [["Bar #", "Left Hand (Bass / Chords)", "Right Hand (Melody Notes: 8 Keys)"]],
                body: tableRows,
                theme: "grid",
                headStyles: { fillColor: [241, 245, 249], textColor: [51, 65, 85], fontStyle: "bold" },
                columnStyles: {
                    0: { cellWidth: 30, fontStyle: "bold" },
                    1: { cellWidth: 70, textColor: [2, 132, 199], fontStyle: "bold" },
                    2: { cellWidth: 85, textColor: [22, 163, 74], fontStyle: "bold" }
                },
                styles: { fontSize: 11, cellPadding: 5 }
            });

            doc.save(`${title.toLowerCase().replace(/\\s+/g, '_')}_sheet.pdf`);
        };

        updateTextDisplay();
    </script>
    </body>
    </html>
    """

    components.html(auto_recorder_component, height=520, scrolling=False)


# =========================================================
# TAB 2: VIDEO NOTE EXTRACTION PIPELINE
# =========================================================
with tab_pipeline:
    st.header("Extract Scales, Rhythm & Notes from Video")
    uploaded_file = st.file_uploader("Upload Keyboard Performance Video (.mp4, .mov)", type=["mp4", "mov"])

    if uploaded_file is not None:
        video_path = os.path.join("data", "uploads", uploaded_file.name)
        with open(video_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        st.video(video_path)

        if st.button("Analyze Performance"):
            with st.spinner("Analyzing music and generating PDF sheet music..."):
                wav_path = os.path.join("data", "outputs", "extracted_audio.wav")
                output_dir = os.path.join("data", "outputs")
                midi_filename = "extracted_audio_basic_pitch.mid"
                midi_path = os.path.join(output_dir, midi_filename)
                xml_path = os.path.join(output_dir, "sheet_music_score.musicxml")
                pdf_path = os.path.join(output_dir, "sheet_music_score.pdf")

                extract_audio_from_video(video_path, wav_path)
                detected_key, chroma = detect_scale_and_key(wav_path)
                tempo, beat_count = detect_tempo_and_beats(wav_path)
                convert_audio_to_midi(wav_path, output_dir)
                xml_string, generated_pdf = generate_musicxml_and_pdf(midi_path, xml_path, pdf_path)

            st.success("Extraction and analysis complete!")

            res_col1, res_col2, res_col3 = st.columns(3)
            res_col1.metric("Detected Key / Scale", detected_key)
            res_col2.metric("Tempo", f"{tempo} BPM")
            res_col3.metric("Downbeat Count", beat_count)
            
            st.subheader("🎼 Extracted Sheet Music")
            if not xml_string.startswith("Error"):
                music_score(xml_string, height=650)
            else:
                st.error(xml_string)

            st.subheader("💾 Export Transcriptions")
            d_col1, d_col2, d_col3 = st.columns(3)

            with d_col1:
                if os.path.exists(midi_path):
                    with open(midi_path, "rb") as f:
                        st.download_button(
                            label="📥 MIDI (.mid for Korg)",
                            data=f,
                            file_name="korg_performance.mid",
                            mime="audio/midi",
                            use_container_width=True
                        )

            with d_col2:
                if os.path.exists(xml_path):
                    with open(xml_path, "rb") as f:
                        st.download_button(
                            label="📥 MusicXML (.musicxml)",
                            data=f,
                            file_name="sheet_music_score.musicxml",
                            mime="application/vnd.recordare.musicxml+xml",
                            use_container_width=True
                        )

            with d_col3:
                if generated_pdf and os.path.exists(generated_pdf):
                    with open(generated_pdf, "rb") as f:
                        st.download_button(
                            label="📄 Download Sheet (PDF)",
                            data=f,
                            file_name="piano_sheet_with_note_names.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )
                else:
                    st.info("PDF conversion uses MuseScore CLI in the background.")