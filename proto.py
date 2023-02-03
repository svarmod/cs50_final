from constants import *

from tkinter import *
from tkinter import ttk
from ttkthemes import ThemedTk
from tkinter.filedialog import askopenfilename
from PIL import Image, ImageTk
from cs50 import SQL
from random import shuffle
from threading import Thread
from alphabet_detector import AlphabetDetector

import re



PAGES = dict()			# Dictionary of all existed pages
INFO_CALLBACK = None	# Store callback function for cancel it if needed


def main():

	# Preparing database, if database or table not exist then create new one
	db = get_database()

	# Get dictionary data from db
	data = db.execute("SELECT * FROM ? ORDER BY word ASC", TABLE_NAME)

	# Main window
	root = ThemedTk(theme="plastik")
	root.resizable(False, False)
	root.geometry("{}x{}+{}+{}".format(WND_W, WND_H, (SCREEN_W - WND_W) // 2, (SCREEN_H - WND_H) // 2))
	root.title(TITLE)
	root.iconbitmap(ICON_IMAGE)

	# ====== STYLES ======
	style = ttk.Style()
	style.configure('content.TFrame', background = COLOR_SECONDARY)
	style.configure('content.TLabel', background = COLOR_SECONDARY, font=(FONT_MAIN, 12, "bold"))
	style.configure('content.TButton', background = COLOR_SECONDARY, font=(FONT_MAIN, 10, "bold"), padding=0, width=16)
	style.configure('content.TCheckbutton', background = COLOR_SECONDARY, font=(FONT_MAIN, 10, "bold"))
	style.configure('word.TLabel', background = COLOR_SECONDARY, font=(FONT_QUIZ_WORD, 12, "bold"))
	style.configure('info.TLabel', background = COLOR_SECONDARY, font=(FONT_MAIN, 12, "bold"), anchor="c")
	style.configure('hint.TLabel', background = COLOR_DECOR, font=(FONT_MAIN, 8), anchor="c")
	style.configure('seqNull.TLabel', background=COLOR_SECONDARY, foreground=COLOR_GREY)
	style.configure('seqBad.TLabel', background=COLOR_SECONDARY, foreground=COLOR_BAD)
	style.configure('seqMid.TLabel', background=COLOR_SECONDARY, foreground=COLOR_MID)
	style.configure('seqGood.TLabel', background=COLOR_SECONDARY, foreground=COLOR_GOOD)
	style.configure('main.TFrame', background=COLOR_PRIMARY)
	style.configure('main.TLabel', background=COLOR_PRIMARY, foreground=COLOR_WHITE, font=(FONT_MAIN, 11, "bold"))
	style.configure('start.TButton', background=COLOR_SECONDARY, font=(FONT_MAIN, 14, "bold"), padding=(0,10,0,10))
	style.configure('page.TButton', background=COLOR_PRIMARY, font=(FONT_MAIN, 14, "bold"), padding=(0,10,0,10))
	style.configure('option.TButton', background = COLOR_SECONDARY, font=(FONT_MAIN, 10, "bold"))

	style.map('content.TButton', foreground=[('active', COLOR_BUTTON_HOVER), ('disabled', COLOR_GREY)])
	style.map('start.TButton', foreground=[('active', COLOR_BUTTON_HOVER)])
	style.map('page.TButton', foreground=[('active', COLOR_BUTTON_HOVER), ('disabled', COLOR_BUTTON_ACTIVE)])
	style.map('option.TButton', foreground=[('active', COLOR_BUTTON_HOVER), ('disabled', COLOR_BUTTON_ACTIVE)])
	style.map('Treeview', background=[('selected', COLOR_PRIMARY)], foreground=[('selected', COLOR_SECONDARY)])

	style.layout("Treeview", [('Treeview.treearea', {'sticky': 'nswe'})]) # Remove borders

	root.option_add('*TCombobox*Listbox.font', (FONT_ENTRY, 12, "bold"))
	root.option_add('*TCombobox*Listbox.selectBackground', COLOR_PRIMARY)
	root.option_add('*TCombobox*Listbox.selectForeground', COLOR_SECONDARY)
 	# ====================

	# Generate main components
	f_header = ttk.Frame(root, height=60, style='main.TFrame')
	f_buttons = ttk.Frame(root, width=100, padding=(2, 0, 2, 0), style='main.TFrame')
	f_content = ttk.Frame(root, relief=SUNKEN, borderwidth=1)
	f_footer = ttk.Frame(root,height=20, style='main.TFrame')
	
	# Set layout for main components
	f_header.pack(side="top", fill=X)
	f_footer.pack(side="bottom", fill=X)
	f_buttons.pack(side="left", fill=Y)
	f_content.pack(fill=BOTH, expand=True)

	# Create header with basic info
	info_header = Header(f_header, data)

	# Create pages and them to global dictionary
	PAGES.update({"exam": ExamPage(root, info_header, f_buttons, f_content, db, data)})
	PAGES.update({"dict": DictPage(root, info_header, f_buttons, f_content, db, data)})
	PAGES.update({"import": ImportPage(root, info_header, f_buttons, f_content, db, data)})

	# And show exam page as home
	show_page("exam")

	root.protocol('WM_DELETE_WINDOW', root.destroy)
	root.mainloop()


class ExamPage:
	def __init__(self, root, info_header, f_buttons, f_content, db, data):

		self.root = root
		self.db = db
		self.data = data
		self.info = info_header

		self.page_button = generate_button(f_buttons, "exam")
		self.exam_page = ttk.Frame(f_content)

		# Bind check answer on quiz page to hit Enter key for better usability
		self.root.bind('<KeyPress>', self.on_key_pressed)
    
		self.quiz_seq = list()
		self.quiz_word_id = -1
		self.start_option_selected = 0

		# START PAGE
		self.start_page = ttk.Frame(self.exam_page, padding=10, style='content.TFrame')

		self.start_button = ttk.Button(self.start_page, text="START", takefocus=0, command = self.start_quiz, style='start.TButton')
		self.start_options_frame = ttk.Frame(self.start_page, style='content.TFrame')
		self.start_info = ttk.Label(self.start_page, text="", style='info.TLabel')
		self.start_altcheck_cbox = ttk.Checkbutton(self.start_page, text="Use online cross-translate checking", takefocus=0, style='content.TCheckbutton')
		self.start_altcheck_cbox.state(["!alternate", "selected"])
		
		self.start_button.pack(side="top", pady=(80, 0))
		self.start_info.pack(side="bottom", fill=X)
		self.start_altcheck_cbox.pack(side="bottom", pady=(0, 20))
		self.start_options_frame.pack(side="bottom", fill=X, pady=(10, 30))
		
		# Generate options buttons
		if len(OPTIONS) == 0:
			OPTIONS.append({"text": "All", "min": 0.0, "max": 20.0})

		for i, params in enumerate(OPTIONS):
			ttk.Button(self.start_options_frame, text=params["text"], takefocus=0, style='option.TButton', command = lambda i=i: self.switch_start_options(i)).pack(side="left", padx=10, expand=True)

		# QUIZ PAGE
		self.quiz_page = ttk.Frame(self.exam_page, padding=10, style='content.TFrame')

		self.quiz_container = ttk.Frame(self.quiz_page, style='content.TFrame')
		self.quiz_form_container = ttk.Frame(self.quiz_container, style='content.TFrame')

		self.target_word = ttk.Label(self.quiz_form_container, text="", anchor="c", style='word.TLabel')
		self.guess_name = ttk.Label(self.quiz_form_container, text="Guess: ", anchor="e", style='content.TLabel')
		self.answer_entry = ttk.Entry(self.quiz_form_container, width=26, justify="center", font=(FONT_ENTRY, 18))
		self.quiz_right_answer = ttk.Label(self.quiz_form_container, text="", style='info.TLabel')
		self.quiz_info = ttk.Label(self.quiz_form_container, text="", style='info.TLabel')
		self.stats_frame = ttk.Frame(self.quiz_form_container, padding=(0,0,0,8), style='content.TFrame')
		self.quiz_seq_current = ttk.Label(self.stats_frame, text="", style='content.TLabel')
		self.quiz_seq_count = ttk.Label(self.stats_frame, text="", style='content.TLabel')
		self.rating_name = ttk.Label(self.stats_frame, text="Rating:", anchor="e", style='content.TLabel')
		self.rating_value = ttk.Label(self.stats_frame, text="0.0", anchor="c", style='content.TLabel')

		self.check_button = ttk.Button(self.quiz_page, text="Check", takefocus=0, command=self.on_check, style='content.TButton')
		self.stop_button = ttk.Button(self.quiz_page, text="Stop", takefocus=0, command=self.stop_quiz, style='content.TButton')

		# Extra frame to freeze 'self.target_word' height (when font size changing)
		ttk.Frame(self.quiz_form_container, height=64, style='content.TFrame').grid(row=1, column=0)

		self.guess_name.grid(row=2, column=0, sticky="nsew", pady=(13, 18), padx=(0, 4))
		self.stats_frame.grid(row=0, column=1, sticky="nsew", pady=(20, 10), padx=10)
		self.target_word.grid(row=1, column=1, sticky="nsew", pady=(0, 10))
		self.answer_entry.grid(row=2, column=1, sticky="nsew", pady=(10, 10))
		self.quiz_info.grid(row=3, column=1, sticky="nsew", pady=(0, 10))
		self.quiz_right_answer.grid(row=4, column=1, sticky="nsew", pady=(0, 10))

		self.quiz_container.pack(fill=BOTH, expand=True)
		self.stop_button.pack(side="left")
		self.check_button.pack(side="right")
		self.quiz_seq_current.pack(side="left")
		self.quiz_seq_count.pack(side="left")
		self.rating_value.pack(side="right")
		self.rating_name.pack(side="right", padx=(0, 4))

		# Decoration line
		self.line = Canvas(self.quiz_form_container, height=1, background=COLOR_BLACK, highlightbackground=COLOR_DECOR)
		self.line.grid(row=0, column=1, sticky="sew", pady=(0, 10))


	def set_db(self, db):
		self.db = db


	def start_quiz(self):
		if not self.data:
			set_label_text(self.root, self.start_info, "Dictionary is empty!", INFO_MSG_DELAY)
			return

		# Generate list of suitable words for quiz
		self.quiz_seq.clear()
		# Get limits from options
		r_min = OPTIONS[self.start_option_selected]["min"]
		r_max = OPTIONS[self.start_option_selected]["max"]
		for i, entry in enumerate(self.data):
			if (not entry["translation"] == '' or self.start_altcheck_cbox.instate(['selected'])) and entry["rating"] >= r_min and entry["rating"] <= r_max:
				self.quiz_seq.append(i)

		if len(self.quiz_seq) == 0:
			set_label_text(self.root, self.start_info, "No words with selected rating!", INFO_MSG_DELAY)
			return

		shuffle(self.quiz_seq)
		self.quiz_word_id = -1
		self.start_page.pack_forget()
		self.quiz_page.pack(fill=BOTH, expand=True)
		self.step_quiz()


	def on_check(self, skip=False):
		self.answer_entry.configure(state=["disabled"])

		# Get 'real' word index in self.data dictionary
		id = self.quiz_seq[self.quiz_word_id]

		add_rating = -1.0
		translated = ""
		variants = ""
		correct_answer = ""

		user_answer = self.answer_entry.get().strip().lower()

		# Check user answer
		if self.start_altcheck_cbox.instate(['selected']):
			# Alternative answer checking, using googletrans
			# 1: Translate initial word and comparing it with user answer
			translated = TRANSLATOR.translate(self.target_word["text"], src=LANG_FROM["tag"], dest=LANG_TO["tag"]).text.lower()
			if user_answer == translated:
				add_rating = 1.0
				correct_answer = translated
			elif not user_answer == "":
				# 2: Translate user answer to origin lang and comparing with initial word
				correct_answer = translated
				translated = TRANSLATOR.translate(user_answer, src=LANG_TO["tag"], dest=LANG_FROM["tag"]).text.lower()
				if self.target_word["text"] == translated:
					add_rating = 1.0
					correct_answer = user_answer
			else:
				# If user answer is wrong then just set variable for info message
				correct_answer = translated
		else:
			# Regular checking from dictionary data
			translated = self.data[id]["translation"].split(',')
			variants = (' (' + ', '.join(translated[1:]) + ')') if len (translated[1:]) > 0 else ''
			if user_answer == translated[0].lower():
				add_rating = 1.0
			else:
				for word in translated[1:]:
					if user_answer == word.lower():
						add_rating = 1.0
						break
			correct_answer = translated[0] + variants

		# Update UI with rating changes
		if add_rating == -1.0:
			self.quiz_info.configure(foreground=COLOR_BAD)
			set_label_text(self.root, self.quiz_info, "Rating: -1.0", 0)
			current_seq_step = "0"
		else:
			self.quiz_info.configure(foreground=COLOR_GOOD)
			set_label_text(self.root, self.quiz_info, "Rating: +1.0", 0)
			current_seq_step = "2"
			# Initial idea was to add 0.5 rating (char '1' in guess sequence) for variants match.
			# In this case 'current_seq_step' should be equals: str(int(add_rating * 2))

		new_seq = self.data[id]["seq"][-19:] + current_seq_step
		new_rating = min(20.0, max(0.0, self.data[id]["rating"] + add_rating))
		diff_rating = new_rating - self.data[id]["rating"]

		#Update dict status in window header
		self.info.update_dict_status_info(rating_changed=diff_rating)

		# Update database
		self.db.execute('UPDATE ? SET rating=?, seq=? WHERE id=?', TABLE_NAME, new_rating, new_seq, self.data[id]["id"])
		# Update dictionary in memory as well
		self.data[id]["rating"] = new_rating
		self.data[id]["seq"] = new_seq
		# Update UI
		self.rating_value["text"] = self.data[id]['rating']
		self.rating_value.configure(foreground=select_color(float(self.rating_value["text"])))
		# If word rating out of range selected option - then delete word from quiz sequence
		if (new_rating < OPTIONS[self.start_option_selected]["min"] or new_rating > OPTIONS[self.start_option_selected]["max"]):
			self.quiz_seq.pop(self.quiz_word_id)
			self.quiz_word_id -= 1

		# Show result info
		if self.start_altcheck_cbox.instate(['selected']):
			correct_answer = "Google: " + correct_answer
		set_label_text(self.root, self.quiz_right_answer, correct_answer, 0)

		self.check_button["text"] = "Next"
		self.check_button.configure(command=self.step_quiz)

		PAGES['dict'].set_dict_loaded(False)


	def step_quiz(self):
		self.answer_entry.configure(state=["!disabled"])
		self.quiz_info.configure(foreground=COLOR_BLACK)

		if not self.quiz_seq:
			self.stop_quiz()
			set_label_text(self.root, self.start_info, "No more words in selected category!", INFO_MSG_DELAY)
			return
		# Get next word from sequence or shuffle list and start from first element
		self.quiz_word_id += 1
		if self.quiz_word_id >= len(self.quiz_seq):
			shuffle(self.quiz_seq)
			self.quiz_word_id = 0
		# Update UI
		self.quiz_seq_current["text"] = self.quiz_word_id + 1
		self.quiz_seq_count["text"] = '/' + str(len(self.quiz_seq))
		# Get 'real' word index in self.data
		id = self.quiz_seq[self.quiz_word_id]
		# Adjusting font size according word length: longer word => smaller font
		font_size = min(30, (14 + 80 // len(self.data[id]['word'])))
		self.target_word.configure(font=(FONT_QUIZ_WORD, font_size))
		self.target_word["text"] = self.data[id]['word']
		self.rating_value["text"] = self.data[id]['rating']
		# Back UI to initial state
		self.rating_value.configure(foreground=select_color(float(self.rating_value["text"])))
		self.answer_entry.delete(0, END)
		self.quiz_info["text"] = ""
		self.check_button["text"] = "Check"
		self.check_button.configure(command=self.on_check)
		self.quiz_form_container.pack(side="left", padx=(40, 0))
		self.quiz_right_answer["text"] = ""
		self.quiz_info["text"] = ""
		self.answer_entry.focus_set()


	def stop_quiz(self):
		self.restart()


	def on_shown(self):
		self.restart()


	def get(self):
		return [self.exam_page, self.page_button]


	def restart(self):
		self.quiz_seq.clear()
		self.quiz_word_id = -1
		self.switch_start_options(0)
		self.quiz_page.pack_forget()
		self.start_page.pack(fill=BOTH, expand=True)
		self.start_altcheck_cbox.state(["!selected"])


	def switch_start_options(self, value):
		self.start_option_selected = value
		for i, button in enumerate(self.start_options_frame.pack_slaves()):
			if i == value:				
				button.state(["!active", "disabled"])
			else:
				button.state(["!disabled"])


	def on_key_pressed(self, event):
		if event.keysym == 'Return' and (self.quiz_form_container.winfo_viewable() and self.root.focus_get() == self.answer_entry):
			self.check_button.invoke()


class DictPage:
	def __init__(self, root, info_header, f_buttons, f_content, db, data):

		self.DICT_LOADED = False

		self.root = root
		self.db = db
		self.data = data
		self.info = info_header

		self.page_button = generate_button(f_buttons, "dict")

		self.dict_page = ttk.Frame(f_content)

		# DICT PAGE
		self.dict_container = ttk.Frame(self.dict_page, padding=10, style='content.TFrame')

		# Create table with scrollbar and little info label
		self.table_container = ttk.Frame(self.dict_container, relief=SUNKEN, borderwidth=1)
		self.table_container.pack(fill=BOTH, expand=True)

		columns = ("number", "word", "translation", "variants", "rating", "id")
		self.dict_table = ttk.Treeview(master=self.table_container, columns=columns, show="headings", selectmode="browse")
		self.dict_scrollbar = ttk.Scrollbar(master=self.table_container, orient=VERTICAL, command=self.dict_table.yview)
		self.dict_table.configure(yscroll=self.dict_scrollbar.set)
		self.dict_hint = ttk.Label(self.table_container, text="Double-click on row to edit entry", style='hint.TLabel')

		self.dict_hint.pack(side="bottom", fill=X)
		self.dict_table.pack(side="left", fill=BOTH, expand=1)
		self.dict_scrollbar.pack(side="right", fill=Y, pady=(0,0))

		#Setup columns and header
		self.dict_table.column("number", width=42, anchor="e", stretch=0)
		self.dict_table.column("word", width=150, anchor="c", stretch=0)
		self.dict_table.column("translation", width=150, anchor="c", stretch=0)
		self.dict_table.column("variants", width=132, anchor="c", stretch=0)
		self.dict_table.column("rating", width=60, anchor="c", stretch=0)
		self.dict_table.column("id", width=42, anchor="c", stretch=0)
		self.dict_table.heading("number", text="№")
		self.dict_table.heading("word", text="Word")
		self.dict_table.heading("translation", text="Translation")
		self.dict_table.heading("variants", text="Variants")
		self.dict_table.heading("rating", text="Rating")
		self.dict_table.heading("id", text="ID")
		# Show all columns except "id"
		self.dict_table["displaycolumns"]=("number", "word", "translation", "variants", "rating")
		# Striped row table style
		self.dict_table.tag_configure('oddrow', background=COLOR_TABLE_ROW_1)
		self.dict_table.tag_configure('evenrow', background=COLOR_TABLE_ROW_2)
		# Bind entry edit to double-click on row
		self.dict_table.bind("<Double-1>", self.on_entry_double_click)

		self.add_button = ttk.Button(self.dict_container, text="Add new word", takefocus=0, command=self.toggle_dictionary, style='content.TButton')
		self.reload_button = ttk.Button(self.dict_container, text="Reload", takefocus=0, command=lambda: Thread(target = self.reload_database()).start(), style='content.TButton')
		self.reveal_button = ttk.Button(self.dict_container, text="Show translation", takefocus=0, command=self.toggle_translation, style='content.TButton')

		self.add_button.pack(side="right", pady=(10, 0), padx=(10, 0))
		self.reload_button.pack(side="left", pady=(10, 0), padx=(0, 10))
		self.reveal_button.pack(side="bottom", pady=(10, 0), fill=X)

		# ADD PAGE
		self.dict_container.pack(fill=BOTH, expand=True)

		self.add_container = ttk.Frame(self.dict_page, padding=10, style='content.TFrame')
		self.dict_form_container = ttk.Frame(self.add_container, style='content.TFrame', padding=(0,60,0,0))
		self.dict_form_container.pack(side="top", fill=BOTH, expand=True)

		# FRAME WITH RATING
		self.word_info_frame = ttk.Frame(self.dict_form_container, height=40, style='content.TFrame')
		self.word_edit_rating_text = ttk.Label(self.word_info_frame, text='Rating:', anchor="c", style='content.TLabel')
		self.word_edit_rating = ttk.Label(self.word_info_frame, text='', anchor="c", style='content.TLabel')

		# Labels for indicate answers sequence. Labels used cause need different color for each symbol.
		for i in range(20):
			item = ttk.Label(self.word_info_frame, text='|', width=0 , font=(FONT_SEQUENCE, 14, "bold"), style='seqNull.TLabel')
			item.pack(side="left")

		self.word_edit_rating.pack(side="right")
		self.word_edit_rating_text.pack(side="right", padx=(0, 4))

		# FORM
		self.word_label = ttk.Label(self.dict_form_container, text="Word:", anchor="e", style='content.TLabel')
		self.translation_label = ttk.Label(self.dict_form_container, text="Translation:", anchor="e", style='content.TLabel')
		self.additional_label = ttk.Label(self.dict_form_container, text="Variants:", anchor="e", style='content.TLabel')

		self.word_entry = ttk.Entry(self.dict_form_container, width=26, font=(FONT_ENTRY, 18), justify="center")
		self.translation_entry = ttk.Entry(self.dict_form_container, width=26, font=(FONT_ENTRY, 18), justify="center")
		self.additional_entry = ttk.Entry(self.dict_form_container, width=26, font=(FONT_ENTRY, 18), justify="center")

		self.word_label.grid(row=1, column=0, sticky="nsew", pady=(12, 12), padx=(0, 10))
		self.translation_label.grid(row=2, column=0, sticky="nsew", pady=(12, 12), padx=(0, 10))
		self.additional_label.grid(row=3, column=0, sticky="nsew", pady=(12, 12), padx=(0, 10))

		self.word_entry.grid(row=1, column=1, sticky="nsew", pady=(3, 4))
		self.translation_entry.grid(row=2, column=1, sticky="nsew", pady=(4, 4))
		self.additional_entry.grid(row=3, column=1, sticky="nsew", pady=(4, 3))

		self.rating_cbox = ttk.Checkbutton(self.dict_form_container, text="Reset rating", takefocus=0, style='content.TCheckbutton')
		self.rating_cbox.state(["!selected", "!alternate"])
		self.rating_cbox.grid(row=4, column=1, pady=(10, 0))

		self.add_info = ttk.Label(self.dict_form_container, text="", style='info.TLabel')
		self.add_info.grid(row=5, column = 1, pady=(10, 0), sticky="nsew")

		self.back_button = ttk.Button(self.add_container, text="Back", takefocus=0, command=self.toggle_dictionary, style='content.TButton')
		self.back_button.pack(side="left")

		self.delete_button = ttk.Button(self.add_container, text="Delete", takefocus=0, command=self.delete_word, style='content.TButton')
		self.delete_button.pack(side="bottom")

		self.save_button = ttk.Button(self.add_container, text="Save", takefocus=0, command=self.save_word, style='content.TButton')
		self.save_button.pack(side="right")

		# Google translate button
		self.google_img = ImageTk.PhotoImage(Image.open(GOOGLE_IMAGE).resize((25, 25), Image.LANCZOS))
		self.google_button = ttk.Button(self.dict_form_container, image=self.google_img, takefocus=0, command=self.google_translate, style='google.TButton')

		self.google_button.grid(row=1, column=2, sticky="nsew", padx=(6, 0), pady=(3, 4))


	def set_db(self, db):
		self.db = db


	def generate_seq_info(self, i_data):
		seq_labels = self.word_info_frame.pack_slaves()[:20]
		seq = "" if i_data == -1 else self.data[i_data]["seq"]
		seq_size = len(seq)

		for i, label in enumerate(seq_labels):
			if i < 20 - seq_size:
				style = 'seqNull.TLabel'
			else:
				seq_char = seq[abs(20 - seq_size - i)]
				style = 'seqBad.TLabel' if seq_char == '0' else 'seqMid.TLabel' if seq_char == '1' else 'seqGood.TLabel' if seq_char == '2' else 'seqNull.TLabel'
			label.configure(style=style)


	def google_translate(self):
		word = self.word_entry.get().strip()
		if word == "":
			set_label_text(self.root, self.add_info, "Nothing to translate!", INFO_MSG_DELAY)
			return

		try:
			translation = TRANSLATOR.translate(word, src=LANG_FROM["tag"], dest=LANG_TO["tag"]).text.lower()
		except:
			set_label_text(self.root, self.add_info, "No internet connection!", INFO_MSG_DELAY)
			return

		if translation == "" or translation == word:
			set_label_text(self.root, self.add_info, "Sorry, can't translate!", INFO_MSG_DELAY)
			return

		self.translation_entry.delete(0, END)
		self.translation_entry.insert(0, translation)
		set_label_text(self.root, self.add_info, "Translated!", INFO_MSG_DELAY)


	def delete_word(self, i_data=-1):
		if i_data == -1:
			set_label_text(self.root, self.add_info, "Can't delete word!", INFO_MSG_DELAY)
			return

		word = self.data[i_data]["word"]

		self.db.execute('DELETE FROM ? WHERE id=?', TABLE_NAME, self.data[i_data]["id"])
		self.info.update_dict_status_info(-self.data[i_data]["rating"], -1)

		del self.data[i_data]

		self.word_entry.state(["!disabled"])
		self.clear_add_form()
		self.word_entry.state(["disabled"])

		self.rating_cbox.state(["!selected", "disabled"])

		self.delete_button.configure(command=self.delete_word)
		self.delete_button.state(["!active", "disabled"])

		self.save_button.state(["disabled"])

		self.generate_seq_info(-1)
		self.word_edit_rating["text"] = 0.0
		self.word_edit_rating.configure(foreground=select_color(0.0))

		self.reload_dictionary()
		self.clear_add_form()
		
		set_label_text(self.root, self.add_info, "Word '" + word + "' deleted!", INFO_MSG_DELAY)
		self.root.focus()


	def save_word(self, i_data=-1):

		word_to_add = self.word_entry.get().strip()
		translate = self.translation_entry.get().strip()
		variants = self.additional_entry.get().strip()

		if any(not (c.isalpha() or c in " -") for c in word_to_add):
			set_label_text(self.root, self.add_info, "Word: only letters or '-'!", INFO_MSG_DELAY)
			return

		if any(not (c.isalpha() or c in " -") for c in translate):
			set_label_text(self.root, self.add_info, "Translation: only letters or '-'!", INFO_MSG_DELAY)
			return

		if any(not (c.isalpha() or c in " -,") for c in variants):
			set_label_text(self.root, self.add_info, "Variants: only letters, '-' or ','!", INFO_MSG_DELAY)
			return

		if word_to_add == "":
			set_label_text(self.root, self.add_info, "Nothing to add!", INFO_MSG_DELAY)
			return

		if translate == "" and not variants == "":
			set_label_text(self.root, self.add_info, "Use main translation at first!", INFO_MSG_DELAY)
			return

		# Format user input of variants
		if not variants == '':
			variants = ',' + ','.join([variant.strip() for variant in variants.split(',')])

		if i_data == -1:
			# Add new word
			for entry in self.data:
				if entry["word"] == word_to_add:
					set_label_text(self.root, self.add_info, "This word already in dictionary!", INFO_MSG_DELAY)
					return

			id = self.db.execute('INSERT INTO ? (word, translation) VALUES(?,?)', TABLE_NAME, word_to_add, translate + variants)
			self.data.append(self.db.execute('SELECT * FROM ? WHERE id=?', TABLE_NAME, id)[0])
			self.data.sort(key=lambda d: d['word'])
			self.info.update_dict_status_info(0, 1)
		else:
			# Update existed word
			new_translation = translate + variants
			# If selected rating reset option then add it to SQL query
			reset_rating_cmd = ', rating=0.0, seq=""' if self.rating_cbox.instate(['selected']) else ''
			if self.rating_cbox.instate(['selected']):
				self.info.update_dict_status_info(-self.data[i_data]["rating"], 0)

			self.db.execute('UPDATE ? SET translation=?' + reset_rating_cmd + ' WHERE id=?', TABLE_NAME, new_translation, self.data[i_data]["id"])
			self.data[i_data].update({"translation": new_translation})

			# If selected rating reset option
			if self.rating_cbox.instate(['selected']):
				# Update data
				self.data[i_data].update({"rating": 0.0, "seq": ""})
				# Refresh UI
				self.generate_seq_info(i_data)
				self.word_edit_rating["text"] = self.data[i_data]["rating"]
				self.word_edit_rating.configure(foreground=select_color(float(self.word_edit_rating["text"])))
				self.rating_cbox.state(["!selected"])

		self.reload_dictionary()

		if i_data == -1:
			self.clear_add_form()

		operation = ("added" if i_data == -1 else "updated")
		set_label_text(self.root, self.add_info, "Word '" + word_to_add + "' " + operation + "!", INFO_MSG_DELAY)


	def clear_add_form(self):
		self.word_entry.delete(0,END)
		self.translation_entry.delete(0,END)
		self.additional_entry.delete(0,END)
		self.word_entry.focus_set()

	
	def reload_dictionary(self):
		self.DICT_LOADED = False
		self.dict_table.pack_forget()
		self.dict_table.delete(*self.dict_table.get_children())
		Thread(target = self.load_dictionary).start()


	def reload_database(self):
		self.dict_hint["text"] = "Reloading data from database..."

		self.DICT_LOADED = False
		self.dict_table.pack_forget()
		self.dict_table.delete(*self.dict_table.get_children())

		# Reconnect to DB
		db = get_database()
		for key, page in PAGES.items():
			page.set_db(db)

		self.data.clear()
		self.data.extend(self.db.execute("SELECT * FROM ? ORDER BY word ASC", TABLE_NAME))

		PAGES['dict'].set_dict_loaded(False)
		self.load_dictionary()

		self.info.update_dict_status_info()

		self.dict_hint["text"] = "Completed!"
		self.root.after(3000, lambda: self.dict_hint.configure(text="Double-click on row to edit entry"))
		

	def toggle_translation(self, force_hide=False):
		need_show = False if force_hide else self.reveal_button["text"] == "Show translation"
		for i, (data, row) in enumerate(zip(self.data, self.dict_table.get_children())):
			translations = (data['translation']).split(',') if need_show else ["***", "***"]
			self.dict_table.set(row, "translation", translations[0])
			variants = ', '.join(translations[1:])
			self.dict_table.set(row, "variants", variants[:17] + "..." if len(variants) >= 20 else variants)
		self.reveal_button["text"] = "Hide translation" if need_show else "Show translation"


	def toggle_dictionary(self):
		if self.dict_container.winfo_viewable():
			self.add_info["text"] = ""
			self.word_entry.state(["!disabled"])
			self.save_button.state(["!disabled"])
			self.word_info_frame.grid_forget()
			self.rating_cbox.grid_forget()
			self.save_button.configure(text="Add", command=self.save_word)
			self.delete_button.configure(command=self.delete_word)
			self.delete_button.pack_forget()
			self.clear_add_form()
			self.toggle_translation(True)
			self.dict_container.pack_forget()
			self.dict_form_container.configure(padding=(0,60,0,0))
			self.add_container.pack(fill=BOTH, expand=True)
		else:
			self.add_container.pack_forget()
			self.dict_container.pack(fill=BOTH, expand=True)
			self.on_shown()


	def on_shown(self):
		if not self.DICT_LOADED:
			self.reload_dictionary()


	def load_dictionary(self):
		self.dict_hint["text"] = "Loading dictionary..."
		words_total = len(self.data)
		for i, v in enumerate(self.data):
			tag = 'evenrow' if i % 2 else 'oddrow'
			self.dict_table.insert("", END, values=(i + 1, v["word"], "***", "***", v["rating"], v["id"]), tags = (tag,))
			self.dict_hint["text"] = "Loading dictionary: " + f"{(i + 1) / words_total * 100:.1f}" + "%"
		self.dict_hint["text"] = "Dictionary loaded!"
		self.dict_table.pack(side="left", fill=BOTH, expand=1)
		self.DICT_LOADED = True
		self.root.after(3000, lambda: self.dict_hint.configure(text="Double-click on row to edit entry"))


	def on_entry_double_click(self, event):
		item = self.dict_table.identify('item', event.x, event.y)
		if item:
			self.edit_entry(int(self.dict_table.item(item, "values")[0]) - 1)


	def edit_entry(self, i):
		translated = (self.data[i]['translation']).split(',')

		self.toggle_dictionary()
		self.dict_form_container.configure(padding=(0,34,0,0))
		self.save_button.configure(text="Update", command=lambda i=i: self.save_word(i))
		self.delete_button.pack(side="left", fill=Y, expand=True)
		self.delete_button.configure(command=lambda: self.delete_word(i))
		self.delete_button.state(["!disabled"])

		self.generate_seq_info(i)
		self.word_info_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=(0, 4))
		self.word_edit_rating["text"] = self.data[i]["rating"]
		self.word_edit_rating.configure(foreground=select_color(float(self.word_edit_rating["text"])))

		self.rating_cbox.state(["!disabled"])
		self.rating_cbox.state(["!selected"])
		self.rating_cbox.grid(row=4, column=1, pady=(10, 0))

		self.word_entry.insert(0, self.data[i].get("word"))
		self.translation_entry.insert(0, translated[0].strip())
		self.additional_entry.insert(0, ', '.join(translated[1:]))
		self.translation_entry.focus_set()
		self.word_entry.state(["disabled"])


	def get(self):
		return [self.dict_page, self.page_button]


	def set_dict_loaded(self, value):
		self.DICT_LOADED = value


	def restart(self):
		self.add_container.pack_forget()
		self.dict_container.pack(fill=BOTH, expand=True)
		self.toggle_translation(True)
		self.clear_add_form()


class ImportPage:
	def __init__(self, root, info_header, f_buttons, f_content, db, data):
		# Variable for soft stopping import process
		self.STOP = False

		self.root = root
		self.db = db
		self.data = data
		self.info = info_header
		
		self.page_button = generate_button(f_buttons, "import")

		self.import_page = ttk.Frame(f_content, style='content.TFrame')

		# IMPORT PAGE
		self.import_container = ttk.Frame(self.import_page, padding=10, style='content.TFrame')
		self.import_container.pack(expand=1)

		self.import_file_label = ttk.Label(self.import_container, text="File: ", anchor="e", style='content.TLabel')
		self.import_filepath = ttk.Entry(self.import_container, font=(FONT_ENTRY, 12), justify="center", width=30)
		self.import_browse_button = ttk.Button(self.import_container, text="Browse", takefocus=0, command=self.browse_file, style='content.TButton')
		self.import_alphabet_label = ttk.Label(self.import_container, text="Alphabet: ", anchor="e", style='content.TLabel')
		self.import_alphabet_combobox = ttk.Combobox(self.import_container, state="readonly", values=[x for x in ALPHABETS], takefocus=0, width=24, font=(FONT_ENTRY, 12, "bold"), justify="center")
		self.import_minlen_label = ttk.Label(self.import_container, text="Word min length: ", anchor="e", style='content.TLabel')
		self.import_minlen = ttk.Entry(self.import_container, width=8, font=(FONT_ENTRY, 12), justify="center")
		self.import_autotranslate_cbox = ttk.Checkbutton(self.import_container, text=" Autotranslate", takefocus=0, style='content.TCheckbutton')
		self.import_start_button = ttk.Button(self.import_container, text="Start", takefocus=0, command=self.start_import, style='content.TButton')
		self.import_info = ttk.Label(self.import_container, text="", style='info.TLabel')

		self.import_alphabet_combobox.set(self.import_alphabet_combobox["values"][0])
		self.import_alphabet_combobox.bind('<<ComboboxSelected>>', lambda *args: self.import_alphabet_combobox.selection_clear())

		self.import_file_label.grid(row=0, column=0, sticky="nsw", pady=10)
		self.import_filepath.grid(row=0, column=1, sticky="nsew", pady=10, columnspan=2)
		self.import_browse_button.grid(row=0, column=3, sticky="nsew", pady=10, padx=(2, 0))
		self.import_alphabet_label.grid(row=1, column=0, sticky="nsw", columnspan=2, pady=10)
		self.import_alphabet_combobox.grid(row=1, column=1, sticky="nse", columnspan=2, pady=10)
		self.import_minlen_label.grid(row=2, column=0, sticky="nsw", columnspan=2, pady=10)
		self.import_minlen.grid(row=2, column=2, sticky="nsw", pady=10)
		self.import_autotranslate_cbox.grid(row=3, column=0, sticky="nsew", columnspan=2, pady=(10, 20))
		self.import_start_button.grid(row=3, column=3, sticky="nsew", pady=(10, 20))
		self.import_info.grid(row=4, column = 0, sticky="nsew", columnspan=4)

		# Important UI widgets list for enable/disable state while import processing
		self.controls = [self.import_filepath, self.import_browse_button, self.import_minlen,
					     self.import_autotranslate_cbox, self.import_alphabet_combobox,
					     PAGES['exam'].get()[1], PAGES['dict'].get()[1]]


	def set_db(self, db):
		self.db = db


	def browse_file(self):
		filepath = askopenfilename(initialdir=PWD)
		if filepath:
			self.import_filepath.delete(0, END)
			self.import_filepath.insert(0, filepath)


	def start_import(self):
		self.STOP = False
		filepath = self.import_filepath.get()
		if filepath == '':
			set_label_text(self.root, self.import_info, "Please, select file for import data!", INFO_MSG_DELAY)
			return

		if not os.access(filepath, os.R_OK):
			set_label_text(self.root, self.import_info, "Can't open file!", INFO_MSG_DELAY)
			return

		try:
			if int(self.import_minlen.get()) < 1:
				raise Exception()
		except:
			set_label_text(self.root, self.import_info, "Wrong length value!", INFO_MSG_DELAY)
			return

		for element in self.controls:
			element.state(["disabled"])
		self.import_start_button["text"] = "Stop"
		self.import_start_button.configure(command=self.abort_import)
		self.import_info["text"] = "Processing..."

		Thread(target = self.process_import, args = (filepath,)).start()


	def abort_import(self):
		self.STOP = True


	def process_import(self, filepath):
		try:
			# Temporary dict to store new words
			temp_dict = list()
			with open(filepath, "r", encoding="UTF-8") as file:

				detector = AlphabetDetector()
				words_count = 0
				to_replace = ',.!?@#$%^&*()_+=\\/\'\"{}[]<>:;~`№|1234567890'
				regex = re.compile('[%s]' % re.escape(to_replace))

				for line in file:
					words = regex.sub(' ', line).split()
					for word in words:
						if self.STOP:
							self.import_info["text"] = "Aborted! No any words added."
							self.stop_import()
							return

						basic_conditions = len(word) >= int(self.import_minlen.get())
						alpha_conditions = True
						extra_conditions = True

						abc_name = self.import_alphabet_combobox.get()

						if not ALPHABETS[abc_name]['id'] == "ALL":
							alpha_conditions = detector.only_alphabet_chars(word, ALPHABETS[abc_name]['id'])
							if ALPHABETS[abc_name]['use_extra']:
								extra_alpha_check = word.encode().isalpha() if ALPHABETS[abc_name]['use_encode'] else word.isalpha()
								extra_conditions = word.islower() and extra_alpha_check

						if basic_conditions and alpha_conditions and extra_conditions:
							# In temp_dict stores words and translation one-by-one so need checks 1,3,5...etc. elements
							if not word in [entry['word'] for entry in self.data] and not word in temp_dict[::2]:
								translation = ""
								if self.import_autotranslate_cbox.instate(['selected']):
									try:
										translation = TRANSLATOR.translate(word, src=LANG_FROM["tag"], dest=LANG_TO["tag"]).text.lower()
									except:
										self.import_info["text"] = "Online translation error!"
										self.stop_import()
										return

									# Word ignores if googletrans returns same word as initial
									if translation == word:
										continue

								temp_dict.extend([word, translation])
								words_count += 1
								self.import_info["text"] = "Processing... (" + str(words_count) + ")"

			self.import_info["text"] = "Finished! Added " + str(words_count) + " new words."
			self.stop_import(temp_dict)

		except:
			# If can't read file line after line
			set_label_text(self.root, self.import_info, "Wrong file type", INFO_MSG_DELAY)
			self.stop_import()
			return


	def stop_import(self, new_words=None):
		self.STOP = False

		# If any non-empty list was given then
		# add new words to database and refresh dict in memory
		# Generating single SQL command for better performance.
		# Not really sure, but expecting problems if try to add toooooo much words at once
		if new_words and len(new_words) > 0 and len(new_words) % 2 == 0:
			cmd = 'INSERT INTO ? (word, translation) VALUES' + ' (?,?),' * (len(new_words) // 2)
			self.db.execute(cmd[:-1], TABLE_NAME, *new_words)
			self.data.clear()
			self.data.extend(self.db.execute("SELECT * FROM ? ORDER BY word ASC", TABLE_NAME))

			PAGES['dict'].set_dict_loaded(False)

		self.info.update_dict_status_info()

		for element in self.controls:
			element.state(["!disabled"])
		self.import_start_button["text"] = "Start"
		self.import_start_button.configure(command=self.start_import)


	def on_shown(self):
		self.restart()


	def get(self):
		return [self.import_page, self.page_button]


	def restart(self):
		self.import_filepath.delete(0, END)
		self.import_minlen.delete(0, END)
		self.import_minlen.insert(0, "2")
		self.import_autotranslate_cbox.state(["!selected", "!alternate"])
		self.import_info["text"] = ""
		self.import_alphabet_combobox.set(self.import_alphabet_combobox["values"][0])


class Header:
	def __init__(self, f_header, data):

		self.data = data
		self.total_rating = 0.0
		self.total_words = 0

		self.dict_info = ttk.Frame(f_header, style='main.TFrame', padding=10)
		self.dict_info.pack(fill=BOTH, expand=1)

		self.lang_indicator = ttk.Label(self.dict_info, text="", style='main.TLabel')
		self.dict_progress_text = ttk.Label(self.dict_info, text="Progress: ", anchor="e", style='main.TLabel')
		self.dict_progress_value = ttk.Label(self.dict_info, text="", anchor="w", style='main.TLabel')
		self.dict_total_text = ttk.Label(self.dict_info, text="Words: ", anchor="e", style='main.TLabel')
		self.dict_total_count = ttk.Label(self.dict_info, text="", anchor="w", style='main.TLabel')
		
		self.lang_indicator.pack(side="left", fill=X, expand=1, padx=(180, 0))
		self.dict_progress_text.pack(side="left", fill=X, expand=1)
		self.dict_progress_value.pack(side="left", fill=X, expand=1)
		self.dict_total_text.pack(side="left", fill=X, expand=1)
		self.dict_total_count.pack(side="left", fill=X, expand=1)

		self.update_lang_indicator(LANG_FROM, LANG_TO)
		self.update_dict_status_info()
		

	def update_lang_indicator(self, lang_from, lang_to):
		self.lang_indicator["text"] = lang_from["short"] + "/" + lang_to["short"]


	def update_dict_status_info(self, rating_changed=0, words_changed=0):
		if rating_changed or words_changed:
			# Update on changed value
			self.total_rating += rating_changed
			self.total_words += words_changed
		else:
			# If no parameters given then force full update
			self.total_rating = 0.0
			self.total_words = 0
			for i in self.data:
				self.total_rating += i["rating"]
				self.total_words += 1

		self.dict_total_count["text"] = self.total_words
		calculated_rating = self.total_rating * 5 / max(self.total_words, 1)
		self.dict_progress_value["text"] = f'{calculated_rating:.2f}%'
		

def set_label_text(root, label, text="", time=0):
	global INFO_CALLBACK
	if INFO_CALLBACK:
		root.after_cancel(INFO_CALLBACK)
		INFO_CALLBACK = None
	label["text"] = text
	if time:
		INFO_CALLBACK = root.after(time * 1000, lambda: set_label_text(root, label))


def generate_button(root, text):
	button = ttk.Button(root, text=text.upper(), takefocus=0, command=lambda text=text: show_page(text), style='page.TButton')
	button.pack(fill=BOTH, expand=0, pady=(0, 2))
	return button


def show_page(name):
	for page in PAGES:
		if PAGES[page].get()[0].winfo_viewable():
			PAGES[page].get()[0].pack_forget()
			PAGES[page].get()[1].state(["!disabled"])
			PAGES[page].restart()
			break
	PAGES[name].get()[0].pack(fill=BOTH, expand=True)
	PAGES[name].get()[1].state(["disabled", "!active"])
	PAGES[name].on_shown()


def select_color(value):
	if value < 5.0: return COLOR_BAD
	elif value < 10.0: return COLOR_LOW
	elif value < 15.0: return COLOR_MID
	elif value < 18.0: return COLOR_AVG
	elif value == 20.0: return COLOR_TOP
	else: return COLOR_GOOD


def get_database():
	if not os.access(PWD + DB_FILENAME, os.R_OK):
		open(PWD + DB_FILENAME, 'w').close()
	db = SQL("sqlite:///" + PWD + DB_FILENAME)
	if len(db.execute('SELECT name FROM sqlite_master WHERE type="table" AND name=?', TABLE_NAME)) != 1:
		# If not exist then create new one
		db.execute('CREATE TABLE ? (id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, word TEXT NOT NULL, translation TEXT DEFAULT "", rating REAL DEFAULT 0.0, seq TEXT DEFAULT "", info TEXT DEFAULT "")', TABLE_NAME)
	return db


if __name__ == '__main__':
	main()
