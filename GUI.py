import os
import zipfile
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
from TextFilter import filter_important_lines


class ModManagerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Diva APWorld Patcher")

        self.mods_folder = ""
        self.apworld_file = ""
        self.folders = []

        # Frame for the buttons
        self.button_frame = tk.Frame(root)
        self.button_frame.pack(pady=10)

        self.select_apworld_button = tk.Button(self.button_frame, text="Select APWorld", command=self.select_apworld)
        self.select_apworld_button.grid(row=0, column=0, padx=5)

        self.select_mods_button = tk.Button(self.button_frame, text="Select Mods Folder", command=self.select_folder)
        # Initially hide the select mods button
        self.select_mods_button.grid(row=0, column=1, padx=5)
        self.select_mods_button.grid_remove()

        self.scrollable_frame = ttk.Frame(root)
        self.canvas = tk.Canvas(self.scrollable_frame)
        self.scrollbar = ttk.Scrollbar(self.scrollable_frame, orient="vertical", command=self.canvas.yview)
        self.checkbox_frame = ttk.Frame(self.canvas)
        self.checkbox_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.checkbox_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.scrollable_frame.pack(fill="both", expand=True)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        self.process_button = tk.Button(root, text="Process Mods", command=self.process_mods)
        # Initially hide the process button
        self.process_button.pack_forget()

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def select_folder(self):
        self.mods_folder = filedialog.askdirectory()
        if self.mods_folder:
            self.list_folders()
            # Show the process button if both a directory and APWorld file are selected
            self.process_button.pack(pady=10)

    def select_apworld(self):
        self.apworld_file = filedialog.askopenfilename(filetypes=[("APWorld files", "*.apworld")])
        if self.apworld_file:
            # Show the select mods button after an APWorld file is selected
            self.select_mods_button.grid()

    def list_folders(self):
        for widget in self.checkbox_frame.winfo_children():
            widget.destroy()
        self.folders = []
        for folder_name in os.listdir(self.mods_folder):
            folder_path = os.path.join(self.mods_folder, folder_name)
            if os.path.isdir(folder_path):
                var = tk.BooleanVar()
                chk = tk.Checkbutton(self.checkbox_frame, text=folder_name, variable=var)
                chk.pack(anchor='w')
                self.folders.append((folder_path, var))

    def process_mods(self):
        output_file_path = os.path.join(os.getcwd(), "combined_mod_pv_db.txt")
        with open(output_file_path, "w", encoding='utf-8', errors='ignore') as output_file:
            for folder_path, var in self.folders:
                if var.get():
                    folder_name = os.path.basename(folder_path)
                    output_file.write(f"song_pack={folder_name}\n")
                    for root, dirs, files in os.walk(folder_path):
                        for file in files:
                            if file == "mod_pv_db.txt":
                                file_path = os.path.join(root, file)
                                try:
                                    with open(file_path, "r", encoding='utf-8', errors='ignore') as input_file:
                                        output_file.write(input_file.read() + "\n")
                                except Exception as e:
                                    messagebox.showerror("Error", f"Failed to read {file_path}: {e}")

        filter_important_lines("combined_mod_pv_db.txt", "filtered_file.txt")

        # Replace moddedData.json in the .apworld file
        self.replace_modded_data()

    def replace_modded_data(self):
        temp_dir = os.path.join(os.getcwd(), "temp_apworld")
        os.makedirs(temp_dir, exist_ok=True)

        try:
            with zipfile.ZipFile(self.apworld_file, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)

            modded_data_path = os.path.join(os.getcwd(), "moddedData.json")
            if not os.path.exists(modded_data_path):
                messagebox.showerror("Error", "moddedData.json not found.")
                return

            # Find the existing moddedData.json within the extracted contents
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    if file == "moddedData.json":
                        apworld_modded_data_path = os.path.join(root, file)
                        shutil.copy(modded_data_path, apworld_modded_data_path)
                        break

            new_apworld_file = self.apworld_file + "_new.apworld"
            with zipfile.ZipFile(new_apworld_file, 'w') as zip_ref:
                for root, dirs, files in os.walk(temp_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, start=temp_dir)
                        zip_ref.write(file_path, arcname)

            os.replace(new_apworld_file, self.apworld_file)
            messagebox.showinfo("Success", "moddedData.json has been replaced successfully.")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to replace moddedData.json: {e}")

        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    root = tk.Tk()
    app = ModManagerApp(root)
    root.mainloop()
