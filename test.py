import fitz
from PIL import Image, ImageTk
import tkinter as tk
import sys
import os
import json
import shutil
import tkinter.messagebox as messagebox
from tkinter import simpledialog


class PDFViewer:
    canvas_width = 800
    canvas_height = 600

    def __init__(self, parent, filepath, button_frame4=None):
        self.on_right_button_release=None
        self.on_right_button_hold=None
        self.parent = parent
        self.filepath = filepath
        self.document = fitz.open(self.filepath)

        # create a frame to hold the canvas and scrollbars
        frame = tk.Frame(self.parent)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # create a vertical scrollbar
        scrollbar_v = tk.Scrollbar(frame, orient="vertical")
        scrollbar_v.pack(side="right", fill="y")

        # create a horizontal scrollbar
        scrollbar_h = tk.Scrollbar(frame, orient="horizontal")
        scrollbar_h.pack(side="bottom", fill="x")

        # create a frame for the buttons
        button_frame = tk.Frame(frame)
        button_frame.pack(side=tk.LEFT, fill=tk.Y)

        # create a frame for the exit button
        button_frame4=tk.Frame(button_frame)
        button_frame4.pack(side=tk.TOP, pady=10, anchor='w')

        # create an exit button in button_frame4
        exit_button=tk.Button(button_frame4, text="Exit", command=self.parent.quit)
        exit_button.pack(pady=5)

        # create a frame to hold the RX number label and entry widget
        rx_frame=tk.Frame(button_frame)
        rx_frame.pack(side=tk.TOP, pady=10)

        # create an RX number label and entry widget
        rx_label=tk.Label(rx_frame, text="Enter RX number:", font=("TkDefaultFont", 16))
        rx_label.pack(pady=5)
        rx_entry=tk.Entry(rx_frame, font=("TkDefaultFont", 16))
        rx_entry.pack(pady=5)

        # create a button in rx_frame
        button = tk.Button(rx_frame, text="Submit")
        button.pack(pady=5)

        # create a frame for the second button
        button_frame1=tk.Frame(button_frame)
        button_frame1.pack(side=tk.BOTTOM, pady=(10))

        # create a second button in button_frame1
        button2 = tk.Button(button_frame1, text="Split document")
        button2.pack(pady=5)

        # create a frame for the third button
        button_frame2 = tk.Frame(button_frame)
        button_frame2.pack(side=tk.BOTTOM, pady=(10))

        # create a third button in button_frame2
        button3=tk.Button(button_frame2, text='NOT a RX\n Rename Move Document',
                          command=self.move_to_documents_folder)

        button3.pack(pady=5)

        # create a frame for the fourth button
        button_frame3 = tk.Frame(button_frame)
        button_frame3.pack(side=tk.BOTTOM, pady=(10))

        # create a fourth button in button_frame3
        button4=tk.Button(button_frame3, text="'NOT a RX\n Rename Move Document'",
                          command=lambda: self.move_and_rename_to_documents_folder())
        button4.pack(pady=5)

        # create a frame for the navigation buttons
        nav_frame = tk.Frame(button_frame)
        nav_frame.pack(side=tk.TOP, pady=10)

        # create a label to display the total number of pages
        self.total_pages_label = tk.Label(nav_frame, text=f"Total Pages: {len(self.document)}")
        self.total_pages_label.pack(side=tk.LEFT, padx=5)

        # create a "Split" button
        split_button = tk.Button(nav_frame, text="Split", command=self.split_document)
        split_button.pack(side=tk.RIGHT, padx=5)

        # create a canvas
        self.canvas=tk.Canvas(frame, width=self.canvas_width, height=self.canvas_height, bg="white",
                              yscrollcommand=scrollbar_v.set, xscrollcommand=scrollbar_h.set)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # configure the scrollbars
        scrollbar_v.config(command=self.canvas.yview)
        scrollbar_h.config(command=self.canvas.xview)

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

        # create a frame for the navigation buttons
        nav_frame = tk.Frame(button_frame)
        nav_frame.pack(side=tk.TOP, pady=10)

        # create a "Previous" button
        prev_button = tk.Button(nav_frame, text="Previous", command=self.prev_page)
        prev_button.pack(side=tk.LEFT, padx=5)

        # create a "Next" button
        next_button = tk.Button(nav_frame, text="Next", command=self.next_page)
        next_button.pack(side=tk.RIGHT, padx=5)

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
                    output_filename=os.path.join(incoming_folder, f"split_page_{i + 1}.pdf")
                    with fitz.open() as output_pdf:
                        output_pdf.insert_pdf(self.document, from_page=i, to_page=i)
                        output_pdf.save(output_filename)

                # move the original file to destination_folder_2 if the split was successful
                original_file_path=os.path.abspath(self.filepath)
                new_file_path=os.path.join(destination_folder_2, os.path.basename(self.filepath))

                # close the document to release the file handle
                self.document.close()

                os.replace(original_file_path, new_file_path)

                messagebox.showinfo("Success", "The document has been split and the original file has been moved.")
            except Exception as e:
                messagebox.showerror("Split Error", f"An error occurred while splitting the document: {e}")



    def move_to_documents_folder(self):
        try:
            # Load configuration from the JSON file
            with open('variable.json') as config_file:
                config=json.load(config_file)

            destination_folder_2=config["destination_folder_2"]

            # Move the original file to destination_folder_2
            original_file_path=os.path.abspath(self.filepath)
            new_file_path=os.path.join(destination_folder_2, os.path.basename(self.filepath))

            # Print the file paths for debugging
            print(f"Original file path: {original_file_path}")
            print(f"New file path: {new_file_path}")

            # Close the document to release the file handle
            self.document.close()

            os.replace(original_file_path, new_file_path)

            messagebox.showinfo("Success", "The original file has been moved.")
        except Exception as e:
            messagebox.showerror("Move Error", f"An error occurred while moving the document: {e}")

    def move_and_rename_to_documents_folder(self):
        try:
            # Load configuration from the JSON file
            with open('variable.json') as config_file:
                config=json.load(config_file)

            destination_folder_2=config["destination_folder_2"]

            # Get the original file path
            original_file_path=os.path.abspath(self.filepath)

            # Prompt the user to enter a new file name
            new_file_name=simpledialog.askstring("Rename Document", "Enter a new name for the document:")

            # If the user provided a new file name, rename the document and move it to destination_folder_2
            if new_file_name:
                new_file_path=os.path.join(destination_folder_2, new_file_name)

                # Print the file paths for debugging
                print(f"Original file path: {original_file_path}")
                print(f"New file path: {new_file_path}")

                # Close the document to release the file handle
                self.document.close()

                os.replace(original_file_path, new_file_path)

                messagebox.showinfo("Success", "The original file has been renamed and moved.")
            else:
                messagebox.showwarning("No Name Entered", "No new name entered. Operation cancelled.")

        except Exception as e:
            messagebox.showerror("Move and Rename Error",
                                 f"An error occurred while moving and renaming the document: {e}")

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


root=tk.Tk()
app=PDFViewer(root, filepath=sys.argv[1])
root.mainloop()