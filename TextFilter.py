import re
from TxTToJSON import process_song_file

def filter_important_lines(input_file, output_file):
    song_pack_lines = {}
    current_song_pack = None
    pv_info = {}
    prev_name = None

    # First pass: Collect length information
    with open(input_file, 'r', encoding='utf-8') as file:
        for line in file:
            match = re.match(r'^(pv_\d+)\.difficulty\.(\w+)\.length=(\d+)', line)
            if match:
                pv_id = match.group(1)
                difficulty = match.group(2)
                length = int(match.group(3))
                if pv_id not in pv_info:
                    pv_info[pv_id] = {}
                pv_info[pv_id][difficulty] = length

    # Second pass: Filter lines based on collected information
    with open(input_file, 'r', encoding='utf-8') as file:
        for line in file:
            if line.startswith('song_pack='):
                current_song_pack = line.strip()
                if current_song_pack not in song_pack_lines:
                    song_pack_lines[current_song_pack] = []
                continue

            match = re.match(r'^(pv_\d+)', line)
            if match and '.song_name_en=' in line:
                cur_name = line
                if current_song_pack and prev_name != cur_name:
                    prev_name = cur_name
                    song_pack_lines[current_song_pack].append(line)
            elif match and '.level=' in line:
                pv_id_match = re.match(r'^(pv_\d+)\.difficulty\.(\w+)\.(\d+)\.level=', line)
                if pv_id_match:
                    pv_id = pv_id_match.group(1)
                    difficulty = pv_id_match.group(2)
                    level_num = int(pv_id_match.group(3))
                    if pv_id in pv_info and difficulty in pv_info[pv_id]:
                        length = pv_info[pv_id][difficulty]
                        # Special case for extreme difficulty
                        if difficulty == 'extreme':
                            if (level_num == 1 and length == 2) or (level_num == 0 and length in [1, 2]):
                                song_pack_lines[current_song_pack].append(line)
                        # General case for other difficulties
                        elif length in [1, 2]:
                            song_pack_lines[current_song_pack].append(line)

    # Sorting and writing output
    sorted_lines = []
    difficulty_order = {'easy': 0, 'normal': 1, 'hard': 2, 'extreme': 3, 'exextreme': 4}

    for song_pack, lines in song_pack_lines.items():
        sorted_lines.append(song_pack + '\n')
        lines.sort(key=lambda x: (
            int(re.match(r'pv_(\d+)', x).group(1)) if re.match(r'pv_(\d+)', x) else float('inf'),
            -1 if '.song_name_en=' in x else difficulty_order.get(x.split('.')[2] if len(x.split('.')) > 2 else '', 5)
        ))
        sorted_lines.extend(lines)

    with open(output_file, 'w', encoding='utf-8') as file:
        file.writelines(sorted_lines)

    flat_text = process_song_file(output_file)

    return flat_text
