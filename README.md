# LSDSNG File Generator & Editor

This directory contains research, tools, and scripts for programmatically interacting with **Little Sound DJ (LSDj)** `.lsdsng` and `.sav` files.

## 🎵 Current Status & Progress

### 1. Vendored & Hardened `pylsdj` Library
We copied the `pylsdj` library into the workspace folder (`/pylsdj`) to keep all changes local. We then resolved multiple Python 3 and design bugs in the library:
* **String/Bytes Compatibility**: Fixed `ValueError` and `AssertionError` bugs caused by comparing decoded strings (`'jk'`, `'rb'`) with raw byte literals (`b'jk'`, `b'rb'`) in Python 3.
* **Closure Scoping Bug**: Fixed a classic Python closure scope bug in `song.py` property generation where all properties (like `song.tempo`, `song.sync_setting`) wrongly returned the values of the last loop variable (`wave_synth_overwrite_locks`).
* **Iteration Support**: Corrected `assert_index_sane` to raise standard `IndexError` instead of `AssertionError` when indexes are out of bounds, allowing standard Python loops/enumerate functions (like `enumerate(chain.phrases)`) to complete naturally rather than crashing.
* **Missing Methods**: Implemented the `__len__` method on `Instruments`.

### 2. MIDI to LSDSNG Converter
Created a robust conversion script, [`midi_to_lsdsng.py`](file:///home/amir/Documents/Misc/Inhalants/LSDSNG/midi_to_lsdsng.py):
* Parses standard MIDI files using `mido`.
* Dynamically clears and resets an existing template project (`UNTOLDST.lsdsng`) to construct a clean canvas.
* Allocates standard Game Boy instrument types (Pulse for channels 1/2, Wave for channel 3, and Noise for channel 4).
* Automatically maps MIDI channels to Game Boy sound channels based on note counts and standard drum tracks.
* Quantizes notes to sixteenth-note steps, groups them into phrases/chains, and handles rests/overlapping notes.
* Successfully tested against [`Trumpet Midi.MID`](file:///home/amir/Documents/Misc/Inhalants/LSDSNG/Trumpet%20Midi.MID) to produce a valid, loadable [`trumpet.lsdsng`](file:///home/amir/Documents/Misc/Inhalants/LSDSNG/trumpet.lsdsng).

To convert any MIDI file to a `.lsdsng` file, run:
```bash
python3 midi_to_lsdsng.py <input_midi_path> <output_lsdsng_path>
```

Example:
```bash
python3 midi_to_lsdsng.py "Trumpet Midi.MID" "trumpet.lsdsng"
```

### 3. Save File Injection & Emulator Playback
We developed an end-to-end automated emulation and capture script:
* **Save File Injection**: We load the raw `lsdj.sav` and inject the generated `.lsdsng` file into slot 0. To avoid standard `pylsdj` block-allocation decompression crashes on other tracks in the save file, the script clears all other unused project slots first.
* **Headless Emulation**: Uses `pyboy` to boot `lsdj9_4_2.gb` in Game Boy Color mode headlessly.
* **Diagnostic Screen Bypassing**: Simulates button press events (`START`, `A`) to bypass the BIOS chime and the LSDj cartridge diagnostic/copyright screens.
* **Audio Capture & Export**: Monkeypatches `pysdl2`'s `SDL_QueueAudio` call in the emulator's core, captures the raw 8-bit stereo audio buffer, and converts it to a standard 16-bit 32.768kHz stereo `.wav` file.

## 🕹️ How to Run the Emulator Playback

To run the emulator headlessly, load the injected save file, start playback, and record a 20-second audio track:
1. Ensure the LSDj ROM file `lsdj9_4_2.gb` is placed inside `lsdj_rom/`.
2. Run:
   ```bash
   python3 play_lsdj.py
   ```
3. The script will:
   * Inject `trumpet.lsdsng` into `lsdj.sav` and copy it to `lsdj_rom/lsdj9_4_2.sav`.
   * Emulate the boot process and start the song.
   * Save a screenshot of the tracker screen during playback to `lsdj_playback.png`.
   * Export the recorded audio to `lsdj_output.wav`.

