import re
from TxTToJSON import process_song_file

def filter_important_lines(input_file, output_file):
    song_pack_lines = {}  # Dictionary to store lines grouped by song_pack

    with open(input_file, 'r', encoding='utf-8') as file:
        current_song_pack = None
        for line in file:
            # Check if the line is a song_pack line
            if line.startswith('song_pack='):
                current_song_pack = line.strip()
                if current_song_pack not in song_pack_lines:
                    song_pack_lines[current_song_pack] = []
                continue

            # Check if the line contains important information
            match = re.match(r'^(pv_\d+)', line)
            if match and ('.level=' in line or '.song_name_en=' in line):
                # Append the line to the corresponding song_pack's list
                if current_song_pack:
                    song_pack_lines[current_song_pack].append(line)

    # Sort lines for each song_pack
    sorted_lines = []
    difficulty_order = {'easy': 0, 'normal': 1, 'hard': 2, 'extreme': 3, 'exextreme': 4}
    for song_pack, lines in song_pack_lines.items():
        sorted_lines.append(song_pack + '\n')  # Add song_pack line with newline
        lines.sort(key=lambda x: (
            int(re.match(r'pv_(\d+)', x).group(1)) if re.match(r'pv_(\d+)', x) else float('inf'),  # Group by PV number
            -1 if '.song_name_en=' in x else difficulty_order.get(x.split('.')[2] if len(x.split('.')) > 2 else '', 5)  # Then sort by difficulty, with song_name_en on top
        ))
        sorted_lines.extend(lines)

    with open(output_file, 'w', encoding='utf-8') as file:
        file.writelines(sorted_lines)

    process_song_file(output_file, "moddedData.json")
