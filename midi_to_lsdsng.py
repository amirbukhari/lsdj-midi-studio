import sys
import os
import mido

# Insert current directory to import local pylsdj
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pylsdj

def midi_note_to_lsdj_note(midi_pitch):
    note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    pitch_class = note_names[midi_pitch % 12]
    # In LSDJ, octaves are 3 to 15 (hex 3 to F)
    # MIDI note 60 is C4. So octave = midi_pitch // 12 - 1.
    octave = (midi_pitch // 12) - 1
    if octave < 3:
        octave = 3
    elif octave > 15:
        octave = 15
    octave_str = f"{octave:X}"
    return f"{pitch_class.ljust(2, ' ')}{octave_str}"

def convert_midi_to_lsdsng(midi_path, output_path, template_path="UNTOLDST.lsdsng"):
    print(f"Loading template: {template_path}")
    proj = pylsdj.load_lsdsng(template_path)
    song = proj.song

    # 1. Clear out the template song data completely (except instruments)
    print("Clearing template sequence, phrases, and chains...")
    for row in song.song_data.song:
        row.pu1 = 0xff
        row.pu2 = 0xff
        row.wav = 0xff
        row.noi = 0xff
    for i in range(len(song.song_data.phrase_alloc_table)):
        song.song_data.phrase_alloc_table[i] = False
    for i in range(len(song.song_data.chain_alloc_table)):
        song.song_data.chain_alloc_table[i] = False

    # 2. Parse MIDI file
    print(f"Parsing MIDI file: {midi_path}")
    mid = mido.MidiFile(midi_path)
    ticks_per_beat = mid.ticks_per_beat

    # Dict of channel_idx -> list of notes (pitch, start_beat, duration)
    channels_notes = {c: [] for c in range(16)}
    bpm = 120

    for track in mid.tracks:
        curr_ticks = 0
        active_notes = {}  # (channel, pitch) -> start_beat
        for msg in track:
            curr_ticks += msg.time
            curr_beat = curr_ticks / ticks_per_beat

            if msg.type == 'set_tempo':
                bpm = mido.tempo2bpm(msg.tempo)
            elif msg.type == 'note_on' and msg.velocity > 0:
                active_notes[(msg.channel, msg.note)] = curr_beat
            elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
                key = (msg.channel, msg.note)
                if key in active_notes:
                    start_beat = active_notes.pop(key)
                    duration = curr_beat - start_beat
                    channels_notes[msg.channel].append({
                        'pitch': msg.note,
                        'start_beat': start_beat,
                        'duration': duration
                    })

    # Set song tempo
    print(f"Setting song tempo: {round(bpm)} BPM")
    song.tempo = int(min(max(round(bpm), 40), 250))

    # 3. Map MIDI channels to LSDJ channels
    active_channels = [c for c, notes in channels_notes.items() if len(notes) > 0]
    active_channels.sort(key=lambda c: len(channels_notes[c]), reverse=True)
    print(f"Active MIDI channels sorted by note count: {active_channels}")

    mapping = {}
    if 9 in active_channels:  # MIDI channel 10 (drums) -> noise channel
        mapping['noi'] = 9
        active_channels.remove(9)

    lsdj_channels = ['pu1', 'pu2', 'wav']
    for l_chan in lsdj_channels:
        if active_channels:
            mapping[l_chan] = active_channels.pop(0)

    if 'noi' not in mapping and active_channels:
        mapping['noi'] = active_channels.pop(0)

    print(f"Mapping MIDI channels to LSDJ channels: {mapping}")

    # Set project name
    proj_name = os.path.basename(midi_path).split('.')[0].upper()[:8]
    proj.name = proj_name.ljust(8, '\0')
    print(f"Setting project name to: {proj.name}")

    # 4. Generate notes on LSDJ channels
    for lsdj_chan, midi_chan in mapping.items():
        notes = channels_notes[midi_chan]
        if not notes:
            continue

        # Set instrument index for this channel (reusing template's pre-configured instruments)
        if lsdj_chan in ('pu1', 'pu2'):
            inst_idx = 2   # template pulse instrument
        elif lsdj_chan == 'wav':
            inst_idx = 0   # template wave instrument
        else:  # noi
            inst_idx = 16  # template noise instrument

        inst_obj = song.instruments[inst_idx]

        # Determine note starts and ends on sixteenth steps
        starts = {}
        ends = {}
        for note in notes:
            start_step = int(round(note['start_beat'] * 4))
            end_step = int(round((note['start_beat'] + note['duration']) * 4))
            starts[start_step] = note['pitch']
            ends[end_step] = 'rest'

        max_step = max(starts.keys()) if starts else 0
        total_phrases_count = (max_step // 16) + 1

        print(f"Channel {lsdj_chan}: max step is {max_step}, total unique phrases: {total_phrases_count}")

        # Keep track of allocated phrases for this channel
        allocated_phrases = {}  # phrase_idx_in_song_bar -> phrase_obj

        for p_bar in range(total_phrases_count):
            # Check if there are any note start events in this bar
            bar_starts = {s % 16: pitch for s, pitch in starts.items() if s // 16 == p_bar}
            bar_ends = {s % 16 for s, rest in ends.items() if s // 16 == p_bar}

            if not bar_starts and not bar_ends:
                allocated_phrases[p_bar] = None
                continue

            # Allocate new phrase
            free_phrase_idx = song.phrases.next_free()
            if free_phrase_idx is None:
                print("Warning: Out of phrase slots! Truncating song.")
                break

            song.phrases.allocate(free_phrase_idx)
            phrase = song.phrases[free_phrase_idx]

            # Populate steps
            for step_in_phrase in range(16):
                abs_step = p_bar * 16 + step_in_phrase
                if abs_step in starts:
                    pitch = starts[abs_step]
                    phrase.notes[step_in_phrase] = midi_note_to_lsdj_note(pitch)
                    phrase.instruments[step_in_phrase] = inst_obj
                elif abs_step in ends:
                    phrase.notes[step_in_phrase] = '---'
                    phrase.instruments[step_in_phrase] = None
                else:
                    phrase.notes[step_in_phrase] = '---'
                    phrase.instruments[step_in_phrase] = None

            allocated_phrases[p_bar] = phrase

        # Group phrases into chains (16 phrases per chain)
        total_chains_count = (total_phrases_count // 16) + 1
        allocated_chains = []

        for c_idx in range(total_chains_count):
            # Check if all phrases in this chain are None
            chain_phrases = [allocated_phrases.get(c_idx * 16 + i) for i in range(16)]
            if all(p is None for p in chain_phrases):
                allocated_chains.append(None)
                continue

            # Allocate new chain
            free_chain_idx = song.chains.next_free()
            if free_chain_idx is None:
                print("Warning: Out of chain slots! Truncating song.")
                break

            song.chains.allocate(free_chain_idx)
            chain = song.chains[free_chain_idx]

            # Populate chain
            for i, phrase_obj in enumerate(chain_phrases):
                chain.phrases[i] = phrase_obj

            allocated_chains.append(chain)

        # Set chains in the sequence
        for i, chain_obj in enumerate(allocated_chains):
            if i >= len(song.song_data.song):
                break
            if chain_obj is not None:
                setattr(song.song_data.song[i], lsdj_chan, chain_obj.index)

    # 5. Save the output lsdsng file
    print(f"Saving converted song to: {output_path}")
    proj.save_lsdsng(output_path)
    print("Conversion completed successfully!")
    return {
        "project_name": proj_name.strip('\0'),
        "bpm": round(bpm),
        "mapping": mapping
    }


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 midi_to_lsdsng.py <input_midi> <output_lsdsng>")
        sys.exit(1)
    convert_midi_to_lsdsng(sys.argv[1], sys.argv[2])
