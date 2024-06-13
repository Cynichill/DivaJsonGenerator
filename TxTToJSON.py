import json
import re
from tkinter import messagebox
from Translator import transliterate


def clean_text(text):
    mapping = {
        '＋': 'plus',
        '♂': 'maleSign',
        '♀': 'femaleSign',
        '♠': 'spade',
        '♣': 'club',
        '♥': 'heart',
        '♦': 'diamond',
        '♪': 'musicalNote',
        '♫': 'musicalNotes',
        '☀': 'sun',
        '☁': 'cloud',
        '☂': 'umbrella',
        '☃': 'snowman',
        '☄': 'comet',
        '★': 'star',
        '☆': 'star',
        '☎': 'telephone',
        '☏': 'telephone',
        '☑': 'checkBox',
        '☒': 'checkBox',
        '☞': 'pointingRight',
        '☜': 'pointingLeft',
        '☝': 'pointingUp',
        '☟': 'pointingDown'
        # Add more mappings for special characters here
    }

    special_characters = set(mapping.keys())

    plain_text = []
    word_buffer = ''

    for char in text:
        if char in special_characters:
            if word_buffer:
                plain_text.append(word_buffer)
                word_buffer = ''
            plain_text.append(mapping[char])
        elif char.isalnum():
            word_buffer += char
        elif char.isspace():
            if word_buffer:
                plain_text.append(word_buffer)
                word_buffer = ''
            plain_text.append(' ')

    # Add the last buffered word
    if word_buffer:
        plain_text.append(word_buffer)

    return ''.join(plain_text)


def replace_non_ascii_with_space(text):
    return ''.join(char if ord(char) < 128 or char == '_' else ' ' for char in text)

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
            parts = line.split('=')
            if len(parts) == 2:
                current_pack = parts[1].strip()
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
            parts = line.split('=')
            if len(parts) == 2:
                song_name = parts[1].strip()
                cleaned_song_name = clean_text(song_name)
                cleaned_song_name = transliterate(cleaned_song_name)
                cleaned_song_name = replace_non_ascii_with_space(cleaned_song_name)
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


def process_song_file(input_file_path, output_file_path):
    with open(input_file_path, 'r', encoding='utf-8', errors='ignore') as file:
        data = file.read()

    songs_info, conflicts = extract_song_info(data)

    if conflicts:
        messagebox.showerror("Conflict Detected", f"Conflicts detected for the following pv_ IDs: {conflicts}")
        return

    if songs_info:
        with open(output_file_path, 'w', encoding='utf-8', errors='ignore') as json_file:
            json.dump(songs_info, json_file, indent=4, ensure_ascii=False)
        print("JSON file generated successfully!")
        messagebox.showinfo("Success", f"Json Data Created!")
    else:
        print("Failed to extract song information from the file.")
