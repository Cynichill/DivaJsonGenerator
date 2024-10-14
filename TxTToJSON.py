import re
from tkinter import messagebox
from SymbolFixer import fix_song_name


def extract_song_info(data):
    song_packs = {}
    current_song = None
    current_name = ""
    current_pack = None
    line_counts = {}
    conflicts = []

    lines = data.split('\n')

    for line in lines:
        if 'song_pack=' in line:
            parts = line.split('=', 1)
            if len(parts) == 2:
                current_pack = parts[1].strip()
                current_pack = fix_song_name(current_pack)
                if current_pack not in song_packs:
                    song_packs[current_pack] = []

        match = re.match(r'^pv_(\d+)', line)
        if match:
            song_number = int(match.group(1))
            current_song = {
                'songID': str(song_number),
                'songName': current_name,
                'difficulties': []
            }
            if current_pack:
                song_packs[current_pack].append(current_song)

            pv_id = match.group(0)
            if pv_id not in line_counts:
                line_counts[pv_id] = 0
            line_counts[pv_id] += 1

            if line_counts[pv_id] > 6:
                conflicts.append(pv_id)

        if 'song_name_en=' in line:
            parts = line.split('=', 1)
            if len(parts) == 2:
                song_name = parts[1].strip()
                cleaned_song_name = fix_song_name(song_name)
                current_song['songName'] = cleaned_song_name
                current_name = cleaned_song_name

        if line.startswith('pv_') and '.difficulty.' in line and '.level=' in line:
            parts = line.split('.')
            difficulty = parts[-3]
            ex_check = parts[-2]
            if ex_check == "1":
                difficulty = "exExtreme"
            rating_str = parts[-1]
            match = re.match(r'level=PV_LV_(\d+)_(\d+)', rating_str)
            if match:
                main_number = int(match.group(1))
                decimal_part = int(match.group(2)) / 10 if match.group(2) else 0.0
                rating = main_number + decimal_part
                if rating.is_integer():
                    rating = int(rating)
                current_song['difficulties'].append({
                    'difficulty': '[' + difficulty.upper() + ']',
                    'difficultyRating': str(rating)
                })

    flattened_packs = []

    for pack_name, pack_songs in song_packs.items():
        flattened_pack = {'packName': pack_name, 'songs': []}
        for song in pack_songs:
            for difficulty_info in song['difficulties']:
                flattened_song = {
                    'songID': song['songID'],
                    'songName': song['songName'],
                    'difficulty': difficulty_info['difficulty'],
                    'difficultyRating': difficulty_info['difficultyRating']
                }
                flattened_pack['songs'].append(flattened_song)
        flattened_packs.append(flattened_pack)

    return flattened_packs, conflicts


def process_song_file(input_file_path):
    with open(input_file_path, 'r', encoding='utf-8', errors='ignore') as file:
        data = file.read()

    songs_info, conflicts = extract_song_info(data)

    if conflicts:
        messagebox.showerror("Conflict Detected", f"Conflicts detected for the following pv_ IDs: {conflicts}")
        return

    if songs_info:
        compressed_data = compress_song_data(songs_info)
        return compressed_data


def compress_song_data(json_data):
    # Create a dictionary to map difficulties to list indices
    difficulty_map = {
        "[EASY]": 0,
        "[NORMAL]": 1,
        "[HARD]": 2,
        "[EXTREME]": 3,
        "[EXEXTREME]": 4
    }

    # Dictionary to hold the grouped song data
    grouped_songs = {}

    # Iterate through each pack in the JSON data
    for pack in json_data:
        pack_name = pack["packName"]

        # Iterate through each song in the song list
        for song in pack["songs"]:
            song_id = song["songID"]
            difficulty = song["difficulty"]
            rating = float(song["difficultyRating"])

            # If this is the first time we're seeing this song, initialize its entry
            if song_id not in grouped_songs:
                # Initialize with packName, songName, songID, and 5 zeros for difficulties
                grouped_songs[song_id] = [pack_name, song["songName"], song_id] + [0] * 5

            # Place the rating in the correct position based on the difficulty
            grouped_songs[song_id][difficulty_map[difficulty] + 3] = rating

    # Convert the dictionary to a string with comma-separated values
    compressed_data = ""
    for song_data in grouped_songs.values():
        # Convert each rating to an integer if it's a whole number, otherwise keep it as a float
        formatted_song_data = [
            str(data) if not isinstance(data, float) or data % 1 != 0 else str(int(data))
            for data in song_data
        ]

        # Join each song's data into a string surrounded by brackets and add to compressed_data
        compressed_data += "[" + ",".join(formatted_song_data) + "]"
    compressed_data = '"' + compressed_data + '"'

    return compressed_data.strip()  # Remove the trailing newline
