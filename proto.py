from constants import *

from tkinter import *
from tkinter import ttk
from ttkthemes import ThemedTk
from tkinter.filedialog import askopenfilename
from PIL import Image, ImageTk
from cs50 import SQL
from random import shuffle
import threading



LANG_FROM = ENG			# Can be freely changed to any language described in constants.py
LANG_TO = RUS			# Can be freely changed to any language described in constants.py

PAGES = dict()			# List of all existed pages
INFO_CALLBACK = None	# Store callback function for cancel it if needed


def main():

	#Preparing database
	if not os.access(PWD + DB_FILENAME, os.R_OK):
		open(PWD + DB_FILENAME, 'w').close()
	db = SQL("sqlite:///" + PWD + DB_FILENAME)
	if len(db.execute('SELECT name FROM sqlite_master WHERE type="table" AND name=?', LANG_FROM["token"])) != 1:
		# If not exist then create new one
		db.execute('CREATE TABLE ? (id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, word TEXT NOT NULL, translation TEXT DEFAULT "", rating REAL DEFAULT 0.0, seq TEXT DEFAULT "", info TEXT DEFAULT "")', LANG_FROM["token"])

	# Get dictionary data from db
	data = db.execute("SELECT * FROM ? ORDER BY word ASC", LANG_FROM["token"])

	# Main window
	root = ThemedTk(theme="plastik")
	root.resizable(False, False)
	root.geometry("{}x{}+{}+{}".format(WND_W, WND_H, (SCREEN_W - WND_W) // 2, (SCREEN_H - WND_H) // 2))

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

	style.map('content.TButton', foreground=[('active', COLOR_BUTTON_HOVER)])
	style.map('start.TButton', foreground=[('active', COLOR_BUTTON_HOVER)])
	style.map('table.TButton', foreground=[('active', COLOR_BUTTON_HOVER)])
	style.map('page.TButton', foreground=[('active', COLOR_BUTTON_HOVER), ('disabled', COLOR_BUTTON_ACTIVE)])
	style.map('option.TButton', foreground=[('active', COLOR_BUTTON_HOVER), ('disabled', COLOR_BUTTON_ACTIVE)])

	style.map('Treeview', background=[('selected', COLOR_PRIMARY)], foreground=[('selected', COLOR_SECONDARY)])
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
	showPage("exam")

	root.protocol('WM_DELETE_WINDOW', root.destroy)
	root.mainloop()


class ExamPage:
	def __init__(self, root, info_header, f_buttons, f_content, db, data):

		self.root = root
		self.db = db
		self.data = data
		self.info = info_header

		self.page_button = generateButton(f_buttons, "exam")
		self.exam_page = ttk.Frame(f_content)

		# Bind check answer on quiz page to hit Enter key for better usability
		self.root.bind('<KeyPress>', self.onKeyPressed)
    
		self.quiz_seq = list()
		self.quiz_word_id = -1
		self.start_option_selected = 0

		# START PAGE
		self.start_page = ttk.Frame(self.exam_page, padding=10, style='content.TFrame')

		self.start_button = ttk.Button(self.start_page, text="START", takefocus=0, command = self.startQuiz, style='start.TButton')
		self.start_options_frame = ttk.Frame(self.start_page, style='content.TFrame')
		self.start_info = ttk.Label(self.start_page, text="", style='info.TLabel')
		self.start_altcheck_cbox = ttk.Checkbutton(self.start_page, text="Use online cross-translate checking", takefocus=0, style='content.TCheckbutton')
		self.start_altcheck_cbox.state(["!alternate", "selected"])
		
		self.start_button.pack(side="top", pady=(80, 0))
		self.start_info.pack(side="bottom", fill=X)
		self.start_altcheck_cbox.pack(side="bottom", pady=(0, 20))
		self.start_options_frame.pack(side="bottom", fill=X, pady=(10, 30))
		
		# Generate options buttons
		for i, v in enumerate(OPTIONS):
			ttk.Button(self.start_options_frame, text=v["text"], takefocus=0, style='option.TButton', command = lambda i=i: self.switchStartOptions(i)).pack(side="left", padx=10, expand=True)

		# QUIZ PAGE
		self.quiz_page = ttk.Frame(self.exam_page, padding=10, style='content.TFrame')

		self.quizContainer = ttk.Frame(self.quiz_page, style='content.TFrame')
		self.quizFormContainer = ttk.Frame(self.quizContainer, style='content.TFrame')

		self.target_word = ttk.Label(self.quizFormContainer, text="", anchor="c", style='word.TLabel')
		self.guess_name = ttk.Label(self.quizFormContainer, text="Guess: ", anchor="e", style='content.TLabel')
		self.answer_entry = ttk.Entry(self.quizFormContainer, width=26, justify="center", font=(FONT_ENTRY, 18))
		self.quiz_right_answer = ttk.Label(self.quizFormContainer, text="", style='info.TLabel')
		self.quiz_info = ttk.Label(self.quizFormContainer, text="", style='info.TLabel')
		self.stats_frame = ttk.Frame(self.quizFormContainer, style='content.TFrame', padding=(0,0,0,8))
		self.quiz_seq_current = ttk.Label(self.stats_frame, text="", style='content.TLabel')
		self.quiz_seq_count = ttk.Label(self.stats_frame, text="", style='content.TLabel')
		self.rating_name = ttk.Label(self.stats_frame, text="Rating:", anchor="e", style='content.TLabel')
		self.rating_value = ttk.Label(self.stats_frame, text="0.0", anchor="c", style='content.TLabel')

		self.check_button = ttk.Button(self.quiz_page, text="Check", takefocus=0, command=self.onCheck, style='content.TButton')
		self.stop_button = ttk.Button(self.quiz_page, text="Stop", takefocus=0, command=self.stopQuiz, style='content.TButton')

		self.guess_name.grid(row=2, column=0, sticky="nsew", pady=(13, 18), padx=(0, 4))
		self.stats_frame.grid(row=0, column=1, sticky="nsew", pady=(20, 10), padx=10)
		self.target_word.grid(row=1, column=1, sticky="nsew", pady=(0, 10))
		self.answer_entry.grid(row=2, column=1, sticky="nsew", pady=(10, 10))
		self.quiz_info.grid(row=3, column=1, sticky="nsew", pady=(0, 10))
		self.quiz_right_answer.grid(row=4, column=1, sticky="nsew", pady=(0, 10))

		self.quizContainer.pack(fill=BOTH, expand=True)
		self.stop_button.pack(side="left")
		self.check_button.pack(side="right")
		self.quiz_seq_current.pack(side="left")
		self.quiz_seq_count.pack(side="left")
		self.rating_value.pack(side="right")
		self.rating_name.pack(side="right", padx=(0, 4))

		# Decoration line
		self.line = Canvas(self.quizFormContainer, height=1, background=COLOR_BLACK, highlightbackground=COLOR_DECOR)
		self.line.grid(row=0, column=1, sticky="sew", pady=(0, 10))


	def startQuiz(self):
		if not self.data:
			setLabelText(self.root, self.start_info, "Dictionary is empty!", INFO_MSG_DELAY)
			return

		# Generate list of suitable words for quiz
		self.quiz_seq.clear()
		# Get limits from options
		r_min = OPTIONS[self.start_option_selected]["min"]
		r_max = OPTIONS[self.start_option_selected]["max"]
		for i, v in enumerate(self.data):
			if (not v["translation"] == '' or self.start_altcheck_cbox.instate(['selected'])) and v["rating"] >= r_min and v["rating"] <= r_max:
				self.quiz_seq.append(i)

		if len(self.quiz_seq) == 0:
			setLabelText(self.root, self.start_info, "No words with selected rating!", INFO_MSG_DELAY)
			return

		shuffle(self.quiz_seq)
		self.quiz_word_id = -1
		self.start_page.pack_forget()
		self.quiz_page.pack(fill=BOTH, expand=True)
		self.stepQuiz()


# BUG: if selected google trans and answer == '' then no adding translation to info message
	def onCheck(self, skip=False):
		self.answer_entry.configure(state=["disabled"])

		# Get 'real' word index in self.data dictionary
		id = self.quiz_seq[self.quiz_word_id]

		addRating = -1.0
		t = ""
		v = ""

		if self.start_altcheck_cbox.instate(['selected']):
			# Alternative answer checking, using googletrans
			ans = self.answer_entry.get().strip().lower()
			if not ans == '':
				# Translate user answer to origin lang and comparing with initial word
				t = TRANSLATOR.translate(ans, src=LANG_TO["tag"], dest=LANG_FROM["tag"]).text.lower()
				if self.target_word["text"] == t:
					addRating = 1.0
				else:
					# Translate initial word to user language and comparing with user answer
					t = TRANSLATOR.translate(self.target_word["text"], src=LANG_FROM["tag"], dest=LANG_TO["tag"]).text.lower()
					if ans == t:
						addRating = 1.0
		else:
			# Regular checking from dictionary data
			tr = self.data[id]["translation"].split(',')
			v = (' (' + ', '.join(tr[1:]) + ')') if len (tr[1:]) > 0 else ''
			if self.answer_entry.get().strip().lower() == tr[0].lower():
				addRating = 1.0
			else:
				for w in tr[1:]:
					if self.answer_entry.get().strip().lower() == w.lower():
						addRating = 1.0
						break

		if addRating == -1.0:
			self.quiz_info.configure(foreground=COLOR_BAD)
			setLabelText(self.root, self.quiz_info, "Rating: -1.0", 0)
			currentSeqStep = "0"
		else:
			self.quiz_info.configure(foreground=COLOR_GOOD)
			setLabelText(self.root, self.quiz_info, "Rating: +" + str(addRating), 0)
			currentSeqStep = str(int(addRating * 2))

		newSeq = self.data[id]["seq"][-19:] + currentSeqStep
		newRating = min(20.0, max(0.0, self.data[id]["rating"] + addRating))
		diffRating = newRating - self.data[id]["rating"]

		self.info.updateDictStatusInfo(rating_changed=diffRating)

		# Update database
		self.db.execute('UPDATE ? SET rating=?, seq=? WHERE id=?', LANG_FROM["token"], newRating, newSeq, self.data[id]["id"])
		# And dictionary in memory as well
		self.data[id]["rating"] = newRating
		self.data[id]["seq"] = newSeq
		# Update UI
		self.rating_value["text"] = self.data[id]['rating']
		self.rating_value.configure(foreground=selectColor(float(self.rating_value["text"])))
		# If word rating out of range selected option - then delete word from quiz sequence
		if (newRating < OPTIONS[self.start_option_selected]["min"] or newRating > OPTIONS[self.start_option_selected]["max"]):
			self.quiz_seq.pop(self.quiz_word_id)
			self.quiz_word_id -= 1
		# Show result info
		if self.start_altcheck_cbox.instate(['selected']):
			setLabelText(self.root, self.quiz_right_answer, "Google: " + t, 0)
		else:
			setLabelText(self.root, self.quiz_right_answer, tr[0] + v, 0)

		self.check_button["text"] = "Next"
		self.check_button.configure(command=self.stepQuiz)

		PAGES['dict'].setDictLoaded(False)


	def stepQuiz(self):
		self.answer_entry.configure(state=["!disabled"])
		self.quiz_info.configure(foreground=COLOR_BLACK)

		if not self.quiz_seq:
			self.stopQuiz()
			setLabelText(self.root, self.start_info, "No more words in selected category!", INFO_MSG_DELAY)
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
		# Adjusting font size according word length
		fSize = min(30, (14 + 80 // len(self.data[id]['word'])))
		self.target_word.configure(font=(FONT_QUIZ_WORD, fSize))
		self.target_word["text"] = self.data[id]['word']
		self.rating_value["text"] = self.data[id]['rating']
		# Back UI to initial state
		self.rating_value.configure(foreground=selectColor(float(self.rating_value["text"])))
		self.answer_entry.delete(0, END)
		self.quiz_info["text"] = ""
		self.check_button["text"] = "Check"
		self.check_button.configure(command=self.onCheck)
		self.quizFormContainer.pack(side="left", padx=(40, 0))
		self.quiz_right_answer["text"] = ""
		self.quiz_info["text"] = ""
		self.answer_entry.focus_set()


	def stopQuiz(self):
		self.restart()


	def onShown(self):
		self.restart()


	def get(self):
		return [self.exam_page, self.page_button]


	def restart(self):
		self.quiz_seq.clear()
		self.quiz_word_id = -1
		self.switchStartOptions(0)
		self.quiz_page.pack_forget()
		self.start_page.pack(fill=BOTH, expand=True)
		self.start_altcheck_cbox.state(["!selected"])


	def switchStartOptions(self, v):
		self.start_option_selected = v
		for i, b in enumerate(self.start_options_frame.pack_slaves()):
			if i == v:				
				b.state(["!active", "disabled"])
			else:
				b.state(["!disabled"])


	def onKeyPressed(self, event):
		if event.keysym == 'Return' and (self.quizFormContainer.winfo_viewable() and self.root.focus_get() == self.answer_entry):
			self.check_button.invoke()


class DictPage:
	def __init__(self, root, info_header, f_buttons, f_content, db, data):

		self.DICT_LOADED = False

		self.root = root
		self.db = db
		self.data = data
		self.info = info_header

		self.page_button = generateButton(f_buttons, "dict")

		self.dict_page = ttk.Frame(f_content)

		# DICT PAGE
		self.dictContainer = ttk.Frame(self.dict_page, padding=10, style='content.TFrame')

		# Create table with scrollbar and little info label
		self.tableContainer = ttk.Frame(self.dictContainer, relief=SUNKEN, borderwidth=1)
		self.tableContainer.pack(fill=BOTH, expand=True)

		columns = ("number", "word", "translation", "variants", "rating", "id")
		self.dict_table = ttk.Treeview(master=self.tableContainer, columns=columns, show="headings", selectmode="browse")
		self.dict_scrollbar = ttk.Scrollbar(master=self.tableContainer, orient=VERTICAL, command=self.dict_table.yview)
		self.dict_table.configure(yscroll=self.dict_scrollbar.set)
		self.dict_hint = ttk.Label(self.tableContainer, text="Double-click on row to edit entry", style='hint.TLabel')

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
		self.dict_table.bind("<Double-1>", self.OnEntryDoubleClick)

		self.add_button = ttk.Button(self.dictContainer, text="Add new word", takefocus=0, command=self.toggleDictionary, style='content.TButton')
# Reload button function need change to full reload dict from DB
		self.reload_button = ttk.Button(self.dictContainer, text="Reload", takefocus=0, command=self.reloadDictionary, style='content.TButton')
		self.reveal_button = ttk.Button(self.dictContainer, text="Show translation", takefocus=0, command=self.toggleTranslation, style='content.TButton')

		self.add_button.pack(side="right", pady=(10, 0), padx=(10, 0))
		self.reload_button.pack(side="left", pady=(10, 0), padx=(0, 10))
		self.reveal_button.pack(side="bottom", pady=(10, 0), fill=X)

		# ADD PAGE
		self.dictContainer.pack(fill=BOTH, expand=True)

		self.addContainer = ttk.Frame(self.dict_page, padding=10, style='content.TFrame')
		self.formContainer = ttk.Frame(self.addContainer, style='content.TFrame', padding=(0,60,0,0))
		self.formContainer.pack(side="top", fill=BOTH, expand=True)

		# FRAME WITH RATING
		self.word_info_frame = ttk.Frame(self.formContainer, height=40, style='content.TFrame')
		self.word_edit_rating_text = ttk.Label(self.word_info_frame, text='Rating:', anchor="c", style='content.TLabel')
		self.word_edit_rating = ttk.Label(self.word_info_frame, text='', anchor="c", style='content.TLabel')

		# Labels for indicate answers sequence
		for i in range(20):
			item = ttk.Label(self.word_info_frame, text='|', width=0 , font=(FONT_SEQUENCE, 14, "bold"), style='seqNull.TLabel')
			item.pack(side="left")

		self.word_edit_rating.pack(side="right")
		self.word_edit_rating_text.pack(side="right", padx=(0, 4))

		# FORM
		self.word_label = ttk.Label(self.formContainer, text="Word:", anchor="e", style='content.TLabel')
		self.translation_label = ttk.Label(self.formContainer, text="Translation:", anchor="e", style='content.TLabel')
		self.additional_label = ttk.Label(self.formContainer, text="Variants:", anchor="e", style='content.TLabel')

		self.word_entry = ttk.Entry(self.formContainer, width=26, font=(FONT_ENTRY, 18), justify="center")
		self.translation_entry = ttk.Entry(self.formContainer, width=26, font=(FONT_ENTRY, 18), justify="center")
		self.additional_entry = ttk.Entry(self.formContainer, width=26, font=(FONT_ENTRY, 18), justify="center")

		self.word_label.grid(row=1, column=0, sticky="nsew", pady=(12, 12), padx=(0, 10))
		self.translation_label.grid(row=2, column=0, sticky="nsew", pady=(12, 12), padx=(0, 10))
		self.additional_label.grid(row=3, column=0, sticky="nsew", pady=(12, 12), padx=(0, 10))

		self.word_entry.grid(row=1, column=1, sticky="nsew", pady=(3, 4))
		self.translation_entry.grid(row=2, column=1, sticky="nsew", pady=(4, 4))
		self.additional_entry.grid(row=3, column=1, sticky="nsew", pady=(4, 3))

		self.rating_cbox = ttk.Checkbutton(self.formContainer, text="Reset rating", takefocus=0, style='content.TCheckbutton')
		self.rating_cbox.state(["!selected", "!alternate"])
		self.rating_cbox.grid(row=4, column=1, pady=(10, 0))

		self.add_info = ttk.Label(self.formContainer, text="", style='info.TLabel')
		self.add_info.grid(row=5, column = 1, pady=(10, 0), sticky="nsew")

		self.back_button = ttk.Button(self.addContainer, text="Back", takefocus=0, command=self.toggleDictionary, style='content.TButton')
		self.back_button.pack(side="left")

		self.delete_word_button = ttk.Button(self.addContainer, text="Delete", takefocus=0, command=lambda: self.deleteWord(), style='content.TButton')
		self.delete_word_button.pack(side="bottom")

		self.save_word_button = ttk.Button(self.addContainer, text="Save", takefocus=0, command=lambda: self.saveWord(), style='content.TButton')
		self.save_word_button.pack(side="right")

		# Google translate button
		self.google_img = ImageTk.PhotoImage(Image.open(GOOGLE_IMAGE).resize((25, 25), Image.LANCZOS))
		self.google_button = ttk.Button(self.formContainer, image=self.google_img, takefocus=0, command=lambda: self.googleTranslate(), style='google.TButton')

		self.google_button.grid(row=1, column=2, sticky="nsew", padx=(6, 0), pady=(3, 4))


	def generateSeqInfo(self, iData):
		seqLabels = self.word_info_frame.pack_slaves()[:20]
		seq = "" if iData == -1 else self.data[iData]["seq"]
		seqSize = len(seq)

		for i, v in enumerate(seqLabels):
			if i < 20 - seqSize:
				style = 'seqNull.TLabel'
			else:
				seqChar = seq[20 - seqSize - i]
				style = 'seqBad.TLabel' if seqChar == '0' else 'seqMid.TLabel' if seqChar == '1' else 'seqGood.TLabel' if seqChar == '2' else 'seqNull.TLabel'
			v.configure(style=style)


	def googleTranslate(self):
		w = self.word_entry.get().strip()
		if w == "":
			setLabelText(self.root, self.add_info, "Nothing to translate!", INFO_MSG_DELAY)
			return

		try:
			t = TRANSLATOR.translate(w, src=LANG_FROM["tag"], dest=LANG_TO["tag"]).text.lower()
		except:
			setLabelText(self.root, self.add_info, "No internet connection!", INFO_MSG_DELAY)
			return

		if t == "" or t == w:
			setLabelText(self.root, self.add_info, "Sorry, can't translate!", INFO_MSG_DELAY)
			return

		self.translation_entry.delete(0, END)
		self.translation_entry.insert(0, t)
		setLabelText(self.root, self.add_info, "Translated!", INFO_MSG_DELAY)


	def deleteWord(self, iData=-1):
		if iData == -1:
			setLabelText(self.root, self.add_info, "Can't delete word!", INFO_MSG_DELAY)
			return

		w = self.data[iData]["word"]

		self.db.execute('DELETE FROM ? WHERE id=?', LANG_FROM["token"], self.data[iData]["id"])
		self.info.updateDictStatusInfo(-self.data[iData]["rating"], -1)

		del self.data[iData]

		self.word_entry.state(["!disabled"])
		self.clearAddForm()
		self.word_entry.state(["disabled"])

		self.rating_cbox.state(["!selected", "disabled"])

		self.delete_word_button.configure(command=lambda: self.deleteWord())
		self.delete_word_button.state(["!active", "disabled"])

		self.save_word_button.state(["disabled"])

		self.generateSeqInfo(-1)
		self.word_edit_rating["text"] = 0.0
		self.word_edit_rating.configure(foreground=selectColor(0.0))

		self.reloadDictionary()
		self.clearAddForm()
		
		setLabelText(self.root, self.add_info, "Word '" + w + "' deleted!", INFO_MSG_DELAY)
		self.root.focus()


	def saveWord(self, iData=-1):
		word_to_add = self.word_entry.get().strip()
		translate = self.translation_entry.get().strip()
		add = self.additional_entry.get().strip()

		if any(not (c.isalpha() or c in " -") for c in word_to_add):
			setLabelText(self.root, self.add_info, "Word: only letters!", INFO_MSG_DELAY)
			return

		if any(not (c.isalpha() or c in " -") for c in translate):
			setLabelText(self.root, self.add_info, "Translation: only letters or '-'!", INFO_MSG_DELAY)
			return

		if any(not (c.isalpha() or c in " -,") for c in add):
			setLabelText(self.root, self.add_info, "Variants: only letters, '-' or ','!", INFO_MSG_DELAY)
			return

		if word_to_add == "":
			setLabelText(self.root, self.add_info, "Nothing to add!", INFO_MSG_DELAY)
			return

		if translate == "" and not add == "":
			setLabelText(self.root, self.add_info, "Main translation required!", INFO_MSG_DELAY)
			return

		# Format user input for translation and variants
		if not add == '':
			add = ',' + ','.join([x.strip() for x in add.split(',')])

		if iData == -1:
			# Add new word
			for i in self.data:
				if i["word"] == word_to_add:
					setLabelText(self.root, self.add_info, "This word already in dictionary!", INFO_MSG_DELAY)
					return

			id = self.db.execute('INSERT INTO ? (word, translation) VALUES(?,?)', LANG_FROM["token"], word_to_add, translate + add)
			self.data.append(self.db.execute('SELECT * FROM ? WHERE id=?', LANG_FROM["token"], id)[0])
			self.data.sort(key=lambda d: d['word'])
			self.info.updateDictStatusInfo(0, 1)
		else:
			# Update existed word
			newTranslation = translate + add
			resetRating = ', rating=0.0, seq=""' if self.rating_cbox.instate(['selected']) else ''
			if self.rating_cbox.instate(['selected']):
				self.info.updateDictStatusInfo(-self.data[iData]["rating"], 0)

			self.db.execute('UPDATE ? SET translation=?' + resetRating + ' WHERE id=?', LANG_FROM["token"], newTranslation, self.data[iData]["id"])
			self.data[iData].update({"translation": newTranslation})

			if self.rating_cbox.instate(['selected']):
				# Refresh data
				self.data[iData].update({"rating": 0.0, "seq": ""})
				# Refresh UI
				self.generateSeqInfo(iData)
				self.word_edit_rating["text"] = self.data[iData]["rating"]
				self.word_edit_rating.configure(foreground=selectColor(float(self.word_edit_rating["text"])))
				self.rating_cbox.state(["!selected"])

		self.reloadDictionary()

		if iData == -1:
			self.clearAddForm()

		operation = ("added" if iData == -1 else "updated")
		setLabelText(self.root, self.add_info, "Word '" + word_to_add + "' " + operation + "!", INFO_MSG_DELAY)


	def clearAddForm(self):
		self.word_entry.delete(0,END)
		self.translation_entry.delete(0,END)
		self.additional_entry.delete(0,END)
		self.word_entry.focus_set()

	
	def reloadDictionary(self):
		self.DICT_LOADED = False
		self.dict_table.pack_forget()
		self.dict_table.delete(*self.dict_table.get_children())
		threading.Thread(target = lambda: self.loadDictionary()).start()
		# self.loadDictionary()
		

	def toggleTranslation(self, forceHide=False):
		needShow = False if forceHide else self.reveal_button["text"] == "Show translation"
		for i, (data, row) in enumerate(zip(self.data, self.dict_table.get_children())):
			t = (data['translation']).split(',') if needShow else ["***", "***"]
			self.dict_table.set(row, "translation", t[0])
			variants = ', '.join(t[1:])
			self.dict_table.set(row, "variants", variants[:17] + "..." if len(variants) >= 20 else variants)
		self.reveal_button["text"] = "Hide translation" if needShow else "Show translation"


	def toggleDictionary(self):
		if self.dictContainer.winfo_viewable():
			self.add_info["text"] = ""
			self.word_entry.state(["!disabled"])
			self.save_word_button.state(["!disabled"])
			self.word_info_frame.grid_forget()
			self.rating_cbox.grid_forget()
			self.save_word_button.configure(text="Add", command=lambda: self.saveWord())
			self.delete_word_button.configure(command=lambda: self.deleteWord())
			self.delete_word_button.pack_forget()
			self.clearAddForm()
			self.toggleTranslation(True)
			self.dictContainer.pack_forget()
			self.formContainer.configure(padding=(0,60,0,0))
			self.addContainer.pack(fill=BOTH, expand=True)
		else:
			self.addContainer.pack_forget()
			self.dictContainer.pack(fill=BOTH, expand=True)
			self.onShown()


	def onShown(self):
		if not self.DICT_LOADED:
			self.reloadDictionary()


	def loadDictionary(self):
		self.dict_hint["text"] = "Loading dictionary..."
		total_words = len(self.data)
		for i, v in enumerate(self.data):
			tag = 'evenrow' if i % 2 else 'oddrow'
			self.dict_table.insert("", END, values=(i + 1, v["word"], "***", "***", v["rating"], v["id"]), tags = (tag,))
			self.dict_hint["text"] = "Loading dictionary: " + f"{(i + 1) / total_words * 100:.1f}" + "%"
		self.dict_hint["text"] = "Dictionary loaded!"
		self.dict_table.pack(side="left", fill=BOTH, expand=1)
		self.DICT_LOADED = True
		self.root.after(3000, lambda: setLabelText(self.root, self.dict_hint, "Double-click on row to edit entry", 0))


	def OnEntryDoubleClick(self, event):
		item = self.dict_table.identify('item', event.x, event.y)
		if item:
			self.editEntry(int(self.dict_table.item(item, "values")[0]) - 1)


	def editEntry(self, i):
		translated = (self.data[i]['translation']).split(',')

		self.toggleDictionary()
		self.formContainer.configure(padding=(0,34,0,0))
		self.save_word_button.configure(text="Update", command=lambda i=i: self.saveWord(i))
		self.delete_word_button.pack(side="left", fill=Y, expand=True)
		self.delete_word_button.configure(command=lambda: self.deleteWord(i))
		self.delete_word_button.state(["!disabled"])

		self.generateSeqInfo(i)
		self.word_info_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=(0, 4))
		self.word_edit_rating["text"] = self.data[i]["rating"]
		self.word_edit_rating.configure(foreground=selectColor(float(self.word_edit_rating["text"])))

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


	def setDictLoaded(self, value):
		self.DICT_LOADED = value


	def restart(self):
		self.addContainer.pack_forget()
		self.dictContainer.pack(fill=BOTH, expand=True)
		self.toggleTranslation(True)
		self.clearAddForm()


class ImportPage:
	def __init__(self, root, info_header, f_buttons, f_content, db, data):
		# Variable for soft stopping import process
		self.STOP = False

		self.root = root
		self.db = db
		self.data = data
		self.info = info_header
		
		self.page_button = generateButton(f_buttons, "import")

		self.import_page = ttk.Frame(f_content, style='content.TFrame')

		# IMPORT PAGE
		self.importContainer = ttk.Frame(self.import_page, padding=10, style='content.TFrame')
		self.importContainer.pack(expand=1)

		self.import_file_label = ttk.Label(self.importContainer, text="File: ", anchor="e", style='content.TLabel')
		self.import_filepath = ttk.Entry(self.importContainer, font=(FONT_ENTRY, 12), justify="center", width=30)
		self.import_browse_button = ttk.Button(self.importContainer, text="Browse", takefocus=0, command=self.browseFile, style='content.TButton')
		self.import_minlen_label = ttk.Label(self.importContainer, text="Word min length: ", anchor="e", style='content.TLabel')
		self.import_minlen = ttk.Entry(self.importContainer, width=5, font=(FONT_ENTRY, 12), justify="center")
		self.import_translate_cbox = ttk.Checkbutton(self.importContainer, text="Autotranslate", takefocus=0, style='content.TCheckbutton')
		self.import_proper_cbox = ttk.Checkbutton(self.importContainer, text="Skip proper names", takefocus=0, style='content.TCheckbutton')
		self.import_start_button = ttk.Button(self.importContainer, text="Start", takefocus=0, command=self.importStart, style='content.TButton')
		self.import_info = ttk.Label(self.importContainer, text="", style='info.TLabel')
		
		self.import_file_label.grid(row=0, column=0, sticky="nsew")
		self.import_filepath.grid(row=0, column=1, sticky="nsew", pady=10, columnspan=2)
		self.import_browse_button.grid(row=0, column=3, sticky="nsew", pady=10, padx=(2, 0))
		self.import_minlen_label.grid(row=1, column=0, sticky="e", columnspan=2, padx=(48, 0))
		self.import_minlen.grid(row=1, column=2, sticky="w", pady=10)
		self.import_translate_cbox.grid(row=2, column=0, sticky="w", pady=10, columnspan=2, padx=(56, 0))
		self.import_proper_cbox.grid(row=3, column=0, sticky="w", pady=10, columnspan=2, padx=(56, 0))
		self.import_start_button.grid(row=3, column=3, sticky="nsew", pady=10)
		self.import_info.grid(row=4, column = 0, pady=(10, 0), sticky="nsew", columnspan=4)

		# Important UI widgets list for enable/disable state while import processing
		self.controls = [self.import_filepath, self.import_browse_button, self.import_minlen,
					     self.import_translate_cbox, 
					     PAGES['exam'].get()[1], PAGES['dict'].get()[1]]


	def browseFile(self):
		filepath = askopenfilename(initialdir=PWD)
		if filepath:
			self.import_filepath.delete(0, END)
			self.import_filepath.insert(0, filepath)


	def importStart(self):
		self.STOP = False
		filepath = self.import_filepath.get()
		if filepath == '':
			setLabelText(self.root, self.import_info, "Please, select file for import data!", INFO_MSG_DELAY)
			return

		if not os.access(filepath, os.R_OK):
			setLabelText(self.root, self.import_info, "Can't open file!", INFO_MSG_DELAY)
			return

		try:
			if int(self.import_minlen.get()) < 1:
				raise Exception()
		except:
			setLabelText(self.root, self.import_info, "Wrong length value!", INFO_MSG_DELAY)
			return

		for i in self.controls:
			i.state(["disabled"])
		self.import_start_button["text"] = "Stop"
		self.import_start_button.configure(command=self.stopping)
		self.import_info["text"] = "Processing..."

		threading.Thread(target = self.importPayload, args = (filepath,)).start()


	def stopping(self):
		self.STOP = True


	def importPayload(self, filepath):
		try:
			# Temporary dict to store new words
			tempdict = list()
			with open(filepath, "r", encoding="UTF-8") as f:
				print('test')
				punctuation = ',.!?@#$%^&*()_+=\\/\'\"{}[]<>:;~`№|'
				count = 0
				for line in f:
					print(len(line))
					# Format string to remove any punctuations except dashes and create list
					words = line.translate(str.maketrans('', '', punctuation)).split()
					print(words)
					for w in words:
						# Interrupt process if stopped by user
						if self.STOP:
							self.import_info["text"] = "Aborted! No any words added."
							self.importStop()
							return
						# Try to add only lowercase words w/o dashes
						if w.islower() and w.isalpha() and len(w) >= int(self.import_minlen.get()):
							if not w in [x['word'] for x in self.data] and not w in tempdict[::2]:
								t = ""
								if self.import_translate_cbox.instate(['selected']):
									try:
										t = TRANSLATOR.translate(w, src=LANG_FROM["tag"], dest=LANG_TO["tag"]).text.lower()
									except:
										self.import_info["text"] = "Online translation error!"
										self.importStop()
										return

									# Word ignores if googletrans returns same word as initial
									if t == w:
										continue

								tempdict.extend([w, t])
								count += 1
								self.import_info["text"] = "Processing... (" + str(count) + ")"

			self.import_info["text"] = "Finished! Added " + str(count) + " new words."
			self.importStop(tempdict)
		except:
			# If can't read file line after line
			setLabelText(self.root, self.import_info, "Wrong file type", INFO_MSG_DELAY)
			self.importStop()
			return


	def importStop(self, newWords=None):
		self.STOP = False

		# If any non-empty list was given then
		# add new words to database and refresh dict in memory
		# Generating single SQL command to better performance.
		# Not really sure, but expecting bugs if try to add toooooo much words at once
		if newWords and len(newWords) > 0 and len(newWords) % 2 == 0:
			cmd = 'INSERT INTO ? (word, translation) VALUES' + ' (?,?),' * (len(newWords) // 2)
			self.db.execute(cmd[:-1], LANG_FROM["token"], *newWords)
			self.data.clear()
			self.data.extend(self.db.execute("SELECT * FROM ? ORDER BY word ASC", LANG_FROM["token"]))

			PAGES['dict'].setDictLoaded(False)

		self.info.updateDictStatusInfo()

		for i in self.controls:
			i.state(["!disabled"])
		self.import_start_button["text"] = "Start"
		self.import_start_button.configure(command=self.importStart)


	def onShown(self):
		self.restart()


	def get(self):
		return [self.import_page, self.page_button]


	def restart(self):
		self.import_filepath.delete(0, END)
		self.import_minlen.delete(0, END)
		self.import_minlen.insert(0, "2")
		self.import_translate_cbox.state(["selected"])
		self.import_translate_cbox.state(["!alternate"])
		self.import_proper_cbox.state(["selected"])
		self.import_proper_cbox.state(["!alternate"])
		self.import_proper_cbox.state(["disabled"])
		self.import_info["text"] = ""


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

		self.setLangIndicator(LANG_FROM, LANG_TO)
		self.updateDictStatusInfo()
		

	def setLangIndicator(self, lang_from, lang_to):
		self.lang_indicator["text"] = lang_from["short"] + "/" + lang_to["short"]


	def updateDictStatusInfo(self, rating_changed=0, words_changed=0):
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
		

def setLabelText(root, label, text="", time=0):
	global INFO_CALLBACK
	if INFO_CALLBACK:
		root.after_cancel(INFO_CALLBACK)
		INFO_CALLBACK = None
	label["text"] = text
	if time:
		INFO_CALLBACK = root.after(time * 1000, lambda: setLabelText(root, label))


def generateButton(root, text):
	b = ttk.Button(root, text=text.upper(), takefocus=0, command=lambda t=text: showPage(t), style='page.TButton')
	b.pack(fill=BOTH, expand=0, pady=(0, 2))
	return b


def showPage(name):
	for i in PAGES:
		if PAGES[i].get()[0].winfo_viewable():
			PAGES[i].get()[0].pack_forget()
			PAGES[i].get()[1].state(["!disabled"])
			PAGES[i].restart()
			break
	PAGES[name].get()[0].pack(fill=BOTH, expand=True)
	PAGES[name].get()[1].state(["disabled", "!active"])
	PAGES[name].onShown()


def selectColor(value):
	if value < 5.0: return COLOR_BAD
	elif value < 10.0: return COLOR_LOW
	elif value < 15.0: return COLOR_MID
	elif value < 18.0: return COLOR_AVG
	elif value == 20.0: return COLOR_TOP
	else: return COLOR_GOOD


if __name__ == '__main__':
	main()
