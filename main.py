import datetime
import json
import os
import shutil
import subprocess
import threading
import tkinter as tk
from io import BytesIO
from tkinter import ttk, messagebox

import customtkinter as ctk
import pdf2image
from PIL import Image, ImageTk
from PyPDF2 import PdfReader

ctk.set_default_color_theme("dark-blue")


def show_message_auto_close(param, param1, param2):
    pass


class Explorer:
    def __init__(self, master: tk.Tk):
        """Initialize the Explorer class with a master tkinter window."""
        self.quit = None
        self.split_scripts = None

        if not isinstance(master, tk.Tk):
            raise TypeError('master must be a tkinter window')

        self.master = master
        master.title('Explorer')

        with open("variable.json", "r") as f:
            data = json.load(f)

        self.incoming_folder = data["incoming_folder"]
        self.is_dark_mode = True

        self.setup_ui()

    def setup_ui(self):
        """Create and configure UI elements for the application."""
        # Create and place UI elements
        self.theme_button=ctk.CTkButton(self.master, text='Themes', command=self.switch_theme, height=25,
                                            width=60)
        self.theme_button.grid(row=6, column=0, padx=10, pady=10, sticky='ne')

        self.master.geometry("800x600")

        style=ttk.Style()
        style.theme_use("clam")

        self.tree=ttk.Treeview(self.master)
        self.tree.grid(row=1, column=1, padx=15, pady=15, sticky='nsew')

        self.master.grid_columnconfigure(1, weight=1)
        self.master.grid_rowconfigure(1, weight=1)

        # Create a new frame for the preview and pages_label
        self.preview_frame=ttk.Frame(self.master, width=400, height=400)

        self.preview_frame.grid(row=1, column=2, padx=15, pady=15, sticky='n')

        self.preview_canvas=tk.Canvas(self.preview_frame, width=350, height=400)
        self.preview_canvas.grid(row=0, column=0, padx=5, pady=5, sticky='nsew')

        # Add this line of code after creating the preview_canvas
        self.pages_label=ttk.Label(self.preview_frame, text="")
        self.pages_label.grid(row=1, column=0, padx=5, pady=5, sticky="w")

        # Add this line of code after creating the preview_canvas
        self.pages_label=ttk.Label(self.master, text="Pages:")
        self.pages_label.grid(row=1, column=2, padx=20, pady=15, sticky="nw")

        self.view_rx_button=ctk.CTkButton(self.master, text='   View RX   ', command=self.view_rx, state='disabled',
                                              height=70, width=145)
        self.view_rx_button.grid(row=1, column=0, padx=10, pady=10, sticky='nw')

        self.split_scripts_button=ctk.CTkButton(self.master, text='Split Scripts', command=self.split_scripts,
                                                    height=25, width=145)
        self.split_scripts_button.grid(row=2, column=0, padx=10, pady=10, sticky='nw')

        self.rename_button=ctk.CTkButton(self.master, text='NOT a RX\nRename and Move',
                                             command=self.rename, height=25, width=145)
        self.rename_button.grid(row=3, column=0, padx=10, pady=10, sticky='nw')

        self.properties_button=ctk.CTkButton(self.master, text='NOT a RX\n Move',
                                                 command=self.properties, height=25, width=145)
        self.properties_button.grid(row=4, column=0, padx=10, pady=10, sticky='nw')

        self.refresh_lists_button = ctk.CTkButton(self.master, text='Refresh Lists', command=self.refresh_lists,
                                                  height=25, width=145)
        self.refresh_lists_button.grid(row=5, column=0, padx=10, pady=10, sticky='nw')

        self.admin_button=ctk.CTkButton(self.master, text='Admin', command=self.open_admin, height=25, width=60)
        self.admin_button.grid(row=6, column=0, padx=10)

        self.tree.bind('<<TreeviewSelect>>', self.on_treeview_select)
        self.tree.bind('<Double-Button-1>', self.on_double_click)

        self.open_files={}  # Initialize as a dictionary

        # Call update_file_list to populate the Treeview
        self.update_file_list()

        # Set initial theme
        self.set_theme()

    def set_theme(self):
        """Configure theme colors for UI elements."""
        if self.is_dark_mode:
            bg_color="darkgray"
            fg_color="white"
            select_color="darkblue"
            treeview_bg_color="darkgray"
            treeview_fg_color="white"
        else:
            bg_color="white"
            fg_color="black"
            select_color="lightblue"
            treeview_bg_color="white"
            treeview_fg_color="black"

        self.master.configure(bg=bg_color)

        style=ttk.Style()

        style.configure("Treeview", background=treeview_bg_color, fieldbackground=treeview_bg_color,
                        foreground=treeview_fg_color, selectbackground=select_color, selectforeground=treeview_fg_color)

        style.configure("Treeview.Row",
                        background=treeview_bg_color,
                        foreground=treeview_fg_color,
                        fieldbackground=treeview_bg_color)

        style.configure("Treeview.Alternate.Row",
                        background=treeview_bg_color,
                        foreground=treeview_fg_color,
                        fieldbackground=treeview_bg_color)

        style.map("Treeview.Row",
                  background=[("selected", select_color)],
                  foreground=[("selected", treeview_fg_color)])

        style.map("Treeview.Alternate.Row",
                  background=[("selected", select_color)],
                  foreground=[("selected", treeview_fg_color)])

    def on_select(self, event):
        """Handle selection events in the Treeview."""
        item=self.tree.selection()[0]
        filename=self.tree.item(item, 'text')
        filepath=os.path.join(self.incoming_folder, filename)

        # Disable the preview canvas
        self.preview_canvas.configure(state='disabled')

        # Set the background color of the selected item
        self.tree.tag_configure(item, background='darkblue', foreground='white')

        if os.path.isfile(filepath):
            self.view_rx_button.configure(state='normal')
        else:
            self.view_rx_button.configure(state='disabled')

        # Print out the necessary information
        print(f"Selected item: {item}")
        print(f"Selected filename: {filename}")
        print(f"Selected filepath: {filepath}")

        # Use a separate thread to update the preview
        preview_thread=threading.Thread(target=self.update_preview, args=(filepath,))
        preview_thread.start()

        # Enable the preview canvas after the preview has been updated
        self.preview_canvas.configure(state='normal')

    def update_preview(self, filepath):
        """Update the preview of the selected file."""
        print(f"Updating preview for {filepath}")

        if os.path.isfile(filepath):
            _, file_extension=os.path.splitext(filepath)

            if file_extension.lower() in ['.jpg', '.jpeg']:
                self.show_image_preview(filepath)
                self.pages_label.config(text="Pages:")
            elif file_extension.lower() == '.pdf':
                try:
                    images=pdf2image.convert_from_path(filepath, dpi=200, first_page=1, last_page=1)
                    if images:
                        img=images[0]
                        img_io=BytesIO()
                        img.save(img_io, 'PNG')
                        img_io.seek(0)
                        img=Image.open(img_io)
                        self.show_image_preview(img)
                        with open(filepath, "rb") as f:
                            pdf=PdfReader(f)
                            self.pages_label.config(text=f"Pages: {len(pdf.pages)}")
                except Exception as e:
                    print(f"Error updating PDF preview: {e}")
                    self.show_image_preview(None)
                    self.pages_label.config(text="")
            else:
                self.show_image_preview(None)
                self.pages_label.config(text="")
        else:
            self.show_image_preview(None)
            self.pages_label.config(text="")

    def update_file_list(self):
        """Update the file list in the Treeview."""
        # Clear the Treeview
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Add the current files in the incoming_folder
        for filename in os.listdir(self.incoming_folder):
            size=os.path.getsize(os.path.join(self.incoming_folder, filename))
            if os.path.isdir(os.path.join(self.incoming_folder, filename)):
                filetype='Directory'
                with Image.open('folder.png') as img:
                    item_icon=ImageTk.PhotoImage(img)
            else:
                filetype='File'
                with Image.open('file.png') as img:
                    item_icon=ImageTk.PhotoImage(img)
            modified=os.path.getmtime(os.path.join(self.incoming_folder, filename))
            item=self.tree.insert('', 'end', text=filename, image=item_icon, values=(size, filetype))
            self.tree.item(item, image=item_icon)

    def show_image_preview(self, img_source):
        """Show an image preview of the file if possible."""
        self.preview_canvas.delete("all")

        if img_source is not None:
            try:
                if isinstance(img_source, str):
                    img = Image.open(img_source)
                else:
                    img = img_source

                img.thumbnail((400, 400), Image.ANTIALIAS)
                imgtk = ImageTk.PhotoImage(img)

                self.preview_canvas.create_image(0, 0, image=imgtk, anchor="nw")
                self.preview_canvas.image = imgtk
            except Exception as e:
                print("Error updating image preview:", e)
                self.preview_canvas.delete("all")
        else:
            self.preview_canvas.delete("all")

    def switch_theme(self):
        """Toggle between dark and light themes."""
        self.is_dark_mode=not self.is_dark_mode
        self.set_theme()

    def refresh_lists(self):
        with open("variable.json", "r") as file:
            config_data=json.load(file)

        self.incoming_folder=config_data["incoming_folder"]

        self.tree.delete(*self.tree.get_children())  # Clear the treeview first
        for item in os.listdir(self.incoming_folder):
            self.tree.insert('', 'end', text=item,
                             values=(os.path.getsize(os.path.join(self.incoming_folder, item)), "File"))

    def view_rx(self):
        """Open the selected file using a separate script."""
        item=self.tree.selection()[0]
        filename=self.tree.item(item, 'text')
        filepath=os.path.join(self.incoming_folder, filename)

        if filepath in self.open_files:
            # Close the previously opened file
            process=self.open_files[filepath]
            process.terminate()
            process.wait()

        # Open the file again
        script_path=os.path.join(os.path.dirname(__file__), 'test.py')
        process=subprocess.Popen(["python", script_path, filepath])
        self.open_files[filepath]=process

    def on_double_click(self, event):
        # Handle double-click event
        print("Double-click event detected")
        item=self.tree.selection()[0]
        if item:  # Check if an item is selected
            filename=self.tree.item(item, 'text')
            filepath=os.path.join(self.incoming_folder, filename)

            if os.path.isfile(filepath):
                print(f"File path: {filepath}")
                self.view_rx_button.configure(state='normal')
                self.view_rx()
            else:
                self.view_rx_button.configure(state='disabled')

    def on_treeview_select(self, event):
        # Handle Treeview selection event
        selected_items=self.tree.selection()

        if not selected_items:
            print("No item selected.")
            return

        item=selected_items[0]
        filename=self.tree.item(item, 'text')
        filepath=os.path.join(self.incoming_folder, filename)

        # Disable the preview canvas
        self.preview_canvas.configure(state='disabled')

        # Set the background color of the selected item
        self.tree.tag_configure(item, background='darkblue', foreground='white')

        if os.path.isfile(filepath):
            self.view_rx_button.configure(state='normal')
        else:
            self.view_rx_button.configure(state='disabled')

        # Use a separate thread to update the preview
        preview_thread=threading.Thread(target=self.update_preview, args=(filepath,))
        preview_thread.start()

        # Enable the preview canvas after the preview has been updated
        self.preview_canvas.configure(state='normal')

    def show_message_auto_close(title, message, duration):
        def close_message():
            messagebox.destroy()

        messagebox=tk.Toplevel()
        messagebox.title(title)

        label=tk.Label(messagebox, text=message)
        label.pack(padx=10, pady=10)

        messagebox.after(duration, close_message)

    def rename(self):
        def submit_rename():
            new_file_name=entry.get().strip()

            if not new_file_name:
                show_message_auto_close("Error", "No new file name entered.", 2000)
                return

            destination_path=os.path.join(destination_folder_2, new_file_name)

            if os.path.exists(destination_path):
                date_time_suffix=datetime.datetime.now().strftime("%y%m%d%H%M%S")
                new_file_name+=f"_{date_time_suffix}"
                destination_path=os.path.join(destination_folder_2, new_file_name)
                messagebox.showinfo("File name conflict",
                                    f"File with the same name exists. Appending date and time to the file name: {new_file_name}")

            shutil.move(source_path, destination_path)
            rename_popup.destroy()
            self.refresh_lists()

            show_message_auto_close("File moved", f'"{file_name}" moved to "{destination_folder_2}"', 2000)

        with open("variable.json", "r") as file:
            config_data=json.load(file)

        destination_folder_2=config_data["destination_folder_2"]

        selected_item=self.tree.selection()[0]
        file_name=self.tree.item(selected_item, 'text')
        source_path=os.path.join(self.incoming_folder, file_name)

        # Create a popup for renaming
        rename_popup=tk.Toplevel()
        rename_popup.title("Rename file")

        # Calculate the position to center the popup on the screen
        screen_width=rename_popup.winfo_screenwidth()
        screen_height=rename_popup.winfo_screenheight()
        popup_width=300
        popup_height=120

        x_position=(screen_width // 2) - (popup_width // 2)
        y_position=(screen_height // 2) - (popup_height // 2)
        rename_popup.geometry(f"{popup_width}x{popup_height}+{x_position}+{y_position}")

        label=tk.Label(rename_popup, text="Enter new file name:")
        label.pack(padx=10, pady=10)

        entry=tk.Entry(rename_popup)
        entry.pack(padx=10, pady=10)

        submit_button=tk.Button(rename_popup, text="Submit", command=submit_rename)
        submit_button.pack(pady=10)

    def properties(self):
        with open("variable.json", "r") as file:
            config_data=json.load(file)

        destination_folder_2=config_data["destination_folder_2"]

        selected_item=self.tree.selection()[0]
        file_name=self.tree.item(selected_item, 'text')
        source_path=os.path.join(self.incoming_folder, file_name)
        destination_path=os.path.join(destination_folder_2, file_name)

        shutil.move(source_path, destination_path)
        self.refresh_lists()
        
    def open_admin(self):
        """Open the admin script."""
        script_path=os.path.join(os.path.dirname(__file__), 'admin1.py')

        # Call admin script
        subprocess.call(["python", script_path])

if __name__ == '__main__':
    root = tk.Tk()
    explorer = Explorer(root)
    root.protocol('WM_DELETE_WINDOW', explorer.quit)
    root.mainloop()
