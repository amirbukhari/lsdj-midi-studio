import os
import sys
import argparse
import shutil
from flask import Flask, request, jsonify, render_template, send_file

# Add local path to import pylsdj and midi_to_lsdsng
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pylsdj
from midi_to_lsdsng import convert_midi_to_lsdsng

app = Flask(__name__, template_folder='templates')

# Create necessary directories
os.makedirs("lsdj_rom", exist_ok=True)
os.makedirs("temp", exist_ok=True)

DEFAULT_META = None

def initialize_default_midi():
    default_midi = "Trumpet Midi.MID"
    output_lsdsng = "trumpet.lsdsng"
    baseline_sav = "lsdj.sav"
    if os.path.exists(default_midi):
        print(f"Pre-converting default midi: {default_midi}")
        try:
            meta = convert_midi_to_lsdsng(default_midi, output_lsdsng, template_path="UNTOLDST.lsdsng")
            
            # Load save, clear other slots, inject, and save
            if not os.path.exists(baseline_sav):
                with open(baseline_sav, 'wb') as f:
                    f.write(b'\0' * 131072)
                    
            sav = pylsdj.SAVFile(baseline_sav)
            for idx in range(1, 32):
                if idx in sav.projects.keys() or idx in sav.projects._projects:
                    sav.projects[idx] = None
            new_project = pylsdj.load_lsdsng(output_lsdsng)
            sav.projects[0] = new_project
            sav.active_project_number = 0
            sav.preamble = new_project.get_raw_data()
            sav.save(baseline_sav)
            
            # Copy to emulator folder
            emu_sav_path = os.path.join("lsdj_rom", "lsdj9_4_2.sav")
            shutil.copy(baseline_sav, emu_sav_path)
            print("Default save initialized successfully!")
            return {
                "success": True,
                "project_name": meta["project_name"],
                "bpm": meta["bpm"],
                "mapping": meta["mapping"],
                "filename": default_midi
            }
        except Exception as e:
            print(f"Error initializing default midi: {e}")
    else:
        print("Default midi Trumpet Midi.MID not found.")
    return None

@app.route('/')
def index():
    return render_template('index.html', default_meta=DEFAULT_META)

@app.route('/billing')
def billing():
    return send_file(os.path.join('static', 'billing', 'index.html'))

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'midi' not in request.files:
        return jsonify({"success": False, "error": "No file uploaded"}), 400
    
    file = request.files['midi']
    if file.filename == '':
        return jsonify({"success": False, "error": "No file selected"}), 400
    
    filename_lower = file.filename.lower()
    if not (filename_lower.endswith('.mid') or filename_lower.endswith('.midi')):
        return jsonify({"success": False, "error": "Only .mid and .midi files are supported"}), 400

    safe_filename = "".join(c for c in file.filename if c.isalnum() or c in ('.', '_', '-'))
    temp_path = os.path.join("temp", safe_filename)
    file.save(temp_path)

    try:
        # 1. Convert MIDI to trumpet.lsdsng
        output_lsdsng = "trumpet.lsdsng"
        meta = convert_midi_to_lsdsng(temp_path, output_lsdsng, template_path="UNTOLDST.lsdsng")

        # 2. Inject song into lsdj.sav
        baseline_sav = "lsdj.sav"
        if not os.path.exists(baseline_sav):
            # Create a dummy blank save file of 128KB if it doesn't exist
            # (though in our workspace it already exists)
            with open(baseline_sav, 'wb') as f:
                f.write(b'\0' * 131072)
        
        # Load the save file, clear other slots, inject, and save
        sav = pylsdj.SAVFile(baseline_sav)
        
        # Clear slots 1-31 to prevent decompression block corruption crashes
        for idx in range(1, 32):
            if idx in sav.projects.keys() or idx in sav.projects._projects:
                sav.projects[idx] = None
        
        # Load the generated lsdsng project and inject into slot 0
        new_project = pylsdj.load_lsdsng(output_lsdsng)
        sav.projects[0] = new_project
        sav.active_project_number = 0
        
        # Overwrite the active work memory preamble (first 32KB) with the raw project data
        sav.preamble = new_project.get_raw_data()
        
        # Save back to main lsdj.sav
        sav.save(baseline_sav)

        # 3. Copy to lsdj_rom/lsdj9_4_2.sav so EmulatorJS can load it
        emu_sav_path = os.path.join("lsdj_rom", "lsdj9_4_2.sav")
        shutil.copy(baseline_sav, emu_sav_path)

        # 4. Clean up temp midi file
        if os.path.exists(temp_path):
            os.remove(temp_path)

        # Return success with metadata
        return jsonify({
            "success": True,
            "project_name": meta["project_name"],
            "bpm": meta["bpm"],
            "mapping": meta["mapping"]
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/download/lsdj.gb')
def download_rom():
    rom_path = os.path.join("lsdj_rom", "lsdj9_4_2.gb")
    if not os.path.exists(rom_path):
        return "LSDj ROM not found in lsdj_rom/lsdj9_4_2.gb", 404
    return send_file(rom_path, mimetype='application/octet-stream')

@app.route('/download/lsdj.sav')
def download_sav():
    sav_path = "lsdj.sav"
    if not os.path.exists(sav_path):
        return "SRAM Save File not found", 404
    return send_file(sav_path, mimetype='application/octet-stream')

@app.route('/download/lsdsng')
def download_lsdsng():
    lsdsng_path = "trumpet.lsdsng"
    if not os.path.exists(lsdsng_path):
        return "LSDSNG file not found", 404
    return send_file(lsdsng_path, as_attachment=True, download_name="converted.lsdsng")

@app.route('/reset', methods=['POST'])
def reset_project():
    global DEFAULT_META
    meta = initialize_default_midi()
    if meta:
        DEFAULT_META = meta
        return jsonify({"success": True, "metadata": meta})
    return jsonify({"success": False, "error": "Failed to reinitialize default MIDI"}), 500

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="LSDj MIDI Studio Web App")
    parser.add_argument('--port', type=int, default=80, help='Port to run the server on (default: 80)')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='Host interface (default: 0.0.0.0)')
    args = parser.parse_args()

    port = args.port
    host = args.host

    DEFAULT_META = initialize_default_midi()

    try:
        print(f"Attempting to start server on host={host}, port={port}...")
        app.run(host=host, port=port)
    except PermissionError:
        print(f"\n[WARNING] Permission denied to bind to port {port}.")
        print("Ports below 1024 require root privileges (sudo).")
        print("Falling back to port 8080...\n")
        app.run(host=host, port=8080)
    except OSError as e:
        if e.errno == 13: # EACCES / Permission denied
            print(f"\n[WARNING] Permission denied to bind to port {port}.")
            print("Falling back to port 8080...\n")
            app.run(host=host, port=8080)
        else:
            raise e
