# MIT License
#
# Copyright 2023 auto_anki
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the “Software”), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import os
from PIL import ImageTk
from user_cli import *
from tkinter import filedialog
from tkinter import *
from tkinter import filedialog, Tk, ttk, Label, Button, StringVar, OptionMenu, messagebox, Text
from docx2pdf import convert
import sys
import threading
import gpt_prompting as gp
from tkinter.ttk import Progressbar
sys.path.append(
    '/Library/Frameworks/Python.framework/Versions/3.11/lib/python3.11/site-packages')

# import filedialog module


def process_(file, progress_callback, finish_callback):
    try:
        update_status("Processing file...")
        lect_name = file.split("/")[-1].split(".")[0]

        if file.split("/")[-1].split(".")[1] == "pdf":
            pass
        elif file.split("/")[-1].split(".")[1] == "docx":
            template = f"soffice --headless --convert-to pdf {file}"
            os.system(template)
            file = file[:-5] + ".pdf"

        raw_data = extract_words(file)
        raw_data = text_to_groupings(raw_data)
        keyword_data = wp.extract_noun_chunks(raw_data)
        keyword_data = wp.merge_slide_with_same_headers(keyword_data)

        keyword_data = wp.duplicate_word_removal(keyword_data)
        search_query = wp.construct_search_query(
            keyword_data)
        if source_choice.get() == "Google":
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                # when testing use searchquery[:10 or less].
                # Still working on better threading to get faster results
                results = executor.map(
                    get_people_also_ask_links, search_query[:3])
        elif source_choice.get() == "GPT":
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                results = executor.map(gp.get_gpt_answers, search_query[:3])

        auto_anki_model = get_model()
        deck = get_deck(deck_name=lect_name)
        total_qapairs = sum(len(result) for result in results)
        processed_qapairs = 0
        for result in results:
            for qapair in result:
                question = qapair["Question"]
                answer = qapair["Answer"]
                qa = add_question(
                    question=f'{question}', answer=f'{answer}', curr_model=auto_anki_model)
                deck.add_note(qa)
                processed_qapairs += 1
                # Calculate dynamic progress
                progress_percentage = 70 + \
                    (processed_qapairs / total_qapairs * 20)
                progress_callback(progress_percentage)

        add_package(deck, lect_name)
        progress_callback(100)

        finish_callback()
        update_status("File processed successfully.")
    except Exception as e:
        messagebox.showerror("Error", str(e))
        finish_callback()
    # import time
    # time.sleep(5)  # Change ::::This simulate long-running process
    # callback()

# Function for opening the
# file explorer window


def update_progress(value):
    progress['value'] = value
    window.update_idletasks()


def on_finish():
    progress['value'] = 0
    messagebox.showinfo(
        "Success", "The Anki deck has been created successfully.")


def browseFiles():
    # file = filedialog.askopenfilename(initialdir="/",title="Select a File",filetypes=(("Text files","*.txt*"),("all files","*.*")))
    file = filedialog.askopenfilename(parent=window, title="Choose a file", filetypes=[
                                      ("Doc file", "*.docx"), ("Pdf file", "*.pdf")])

    # Change label contents

    if file:
        text_box = Text(window, height=10, width=50, padx=15, pady=15)
        text_box.insert(1.0, file)
        text_box.tag_configure("center", justify="center")
        text_box.tag_add("center", 1.0, "end")
        text_box.grid(column=0, row=3)
        threading.Thread(target=process_, args=(
            file, update_progress, on_finish), daemon=True).start()


def update_status(message):
    status_label.config(text=message)
    window.update_idletasks()


# Create the root window
window = Tk()
# window.minsize(width=450, height=450)
window.config(background="#515A5A")

canvas = Canvas(width=440, height=500)

# canvas color
canvas.configure(bg='#515A5A')

canvas.grid(columnspan=2, rowspan=8)
# Set window title
window.title('Auto-Anki')

# Set window size
window.geometry("450x600")

# set logo
logo = ImageTk.PhotoImage(file='code/Auto_Anki_Logo.jpg')
logo_label = Label(image=logo)
logo_label.image = logo
logo_label.grid(column=0, row=0)

instructions = Label(
    window, text="Select a PDF file on your computer", font="Raleway")
instructions.grid(column=0, row=1)

button_explore = Button(window,
                        text="Browse Files",
                        command=browseFiles)

source_choice = StringVar(window)  # Variable to hold the choice
sources = ["Google", "GPT"]  # List of choices
source_choice.set(sources[0])  # Set default value to Google

source_dropdown = OptionMenu(window, source_choice, *sources)
source_dropdown_label = Label(
    window, text="Choose an API source:", font="Raleway")

source_dropdown_label.grid(column=0, row=2)
source_dropdown.grid(column=0, row=3)


style = ttk.Style(window)
# Set the theme to the default theme
style.theme_use('default')
style.configure('TProgressbar', thickness=10)


# Progress bar widget
progress = Progressbar(window, style='TProgressbar', orient="horizontal",
                       length=250, mode="determinate")
progress.grid(column=0, row=6)  # , columnspan=2, pady=20)

# Status
status_label = Label(window, text="Ready", bd=1, relief="sunken", anchor="w")
status_label.grid(column=0, row=7, columnspan=2,
                  sticky="we", padx=(10, 10), pady=(10, 10))


button_exit = Button(window,
                     text="Exit",
                     command=exit)

button_explore.grid(column=0, row=4)
button_exit.grid(column=0, row=5)

# Let the window wait for any events
window.mainloop()
