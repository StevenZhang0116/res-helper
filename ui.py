import tkinter as tk
from tkinter import ttk
import subprocess

def run_command():
    rootfolder = e_rootfolder_var.get()
    key = e_key_var.get()
    index = cb_index_var.get()
    ioindex = cb_ioindex_var.get()
    databaseindex = cb_databaseindex_var.get()
    imgout = e_imgout_var.get()

    command = ["python", "article_search.py", "--rootfolder", rootfolder, "--key", key, "--index", index]
    
    if index == "0":
        command.extend(["--ioindex", ioindex, "--databaseindex", databaseindex, "--imgout", imgout])
    
    # code could run recursively
    subprocess.Popen(command)

def create_label_entry(frame, label_text, variable):
    row_frame = ttk.Frame(frame)
    row_frame.pack(fill=tk.X, pady=5)
    ttk.Label(row_frame, text=label_text, background=frame_color, font=('Verdana', 14)).pack(side=tk.LEFT)
    ttk.Entry(row_frame, textvariable=variable, font=('Verdana', 14)).pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)

def create_option_menu(frame, label_text, variable, options):
    row_frame = ttk.Frame(frame)
    row_frame.pack(fill=tk.X, pady=5)
    ttk.Label(row_frame, text=label_text, background=frame_color, font=('Verdana', 14)).pack(side=tk.LEFT)
    ttk.OptionMenu(row_frame, variable, variable.get(), *options).pack(side=tk.LEFT, padx=10)

def quit_application():
    root.destroy()

    
root = tk.Tk()
root.title("Document Handling Interface")

bg_color = "#f3f4f6"
frame_color = "#ffffff"
button_color = "#4a7a8c"
text_color = "#000000"
entry_bg = "#ffffff"
button_text_color = "#ffffff"

style = ttk.Style(root)
style.theme_use('clam')

style.configure('TFrame', background=frame_color)
style.configure('TLabel', background=frame_color, foreground=text_color, font=('Verdana', 14))
style.configure('TEntry', background=entry_bg, foreground=text_color, font=('Verdana', 14))
style.configure('TButton', background=button_color, foreground=button_text_color, font=('Verdana', 14))
style.map('TButton', background=[('active', button_color)], foreground=[('active', button_text_color)])

root.configure(background=bg_color)

window_width = 600
window_height = 400
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
center_x = int(screen_width/2 - window_width / 2)
center_y = int(screen_height/2 - window_height / 2)
root.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')

main_frame = ttk.Frame(root)
main_frame.pack(expand=True, fill=tk.BOTH)

center_frame = ttk.Frame(main_frame)
center_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

e_rootfolder_var = tk.StringVar(value="../paper/")
e_key_var = tk.StringVar()
cb_index_var = tk.StringVar(value="0")
cb_ioindex_var = tk.StringVar(value="1")
cb_databaseindex_var = tk.StringVar(value="0")
e_imgout_var = tk.StringVar(value="image_save/")

create_label_entry(center_frame, "Root Folder:", e_rootfolder_var)
create_label_entry(center_frame, "Keywords:", e_key_var)
create_label_entry(center_frame, "Image Output Folder:", e_imgout_var)

options_list = [("Functionality:", cb_index_var, ["0", "1"]), 
                ("I/O Index:", cb_ioindex_var, ["0", "1"]), 
                ("Database Index:", cb_databaseindex_var, ["0", "1"])]

for label, var, options in options_list:
    create_option_menu(center_frame, label, var, options)

ttk.Button(center_frame, text="Run Command", command=run_command).pack(pady=10)

ttk.Button(center_frame, text="Quit", command=quit_application, style='TButton').pack(pady=10)

root.mainloop()