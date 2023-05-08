import json
import os
import sys
import tkinter as tk
import tkinter.messagebox as messagebox
from tkinter import simpledialog
import time
import fitz
import datetime
import shared_state
import shutil
from PIL import Image, ImageTk, ImageDraw, ImageFont
import itertools
import traceback


class PDFViewer:
    canvas_width = 800
    canvas_height = 600

    def __init__(self, parent, filepath=None, button_frame3=None):
        self.on_right_button_release=None
        self.on_right_button_hold=None
        self.parent=parent
        self.filepath=filepath
        self.document=fitz.open(self.filepath)

        # create a frame to hold the canvas and scrollbars
        frame=tk.Frame(self.parent)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # create a vertical scrollbar
        scrollbar_v=tk.Scrollbar(frame, orient="vertical")
        scrollbar_v.pack(side="right", fill="y")

        # create a horizontal scrollbar
        scrollbar_h=tk.Scrollbar(frame, orient="horizontal")
        scrollbar_h.pack(side="bottom", fill="x")

        # create a frame for the buttons
        button_frame=tk.Frame(frame)
        button_frame.pack(side=tk.LEFT, fill=tk.Y)

        # create a frame for the exit button
        button_frame4 = tk.Frame(button_frame)
        button_frame4.pack(side=tk.TOP, pady=10, anchor='w')

        # create an exit button in button_frame4
        exit_button = tk.Button(button_frame4, text="Exit", command=self.parent.quit, bg="lightblue")
        exit_button.pack(pady=5)

        exit_button.bind("<Enter>", lambda event: self.on_enter(exit_button))
        exit_button.bind("<Leave>", lambda event: self.on_leave(exit_button))

        # create a frame to hold the RX number label and entry widget
        rx_frame = tk.Frame(button_frame)
        rx_frame.pack(side=tk.TOP, pady=10)


        # create a frame to hold the RX number label and entry widget
        rx_frame=tk.Frame(button_frame)
        rx_frame.pack(side=tk.TOP, pady=10)

        # create an RX number label and entry widget
        rx_label=tk.Label(rx_frame, text="Enter RX number:", font=("TkDefaultFont", 16))
        rx_label.pack(pady=5)
        rx_entry=tk.Entry(rx_frame, font=("TkDefaultFont", 16))
        rx_entry.pack(pady=5)

        # create a button in rx_frame
        button=tk.Button(rx_frame, text="Submit",
                         command=lambda: self.rename_and_move_with_rx_number(rx_entry.get(), rx_entry), bg="lightblue")
        button.pack(pady=5)

        button.bind("<Enter>", lambda event: self.on_enter(button))
        button.bind("<Leave>", lambda event: self.on_leave(button))

        # create a frame for the second button
        button_frame1=tk.Frame(button_frame)
        button_frame1.pack(side=tk.TOP, pady=(10))

        # create a second button in button_frame1
        button2=tk.Button(button_frame1, text="Split document", command=self.split_document, bg="lightblue")
        button2.pack(pady=5)

        button2.bind("<Enter>", lambda event: self.on_enter(button2))
        button2.bind("<Leave>", lambda event: self.on_leave(button2))

        # create a frame for the third button
        button_frame2 = tk.Frame(button_frame)
        button_frame2.pack(side=tk.TOP, pady=(10))

        # create a third button in button_frame2
        button3=tk.Button(button_frame2, text="'NOT a RX\n Move to Documents Folder'",
                          command=self.move_to_documents_folder, bg="lightblue")
        button3.pack(pady=5)

        button3.bind("<Enter>", lambda event: self.on_enter(button3))
        button3.bind("<Leave>", lambda event: self.on_leave(button3))

        # create a frame for the fourth button
        button_frame3 = tk.Frame(button_frame)
        button_frame3.pack(side=tk.TOP, pady=(10))

        # create a fourth button in button_frame3
        button4=tk.Button(button_frame3, text="'NOT a RX\n Rename Move Document'",
                          command=lambda: self.move_and_rename_to_documents_folder(), bg="lightblue")
        button4.pack(pady=5)

        button4.bind("<Enter>", lambda event: self.on_enter(button4))
        button4.bind("<Leave>", lambda event: self.on_leave(button4))

        # create a frame for the navigation buttons
        nav_frame = tk.Frame(button_frame)
        nav_frame.pack(side=tk.TOP, pady=10)

        # create a canvas
        self.canvas=tk.Canvas(frame, width=self.canvas_width, height=self.canvas_height, bg="white",
                              yscrollcommand=scrollbar_v.set, xscrollcommand=scrollbar_h.set)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Add the new frame and label for self.total_pages_2
        self.info_frame=tk.Frame(self.canvas, bg="white")

        # Place the new frame on top of the canvas
        self.info_frame.place(x=0, y=0)


        # configure the scrollbars
        scrollbar_v.config(command=self.canvas.yview)
        scrollbar_h.config(command=self.canvas.xview)
        self.number_of_pages=len(self.document)
        self.current_page=0
        self.zoom_factor=1.0
        self.display_current_page()

        self.canvas.bind("<Configure>", self.on_canvas_resized)
        self.canvas.bind("<MouseWheel>", self.on_mousewheel)
        self.canvas.bind("<Button-3>", self.on_right_click)
        self.canvas.bind("<Double-Button-1>", self.on_double_click)
        self.canvas.bind("<ButtonPress-1>", self.on_mouse_down)
        self.canvas.bind("<B1-Motion>", self.on_mouse_move)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)

        # initialize variables for grabbing operation
        self.grabbing=False
        self.hand_image=None

        self.display_current_page()
        self.update_total_pages_label()

        # create a "Previous" button
        prev_button=tk.Button(nav_frame, text="Previous", command=self.prev_page, bg="lightblue")
        prev_button.pack(side=tk.LEFT, padx=5)

        prev_button.bind("<Enter>", lambda event: self.on_enter(prev_button))
        prev_button.bind("<Leave>", lambda event: self.on_leave(prev_button))

        # create a "Next" button
        next_button=tk.Button(nav_frame, text="Next", command=self.next_page, bg="lightblue")
        next_button.pack(side=tk.RIGHT, padx=5)

        next_button.bind("<Enter>", lambda event: self.on_enter(next_button))
        next_button.bind("<Leave>", lambda event: self.on_leave(next_button))

        with open("variables.json") as f:
            variables=json.load(f)

        self.script_length=int(variables["script_length"])
        self.destination_folder_1=variables["destination_folder_1"]

        self.buttons_frame=tk.Frame(self.info_frame)
        self.buttons_frame.pack()

    def create_image_with_page_count(self, img, page_count):
        draw=ImageDraw.Draw(img)
        font_size=50
        font=ImageFont.truetype("arial.ttf", font_size)
        text=f"{page_count} pages"
        text_width, text_height=draw.textsize(text, font=font)
        x, y=(img.width - text_width) // 2, (img.height - text_height) // 2
        draw.text((x, y), text, font=font, fill="white")
        return img

    def on_enter(self, button):
        button['background'] = '#5CA5CC'

    def on_leave(self, button):
        button['background'] = 'lightblue'

    def update_shared_state_file(self):
        with open("shared_state.json", "r") as file:
            shared_state=json.load(file)

        shared_state["update_file_list_flag"]=False

        with open("shared_state.json", "w") as file:
            json.dump(shared_state, file)

    def update_shared_state_file(self):
        with open("shared_state.json", "r") as file:
            shared_state=json.load(file)

        shared_state["update_file_list_flag"]=True

        with open("shared_state.json", "w") as file:
            json.dump(shared_state, file)

    def split_document(self):
        if len(self.document) == 1:
            messagebox.showinfo("Split Error", "Only one page, why split?")
        else:
            try:
                # load configuration from the JSON file
                with open('variable.json') as config_file:
                    config=json.load(config_file)

                incoming_folder=config["incoming_folder"]
                destination_folder_2=config["destination_folder_2"]

                # split the document into separate pages
                for i in range(len(self.document)):
                    base_output_filename=f"split_page_{i + 1}.pdf"
                    output_filename=os.path.join(incoming_folder, base_output_filename)

                    # Check for existing files and add a suffix to avoid overwriting
                    for suffix in itertools.chain(('',), ('_{}'.format(j) for j in itertools.count(1))):
                        candidate_output_filename=os.path.join(incoming_folder,
                                                               f"{os.path.splitext(base_output_filename)[0]}{suffix}.pdf")
                        if not os.path.exists(candidate_output_filename):
                            output_filename=candidate_output_filename
                            break

                    with fitz.open() as output_pdf:
                        output_pdf.insert_pdf(self.document, from_page=i, to_page=i)
                        output_pdf.save(output_filename)

                # move the original file to destination_folder_2 if the split was successful
                original_file_path=os.path.abspath(self.filepath)
                new_file_path=os.path.join(destination_folder_2, os.path.basename(self.filepath))

                # Check for existing files in destination_folder_2 and add a suffix to avoid overwriting
                for suffix in itertools.chain(('',), ('_{}'.format(j) for j in itertools.count(1))):
                    candidate_new_file_path=os.path.join(destination_folder_2,
                                                         f"{os.path.splitext(os.path.basename(self.filepath))[0]}{suffix}{os.path.splitext(self.filepath)[1]}")
                    if not os.path.exists(candidate_new_file_path):
                        new_file_path=candidate_new_file_path
                        break

                # close the document to release the file handle
                self.document.close()

                os.replace(original_file_path, new_file_path)

                # Update shared state file
                self.update_shared_state_file()

                # Update showlist
                folder_contents=os.listdir(incoming_folder)
                with open('showlist.json', 'w') as showlist_file:
                    json.dump(folder_contents, showlist_file)

                with open('showlist.json', 'r') as showlist_file:
                    showlist=json.load(showlist_file)

                if showlist:
                    next_file_path=os.path.join(incoming_folder, showlist[0])  # Define next_file_path here
                    self.filepath=next_file_path
                    time.sleep(0.2)  # Add a small delay
                    self.load_new_file(next_file_path)
                    self.display_current_page()
                else:
                    messagebox.showwarning("No Files", "There are no more files to display.")

            except Exception as e:
                messagebox.showerror("Split Error", f"An error occurred while splitting the document: {e}")

    def open_new_file(self, new_filepath):
        # Your code to load the new PDF file
        self.document = ...  # Load the new file
        self.update_total_pages_label()

    import itertools

    def split_document(self):
        if len(self.document) == 1:
            messagebox.showinfo("Split Error", "Only one page, why split?")
        else:
            try:
                # load configuration from the JSON file
                with open('variable.json') as config_file:
                    config=json.load(config_file)

                incoming_folder=config["incoming_folder"]
                destination_folder_2=config["destination_folder_2"]

                # get the original document name without the extension
                original_document_name=os.path.splitext(os.path.basename(self.filepath))[0]

                # split the document into separate pages
                for i in range(len(self.document)):
                    base_output_filename=f"{original_document_name}_Split_{i + 1}.pdf"

                    # Check for existing files and add a suffix to avoid overwriting
                    for suffix in itertools.chain(('',), ('_{}'.format(j) for j in itertools.count(1))):
                        candidate_output_filename=os.path.join(incoming_folder,
                                                               f"{os.path.splitext(base_output_filename)[0]}{suffix}{os.path.splitext(base_output_filename)[1]}")
                        if not os.path.exists(candidate_output_filename):
                            output_filename=candidate_output_filename
                            break

                    with fitz.open() as output_pdf:
                        output_pdf.insert_pdf(self.document, from_page=i, to_page=i)
                        output_pdf.save(output_filename)

                # move the original file to destination_folder_2 if the split was successful
                original_file_path=os.path.abspath(self.filepath)

                # Check for existing files in destination_folder_2 and add a suffix to avoid overwriting
                for suffix in itertools.chain(('',), ('_{}'.format(j) for j in itertools.count(1))):
                    candidate_new_file_path=os.path.join(destination_folder_2,
                                                         f"{os.path.splitext(os.path.basename(self.filepath))[0]}{suffix}{os.path.splitext(self.filepath)[1]}")
                    if not os.path.exists(candidate_new_file_path):
                        new_file_path=candidate_new_file_path
                        break

                # close the document to release the file handle
                self.document.close()

                shutil.move(original_file_path, new_file_path)

                messagebox.showinfo("Success", "The document has been split and the original file has been moved.")

                # Update shared state file
                self.update_shared_state_file()

                # Update showlist
                folder_contents=os.listdir(incoming_folder)
                with open('showlist.json', 'w') as showlist_file:
                    json.dump(folder_contents, showlist_file)

                with open('showlist.json', 'r') as showlist_file:
                    showlist=json.load(showlist_file)

                if showlist:
                    next_file_path=os.path.join(incoming_folder, showlist[0])  # Define next_file_path here
                    self.filepath=next_file_path
                    time.sleep(0.2)  # Add a small delay
                    self.load_new_file(next_file_path)  # Use next_file_path directly
                    self.display_current_page()
                else:
                    messagebox.showwarning("No Files", "There are no more files to display.")

            except Exception as e:
                messagebox.showerror("Split Error", f"An error occurred while splitting the document: {e}")

    def set_update_flag(self):
        shared_state.update_file_list_flag=True

    def open_file(self):
        # Close the current document if one is already open
        if self.document:
            self.document.close()
        # Open the document at the current file path
        self.document=fitz.open(self.filepath)
        # Display the first page of the document
        self.display_current_page()
        # Update the total pages label
        self.update_total_pages_label()

    def load_new_file(self, filepath=None, nav_frame=None):
        if filepath:
            self.filepath=filepath

        # Load the new file
        self.document=fitz.open(self.filepath)
        self.number_of_pages=len(self.document)

        self.update_total_pages_label()

        # No need to call load_new_file here, as it would lead to recursion


        self.current_page=0

    def rename_and_move_with_rx_number(self, rx_number, rx_entry=None):
        if not rx_number:
            messagebox.showwarning("Warning", "No file name entered.")
            return

        if not rx_number.isdigit():
            messagebox.showerror("Error", "Invalid input. RX number should only contain digits.")
            return

        try:
            with open('variables.json') as config_file:
                config=json.load(config_file)

            self.script_length=int(config["script_length"])
            self.destination_folder_1=config["destination_folder_1"]

            original_file_path=os.path.abspath(self.filepath)
            _, file_extension=os.path.splitext(original_file_path)

            if self.script_length != 0:
                if len(rx_number) > self.script_length:
                    messagebox.showerror("Error", "Script number too long.")
                    return
                elif len(rx_number) < self.script_length:
                    result=messagebox.askokcancel("Warning",
                                                  f"Not correct RX number length. Adding leading zeros: {rx_number.zfill(self.script_length)}")
                    if not result:
                        return
                    rx_number=rx_number.zfill(self.script_length)

            padded_rx_number=rx_number
            timestamp=datetime.datetime.now().strftime("_%y%m%d%H%M%S")
            new_file_name=f"{padded_rx_number}{timestamp}{file_extension}"
            new_file_path=os.path.join(self.destination_folder_1, new_file_name)

            self.open_file()
            self.set_update_flag()
            self.document.close()

            shutil.move(original_file_path, new_file_path)

            messagebox.showinfo("Success", "The original file has been renamed and moved.")
            rx_entry.delete(0, 'end')  # Add this line to clear the entry field
            self.update_shared_state_file()

            # Refresh the view for the next file
            incoming_folder=config["incoming_folder"]
            folder_contents=os.listdir(incoming_folder)
            with open('showlist.json', 'w') as showlist_file:
                json.dump(folder_contents, showlist_file)

            with open('showlist.json', 'r') as showlist_file:
                showlist=json.load(showlist_file)

            if showlist:
                next_file_path=os.path.join(incoming_folder, showlist[0])
                self.load_new_file(next_file_path)
            else:
                print("No more files to display")
                response=messagebox.showwarning("No Files", "There are no more files to display.")
                if response == 'ok':
                    sys.exit()


        except Exception as e:
            messagebox.showerror("Rename and Move Error",
                                 f"An error occurred while renaming and moving the document: {e}")

    def update_total_pages_label(self):
        if not hasattr(self, "total_pages_label"):
            self.total_pages_label=tk.Label(self.info_frame, text=f"Total Pages: {len(self.document)}", bg="white",
                                            font=("Arial", 14))  # Change font size here
            self.total_pages_label.pack(padx=10, pady=10)  # Change padding values here
        self.total_pages_label.config(text=f"Total Pages: {len(self.document)}")

    def move_to_documents_folder(self):
        try:
            print("Reading variable.json")
            with open('variable.json') as config_file:
                config=json.load(config_file)

            print("Setting folder paths")
            destination_folder_2=config["destination_folder_2"]
            incoming_folder=config["incoming_folder"]

            original_file_path=os.path.abspath(self.filepath)
            file_name, file_extension=os.path.splitext(os.path.basename(self.filepath))

            timestamp=datetime.datetime.now().strftime("%y%m%d%H%M%S")
            new_file_name=f"{file_name}_{timestamp}{file_extension}"

            new_file_path=os.path.join(destination_folder_2, new_file_name)

            print(f"Original file path: {original_file_path}")
            print(f"New file path: {new_file_path}")

            print("Opening and closing file")
            self.open_file()
            self.set_update_flag()
            self.document.close()

            print("Moving file")
            os.replace(original_file_path, new_file_path)

            print("Showing success messagebox")
            messagebox.showinfo("Success", "The original file has been moved.")
            print("Success messagebox shown")

            print("Updating shared state file")
            self.update_shared_state_file()

            print("Updating showlist.json")
            folder_contents=os.listdir(incoming_folder)
            with open('showlist.json', 'w') as showlist_file:
                json.dump(folder_contents, showlist_file)

            print("Reading showlist.json")
            with open('showlist.json', 'r') as showlist_file:
                showlist=json.load(showlist_file)

            print("Showlist after moving the file:", showlist)

            if showlist:
                print("Loading next file")
                next_file_path=os.path.join(incoming_folder, showlist[0])
                self.filepath=next_file_path
                time.sleep(0.2)  # Add a small delay
                self.load_new_file(next_file_path)
                print("New file loaded")
            else:
                print("No more files to display")
                response=messagebox.showwarning("No Files", "There are no more files to display.")
                if response == 'ok':
                    sys.exit()

        except Exception as e:
            print("An error occurred:", e)
            messagebox.showerror("Move Error", f"An error occurred while moving the document: {e}")

        self.display_current_page()

    def move_and_rename_to_documents_folder(self):
        try:
            with open('variable.json') as config_file:
                config=json.load(config_file)

            destination_folder_2=config["destination_folder_2"]
            incoming_folder=config["incoming_folder"]

            original_file_path=os.path.abspath(self.filepath)

            # Get the file extension from the original file path
            _, file_extension=os.path.splitext(original_file_path)

            new_file_name=simpledialog.askstring("Rename Document", "Enter a new name for the document:")

            if new_file_name:
                # Add a timestamp to the new file name
                timestamp=datetime.datetime.now().strftime("_%y%m%d%H%M%S")
                new_file_name_with_timestamp=new_file_name + timestamp + file_extension
                new_file_path=os.path.join(destination_folder_2, new_file_name_with_timestamp)

                self.open_file()
                self.set_update_flag()
                self.document.close()

                os.replace(original_file_path, new_file_path)

                messagebox.showinfo("Success", "The original file has been renamed and moved.")
                self.update_shared_state_file()

                # Update showlist
                folder_contents=os.listdir(incoming_folder)
                with open('showlist.json', 'w') as showlist_file:
                    json.dump(folder_contents, showlist_file)

                with open('showlist.json', 'r') as showlist_file:
                    showlist=json.load(showlist_file)

            if showlist:
                next_file_path=os.path.join(incoming_folder, showlist[0])
                self.load_new_file(next_file_path)
            else:
                print("No more files to display")
                response=messagebox.showwarning("No Files", "There are no more files to display.")
                if response == 'ok':
                    sys.exit()

        except Exception as e:
            messagebox.showerror("Move and Rename Error",
                                 f"An error occurred while moving and renaming the document: {e}")

        self.display_current_page()

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.display_current_page()

    def next_page(self):
        if self.current_page < len(self.document) - 1:
            self.current_page += 1
            self.display_current_page()


    def display_current_page(self):
        page=self.document[self.current_page]
        zoom_factor=self.canvas.winfo_width() / page.mediabox[2] * self.zoom_factor
        pix=page.get_pixmap(matrix=fitz.Matrix(zoom_factor, zoom_factor))
        img=Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        img=ImageTk.PhotoImage(img)
        self.canvas.delete('all')
        self.canvas.create_image(0, 0, anchor='nw', image=img)
        self.canvas.image=img
        page_width, page_height=page.mediabox[2], page.mediabox[3]
        self.canvas.configure(scrollregion=(0, 0, page_width * zoom_factor, page_height * zoom_factor))
        self.canvas.scale("all", 0, 0, self.zoom_factor, self.zoom_factor)

    def on_canvas_resized(self, event):
        self.display_current_page()


    def on_mousewheel(self, event):
        # scroll the canvas vertically depending on the direction of the mouse wheel
        if event.delta > 0:
            self.canvas.yview_scroll(-1, "units")
        else:
            self.canvas.yview_scroll(1, "units")

    def on_double_click(self, event):
        # get the coordinates of the mouse click
        x, y=event.x, event.y

        # calculate the position of the mouse click relative to the canvas
        canvas_x=self.canvas.canvasx(x)
        canvas_y=self.canvas.canvasy(y)

        # calculate the new zoom factor
        self.zoom_factor*=1.2

        # limit the zoom factor to a maximum value (e.g., 5.0)
        if self.zoom_factor > 5:
            self.zoom_factor=5

        # zoom in towards the location of the mouse click
        self.canvas.scale("all", canvas_x, canvas_y, 1.2, 1.2)

        # redraw the current page
        self.display_current_page()

        # adjust the scroll region to fit the new size of the canvas
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

        # scroll the canvas to center on the double-click location
        canvas_width=self.canvas.winfo_width()
        canvas_height=self.canvas.winfo_height()
        scroll_x=min(max(canvas_x - canvas_width / 2, 0), self.canvas.canvasx(self.canvas.winfo_width()))
        scroll_y=min(max(canvas_y - canvas_height / 2, 0), self.canvas.canvasy(self.canvas.winfo_height()))
        self.canvas.xview_moveto(scroll_x / self.canvas.canvasx(self.canvas.winfo_width()))
        self.canvas.yview_moveto(scroll_y / self.canvas.canvasy(self.canvas.winfo_height()))


    def on_right_click(self, event):
        # get the coordinates of the mouse click
        x, y=event.x, event.y

        # calculate the new zoom factor
        self.zoom_factor/=1.2

        # limit the zoom factor to a minimum value (e.g., 0.2)
        if self.zoom_factor < 0.2:
            self.zoom_factor=0.2

        # zoom out from the point where the mouse was clicked
        self.canvas.scale("all", x, y, 1 / 1.2, 1 / 1.2)

        # redraw the current page
        self.display_current_page()

        # adjust the scroll region to fit the new size of the canvas
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def on_mouse_down(self, event):
        # save the starting position of the mouse
        self.start_x, self.start_y=event.x, event.y

        # save the current scroll region
        self.start_scroll_region=self.canvas.bbox("all")

    def on_mouse_move(self, event):
        # calculate the distance that the mouse has moved
        delta_x, delta_y=event.x - getattr(self, 'start_x', event.x), event.y - getattr(self, 'start_y', event.y)

        # move the canvas by the same amount
        self.canvas.move("all", delta_x, delta_y)

        # update the starting position of the mouse
        self.start_x, self.start_y=event.x, event.y


    def on_mouse_up(self, event):
        if event.num == 3:
            if self.grabbing:
                # remove the hand image
                self.canvas.delete(self.hand_image)

                # reset the flag
                self.grabbing=False
            else:
                # update the current scroll region
                self.current_scroll_region=self.canvas.bbox("all")

                # if the canvas hasn't moved, it was just a click, so do nothing
                if self.current_scroll_region == self.start_scroll_region:
                    return

                # calculate the difference in scroll regions
                delta_x, delta_y=self.start_scroll_region[0] - self.current_scroll_region[0], \
                                 self.start_scroll_region[1] - self.current_scroll_region[1]

                # adjust the scroll region to compensate for the movement
                self.canvas.configure(scrollregion=(self.canvas.bbox("all")[0] - delta_x,
                                                    self.canvas.bbox("all")[1] - delta_y,
                                                    self.canvas.bbox("all")[2] - delta_x,
                                                    self.canvas.bbox("all")[3] - delta_y))

    def on_canvas_resized(self, event):
        # redraw the current page
        self.display_current_page()

        # if the canvas has been resized, adjust the scroll region to fit the new size
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def bind_events(self):
        self.canvas.bind("<Configure>", self.on_canvas_resized)
        self.canvas.bind("<MouseWheel>", self.on_mousewheel)
        self.canvas.bind("<Button-3>", self.on_mouse_down)
        self.canvas.bind("<B3-Motion>", self.on_mouse_move)
        self.canvas.bind("<ButtonRelease-3>", self.on_mouse_up)
        self.canvas.bind("<B2-Motion>", self.on_right_button_hold)
        self.canvas.bind("<ButtonRelease-2>", self.on_right_button_release)


if __name__ == '__main__':
    root = tk.Tk()
    if len(sys.argv) > 1:
        app = PDFViewer(root, filepath=sys.argv[1])
    else:
        app = PDFViewer(root)
    root.mainloop()
