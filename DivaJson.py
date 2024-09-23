import os
import zipfile
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
from TextFilter import filter_important_lines


class ModManagerApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Diva Json Generator")

        self.mods_folder = ""
        self.player_name = ""

        self.folders = []

        self.button_frame = tk.Frame(self.master)
        self.button_frame.pack(pady=10)

        # Label and Entry for entering player name
        self.player_name_label = tk.Label(self.button_frame, text="Enter Player Name here:")
        self.player_name_label.grid(row=0, column=0, padx=5, pady=5)

        self.player_name_entry = tk.Entry(self.button_frame)
        self.player_name_entry.grid(row=0, column=1, padx=5, pady=5)

        self.select_mods_button = self.create_button("Select Mods Folder", self.select_folder, 1, 0)

        self.scrollable_frame = None
        self.canvas = None
        self.scrollbar = None

        self.checkbox_frame = None

        self.setup_scrollable_frame()

        self.process_button = tk.Button(self.master, text="Process Mods", command=self.process_mods)
        self.process_button.pack_forget()

    def create_button(self, text, command, row, column):
        button = tk.Button(self.button_frame, text=text, command=command)
        button.grid(row=row, column=column, padx=5)
        return button

    def setup_scrollable_frame(self):
        self.scrollable_frame = ttk.Frame(self.master)
        self.canvas = tk.Canvas(self.scrollable_frame)
        self.scrollbar = ttk.Scrollbar(self.scrollable_frame, orient="vertical", command=self.canvas.yview)

        self.checkbox_frame = ttk.Frame(self.canvas)
        self.checkbox_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        self.canvas.create_window((0, 0), window=self.checkbox_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.scrollable_frame.pack(fill="both", expand=True)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def select_folder(self):
        self.mods_folder = filedialog.askdirectory()
        if self.mods_folder:
            self.list_folders()
            # Show the process button after selecting a mods folder
            self.process_button.pack(pady=10)

    def list_folders(self):
        # Clear the checkbox frame first
        for widget in self.checkbox_frame.winfo_children():
            widget.destroy()

        self.folders = []

        # Loop through each folder in mods_folder
        for folder_name in os.listdir(self.mods_folder):
            folder_path = os.path.join(self.mods_folder, folder_name)

            # Check if it's a directory
            if os.path.isdir(folder_path):
                # Recursively search for mod_pv_db.txt using os.walk
                for root, dirs, files in os.walk(folder_path):
                    if 'mod_pv_db.txt' in files:
                        # If found, create a checkbox
                        var = tk.BooleanVar()
                        chk = tk.Checkbutton(self.checkbox_frame, text=folder_name, variable=var)
                        chk.pack(anchor='w')
                        self.folders.append((folder_path, var))
                        break  # No need to search further in this directory

    def process_mods(self):
        self.player_name = self.player_name_entry.get().strip()
        if not self.player_name:
            messagebox.showerror("Error", "Please enter a player name.")
            return

        output_file_path = os.path.join(os.getcwd(), "combined_mod_pv_db.txt")
        with open(output_file_path, "w", encoding='utf-8', errors='ignore') as output_file:
            for folder_path, var in self.folders:
                if var.get():
                    folder_name = os.path.basename(folder_path)
                    output_file.write(f"song_pack={folder_name}\n")
                    for master, dirs, files in os.walk(folder_path):
                        for file in files:
                            if file == "mod_pv_db.txt":
                                file_path = os.path.join(master, file)
                                try:
                                    with open(file_path, "r", encoding='utf-8', errors='ignore') as input_file:
                                        output_file.write(input_file.read() + "\n")
                                except Exception as e:
                                    messagebox.showerror("Error", f"Failed to read {file_path}: {e}")

        # Now pass the player name to the filter function
        filter_important_lines("combined_mod_pv_db.txt", "filtered_file.txt", f"{self.player_name}")

if __name__ == "__main__":
    master = tk.Tk()
    app = ModManagerApp(master)
    master.mainloop()
