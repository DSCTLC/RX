import json
import tkinter as tk
from tkinter import messagebox


class VariableEditor:
    def __init__(self, master):
        self.master = master
        master.title('Variable Editor')

        # Set the size of the window
        master.geometry("400x300")

        # Create a frame to hold the entry widgets
        self.frame = tk.Frame(master)
        self.frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create labels and entry widgets for each variable
        self.variables = {}
        row = 0
        with open('variables.json', 'r') as f:
            variables = json.load(f)
        for variable, value in variables.items():
            label = tk.Label(self.frame, text=variable)
            label.grid(row=row, column=0, padx=5, pady=5)
            entry = tk.Entry(self.frame)
            entry.insert(0, value)
            entry.grid(row=row, column=1, padx=5, pady=5)
            self.variables[variable] = entry
            row += 1

        # Create a button to save the changes
        self.save_button = tk.Button(master, text="Save Changes", command=self.save_changes)
        self.save_button.pack(side=tk.BOTTOM, pady=10)

    def save_changes(self):
        # Update the variables dictionary with the new values
        variables = {}
        for variable, entry in self.variables.items():
            variables[variable] = entry.get()

        # Write the updated variables to the file
        with open('variables.json', 'w') as f:
            json.dump(variables, f)

        # Notify the user that changes have been saved
        messagebox.showinfo("Save Successful", "Changes have been saved.")
        self.master.destroy()


class AdminInterface:
    def __init__(self, master):
        self.master = master
        master.title('Admin Interface')

        # Set the size of the window
        master.geometry("400x300")

        # Create a label and entry widget for the password
        password_label = tk.Label(master, text="Password:")
        password_label.pack(pady=10)
        self.password_entry = tk.Entry(master, show="*")
        self.password_entry.pack(pady=10)

        # Create a button to submit the password
        submit_button = tk.Button(master, text="Submit", command=self.submit_password)
        submit_button.pack()

    def submit_password(self):
        password = self.password_entry.get()
        if password == "GPT4":
            self.master.destroy()
            root = tk.Tk()
            app = VariableEditor(root)
            root.mainloop()
        else:
            messagebox.showerror("Incorrect Password", "The password you entered is incorrect.")


root = tk.Tk()
app = AdminInterface(root)
root.mainloop()
