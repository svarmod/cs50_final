from constants import *

from tkinter import *
from tkinter import ttk
from ttkthemes import ThemedTk
from tkinter.filedialog import askopenfilename

from PIL import Image, ImageTk
from cs50 import SQL
from random import shuffle

import copy
import threading





PAGES = dict()
# DATA = list()
INFO_CALLBACK = None

LANG_FROM = ENG
LANG_TO = RUS

OPTIONS = [{"text": "< 10", "min": 0.0, "max": 10.0},
           {"text": "5 - 15", "min": 5.0, "max": 15.0},
           {"text": "< 20", "min": 0.0, "max": 19.9},
           {"text": "All", "min": 0.0, "max": 20.9}]


def main():

	#Preparing database
	if not os.access(PWD + DB_FILENAME, os.R_OK):
		open(PWD + DB_FILENAME, 'w').close()
	db = SQL("sqlite:///" + PWD + DB_FILENAME)
	if len(db.execute('SELECT name FROM sqlite_master WHERE type="table" AND name=?', LANG_FROM["token"])) != 1:
		# Create dictionary table
		db.execute('CREATE TABLE ? (id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, word TEXT NOT NULL, translation TEXT DEFAULT "", rating REAL DEFAULT 0.0, seq TEXT DEFAULT "", info TEXT DEFAULT "")', LANG_FROM["token"])
		# === Insert test data ==================
		insertTestData(db, LANG_FROM)
		# =======================================

	# Get dict from db
	data = db.execute("SELECT * FROM ? ORDER BY word ASC", LANG_FROM["token"])

	# Root
	root = ThemedTk(theme="plastik")	# For stylish windows
	# root = Tk()						# For regular windows
	root.resizable(False, False)
	root.geometry("{}x{}+{}+{}".format(WND_W, WND_H, (SCREEN_W - WND_W) // 2, (SCREEN_H - WND_H) // 2))
	root.configure(background="black") # DEBUG

	# STYLES
	style = ttk.Style()
	# style.configure('TFrame', background = '#ab23ff') # DEBUG
	style.configure('head.TFrame', background = COLOR_BG_ALT)
	style.configure('foot.TFrame', background = COLOR_BG_ALT)
	style.configure('page.TButton', background = '#ab23ff', font=(FONT_MAIN, 14, "bold"))
	style.configure('common.TButton', font=(FONT_MAIN, 10, "bold"), width=16)
	style.configure('g.TButton', font=("Helvetica", 18, "bold"))
	style.configure('dict.TButton', font=("Helvetica", 8, "bold"), width=3)
	style.configure('alt_dict.TButton', font=("Helvetica", 8, "bold"), width=3)
	style.configure('common.TCheckbutton', font=(FONT_MAIN, 10, "bold"))
	style.configure('common.TRadiobutton', font=(FONT_MAIN, 10, "bold"))

	style.configure('option.TButton', font=(FONT_MAIN, 10, "bold"))
	style.map('option.TButton', foreground=[('disabled', '#ab23ff')])

	# style.map("TEntry",
 #                        foreground=[('disabled', 'yellow'),
 #                                    ('active', 'blue')],
 #                        background=[('disabled', 'magenta'),
 #                                    ('active', 'green')],
 #                        highlightcolor=[('focus', 'green'),
 #                                        ('!focus', 'red')],
 #                        fieldbackground=[('disabled', 'green'),
 #                                        ('!disabled', 'red')])



	# Generate main components
	f_header = ttk.Frame(root, height=60, relief=SOLID, borderwidth=1, style="head.TFrame")
	f_buttons = ttk.Frame(root, width=100, relief=SOLID, padding=10)
	f_content = ttk.Frame(root, relief=SOLID)
	f_footer = ttk.Frame(root,height=40, relief=SOLID, style="foot.TFrame")
	
	# Set layout for main components
	f_header.pack(side="top", fill=X)
	f_footer.pack(side="bottom", fill=X)
	f_buttons.pack(side="left", anchor="nw")
	f_content.pack(fill=BOTH, expand=True)

	# Dictionary info setup
	info_header = Header(root, data, f_header)
	info_header.setLangIndicator(LANG_FROM, LANG_TO)
	info_header.updateDictStatusInfo()
	
	# Create pages and them to global dictionary
	PAGES.update({"exam": ExamPage(root, info_header, f_buttons, f_content, f_footer, db, data)})
	PAGES.update({"dict": DictPage(root, info_header, f_buttons, f_content, f_footer, db, data)})
	PAGES.update({"import": ImportPage(root, info_header, f_buttons, f_content, f_footer, db, data)})
	# And show first page after
	showPage("exam")

	root.protocol('WM_DELETE_WINDOW', root.destroy)
	root.mainloop()


class ExamPage:
	def __init__(self, root, info_header, f_buttons, f_content, f_footer, db, data):

		self.root = root
		self.db = db
		self.data = data
		self.parent = f_content
		self.info = info_header

		self.page_button = generateButton(f_buttons, "exam")

		self.exam_page = ttk.Frame(self.parent, relief=SOLID, borderwidth=1)

		self.root.bind('<KeyPress>', self.onKeyPressed)
    


		# START PAGE
		self.quiz_seq = list()
		self.quiz_word_id = -1
		self.start_option_selected = 0


		self.start_page = ttk.Frame(self.exam_page, padding=10)


		self.start_button = ttk.Button(self.start_page, text="START", takefocus=0, padding=10, style="page.TButton", command = self.startQuiz)
		self.start_options_frame = ttk.Frame(self.start_page, relief=SOLID, borderwidth=1)

		self.start_info = ttk.Label(self.start_page, text="", font=(FONT_MAIN, 14), anchor="c", relief=SOLID, borderwidth=1)

		self.start_altcheck_cbox = ttk.Checkbutton(self.start_page, text="Use back-translate checking", takefocus=0, style="common.TCheckbutton")
		self.start_altcheck_cbox.state(["!alternate", "!selected"])
		

		self.start_button.pack(expand=True)
		self.start_info.pack(side="bottom", fill=X)
		self.start_options_frame.pack(side="bottom", fill=X, pady=(20, 10))
		self.start_altcheck_cbox.pack(side="bottom")
		

		# Generate options buttons
		for i, v in enumerate(OPTIONS):
			ttk.Button(self.start_options_frame, takefocus=0, text=v["text"], style="option.TButton", command = lambda i=i: self.switchStartOptions(i)).pack(side="left", padx=10, expand=True)


		# QUIZ PAGE
		self.quiz_page = ttk.Frame(self.exam_page, padding=10, relief=SOLID, borderwidth=1)

		self.quizContainer = ttk.Frame(self.quiz_page)

		self.quizFormContainer = ttk.Frame(self.quizContainer, relief=SOLID, borderwidth=1)
		# self.quizFormContainer.pack(fill=BOTH, expand=True, pady=(0, 20), anchor="s")
		# self.quizFormContainer.grid_columnconfigure(1, weight=0)


		self.target_word = ttk.Label(self.quizFormContainer, text="", anchor="c", relief=SOLID, borderwidth=1)

		self.guess_name = ttk.Label(self.quizFormContainer, text="Guess:", anchor="e", font=(FONT_MAIN, 12), relief=SOLID, borderwidth=1)

		self.answer_entry = ttk.Entry(self.quizFormContainer, font=(FONT_MAIN, 18), justify="center", width=26)

		self.quiz_right_answer = ttk.Label(self.quizFormContainer, text="", width=30, font=(FONT_MAIN, 10), anchor="c", relief=SOLID, borderwidth=1)

		self.quiz_info = ttk.Label(self.quizFormContainer, text="", width=30, font=(FONT_MAIN, 14), anchor="c", relief=SOLID, borderwidth=1)

		
		self.stats_frame = ttk.Frame(self.quizFormContainer, relief=SOLID, borderwidth=1)

		##############################################
		self.quiz_seq_current = ttk.Label(self.stats_frame, text="1", anchor="e", font=(FONT_MAIN, 12))
		self.quiz_seq_count = ttk.Label(self.stats_frame, text="/256", anchor="c", font=(FONT_MAIN, 12))

		self.rating_name = ttk.Label(self.stats_frame, text="Rating:", width=7, anchor="e", font=(FONT_MAIN, 12))
		self.rating_value = ttk.Label(self.stats_frame, text="0.0", anchor="c", font=(FONT_MAIN, 12, "bold"))

		self.check_button = ttk.Button(self.quiz_page, text="? Check ?", takefocus=0, command=self.onCheck, style="common.TButton")

		self.stop_button = ttk.Button(self.quiz_page, text="! Stop !", takefocus=0, command=self.stopQuiz, style="common.TButton")

		# self.skip_button = ttk.Button(self.quiz_page, text="Skip", takefocus=0, command=lambda: self.onCheck(True), style="common.TButton")

		# self.guess_name.pack(side="left", anchor="w", pady=(30, 0), padx=(30, 0))
		# self.stats_frame.pack(side="top", anchor="n", pady=(20, 0), fill=X, padx=(0, 10))
		# self.target_word.pack(side="top", pady=(30, 0), padx=(0, 10))
		# self.check_button.pack(side="bottom", anchor="n", fill=Y, pady=(0, 40), padx=(10, 10))
		# self.answer_entry.pack(side="left", anchor="c", expand=True, padx=(0, 10))

		self.guess_name.grid(row=2, column=0, sticky="nsew", pady=(8, 18), padx=(0, 4))
		self.stats_frame.grid(row=0, column=1, sticky="nsew", pady=(0, 4), padx=20)
		self.target_word.grid(row=1, column=1, sticky="nsew", pady=(0, 10))
		self.answer_entry.grid(row=2, column=1, pady=(0, 10), sticky="nsew")

		self.quiz_info.grid(row=3, column=1, sticky="nsew", pady=(0, 10))

		self.quiz_right_answer.grid(row=4, column=1, sticky="nsew", pady=(0, 10))

		

		
		self.quizContainer.pack(fill=BOTH, expand=True)

		self.stop_button.pack(side="left")
		# self.skip_button.pack(side="left", expand=True)
		self.check_button.pack(side="right")

		self.quiz_seq_current.pack(side="left")
		self.quiz_seq_count.pack(side="left")

		self.rating_value.pack(side="right")
		self.rating_name.pack(side="right", padx=(0, 4))


	def startQuiz(self):
		if len(self.data) == 0:
			setLabelText(self.root, self.start_info, "Dictionary is empty!", INFO_MSG_DELAY)
			return

		self.quiz_seq.clear()

		# USE START OPTIONS FOR GENERATE LIST
		print('Option selected: ' + str(self.start_option_selected))

		# if not self.start_option_selected == 3:
		# 	# r_min = 0.0 if self.start_option_selected == 1 else 5.0
		# 	# r_max = 10.0 if self.start_option_selected == 1 else 15.0
		# 	r_min = OPTIONS[self.start_option_selected]["min"]
		# 	r_max = OPTIONS[self.start_option_selected]["max"]
		# 	for i in range(len(self.data)):
		# 		if not self.data[i]["translation"] == '' and self.data[i]["rating"] >= r_min and self.data[i]["rating"] <= r_max:
		# 			self.quiz_seq.append(i)
		# else:
		# 	self.quiz_seq.extend(list(range(len(self.data))))



		r_min = OPTIONS[self.start_option_selected]["min"]
		r_max = OPTIONS[self.start_option_selected]["max"]
		for i, v in enumerate(self.data):
			if (not v["translation"] == '' or self.start_altcheck_cbox.instate(['selected'])) and v["rating"] >= r_min and v["rating"] <= r_max:
				self.quiz_seq.append(i)

		print('>>>', self.quiz_seq) # DEBUG

		if len(self.quiz_seq) == 0:
			setLabelText(self.root, self.start_info, "No words with selected rating!", INFO_MSG_DELAY)
			return

		shuffle(self.quiz_seq)
		self.quiz_word_id = -1

		self.start_page.pack_forget()
		self.quiz_page.pack(fill=BOTH, expand=True)
		self.stepQuiz()


	def onCheck(self, skip=False):
		# TODO: Check answer, setup and update rating and sequence for word
		self.answer_entry.configure(state=["disabled"])

		id = self.quiz_seq[self.quiz_word_id]

		addRating = -1.0

		if self.start_altcheck_cbox.instate(['selected']):
			ans = self.answer_entry.get().strip().lower()
			if not ans == '':
				t = TRANSLATOR.translate(ans, src=LANG_TO["tag"], dest=LANG_FROM["tag"]).text.lower()
				if self.target_word["text"] == t:
					addRating = 1.0
		else:
			t = self.data[id]["translation"].split(',')
			v = (' (' + ', '.join(t[1:]) + ')') if len (t[1:]) > 0 else ''

			if self.answer_entry.get().strip().lower() == t[0].lower():
				addRating = 1.0
			else:
				for w in t[1:]:
					if self.answer_entry.get().strip().lower() == w.lower():
						addRating = 0.5
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

		print(newRating, newSeq)

		self.data[id]["rating"] = newRating
		self.data[id]["seq"] = newSeq

		self.rating_value["text"] = self.data[id]['rating']
		self.rating_value.configure(foreground=selectColor(float(self.rating_value["text"])))

		# if (self.start_option_selected == 1 and newRating > 10.0) or (self.start_option_selected == 2 and (newRating < 5.0 or newRating > 15.0)):
		if (newRating < OPTIONS[self.start_option_selected]["min"] or newRating > OPTIONS[self.start_option_selected]["max"]):
			self.quiz_seq.pop(self.quiz_word_id)
			self.quiz_word_id -= 1

		if self.start_altcheck_cbox.instate(['selected']):
			setLabelText(self.root, self.quiz_right_answer, "Google: " + t, 0)
		else:
			setLabelText(self.root, self.quiz_right_answer, t[0] + v, 0)

		# SHOW RESULT PAGE
		# self.skip_button.pack_forget()
		self.check_button["text"] = "Next ->"
		self.check_button.configure(command=self.stepQuiz)
		# self.quizFormContainer.pack_forget()
		# self.quizResultContainer.pack(fill=BOTH, expand=True, pady=(0, 20), anchor="s")
		# self.result_answer.grid(row=3, column=1, sticky="nsew", pady=(0, 10))


		

	# TODO
	def stepQuiz(self):
		self.answer_entry.configure(state=["!disabled"])
		self.quiz_info.configure(foreground='black')

		if len(self.quiz_seq) <= 0:
			self.stopQuiz()
			setLabelText(self.root, self.start_info, "No more words in selected category!", INFO_MSG_DELAY)
			return

		self.quiz_word_id += 1
		if self.quiz_word_id >= len(self.quiz_seq):
			shuffle(self.quiz_seq)
			self.quiz_word_id = 0

		# TODO: IF QUIZ_SEQ ENDS THEN DO SOMETHING!

		self.quiz_seq_current["text"] = self.quiz_word_id + 1
		self.quiz_seq_count["text"] = '/' + str(len(self.quiz_seq))


		id = self.quiz_seq[self.quiz_word_id]

		fSize = min(30, (14 + 80 // len(self.data[id]['word'])))
		self.target_word.configure(font=(FONT_MAIN, fSize))
		self.target_word["text"] = self.data[id]['word']
		self.rating_value["text"] = self.data[id]['rating']

		self.rating_value.configure(foreground=selectColor(float(self.rating_value["text"])))

		self.answer_entry.delete(0, END)
		self.quiz_info["text"] = ""
		# self.skip_button.pack(side="left", expand=True)
		self.check_button["text"] = "? Check ?"
		self.check_button.configure(command=self.onCheck)
		self.quizFormContainer.pack(side="left", padx=(40, 0))

		# SHOW RESULT
		self.quiz_right_answer["text"] = ""
		self.quiz_info["text"] = ""

		self.answer_entry.focus_set()


	def stopQuiz(self):
		# Maybe show some statistics...
		self.restart()


	def onShown(self):
		self.restart()
		# self.startQuiz()


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
				b.state(["disabled"])
			else:
				b.state(["!disabled"])


	def onKeyPressed(self, event):
		if event.keysym == 'Return' and (self.quizFormContainer.winfo_viewable() and self.root.focus_get() == self.answer_entry):
			self.check_button.invoke()
			print("Check/Next button invoked!")




















class DictPage:
	def __init__(self, root, info_header, f_buttons, f_content, f_footer, db, data):

		self.DICT_LOADED = False

		self.root = root
		self.db = db
		self.data = data
		self.parent = f_content
		self.info = info_header

		self.page_button = generateButton(f_buttons, "dict")

		self.dict_page = ttk.Frame(self.parent, relief=SOLID, borderwidth=1)

		# DICT PAGE
		self.dictContainer = ttk.Frame(self.dict_page, padding=10)
		self.scrollContainer = ttk.Frame(self.dictContainer, relief=SUNKEN, borderwidth=1)
		self.scrollCanvas = Canvas(self.scrollContainer, width=514, height=80, bg=COLOR_BG)
		self.scrollBar = ttk.Scrollbar(self.scrollContainer, orient="vertical", command=self.scrollCanvas.yview)
		self.scrollFrame = ttk.Frame(self.scrollCanvas)
		self.scrollFrame.bind(
			"<Configure>",
			lambda e: self.scrollCanvas.configure(scrollregion=self.scrollCanvas.bbox("all"))
		)
		self.scrollCanvas.create_window((0, 0), window=self.scrollFrame, anchor="nw")
		self.scrollCanvas.configure(yscrollcommand=self.scrollBar.set)

		# self.dict_content = ttk.Label(self.scrollFrame, text="Loading...", wraplength=460, background=self.COLOR_BG)
		self.add_button = ttk.Button(self.dictContainer, text="Add new word", takefocus=0, command=self.toggleDictionary, style="common.TButton")
		self.reload_button = ttk.Button(self.dictContainer, text="Reload", takefocus=0, command=self.reloadDictionary, style="common.TButton")


		self.reveal_button = ttk.Button(self.dictContainer, text="Show translation", width=24, takefocus=0, command=self.toggleTranslation, style="common.TButton")

		# self.dict_header = ttk.Frame(self.scrollFrame)
		self.dict_header = ttk.Frame(self.scrollContainer)
		self.dict_content = ttk.Frame(self.scrollFrame)

		self.dict_header.pack(anchor="w", pady=(0, 2))
		self.dict_content.pack(fill=BOTH, expand=True, anchor="c")

		# Dictionary header
		ttk.Label(self.dict_header, text="№", width=4, anchor="e", background=COLOR_BG, font=("Helvetica", 10, "bold"), justify=RIGHT).grid(row=0, column=0, padx=(0, 0), sticky="nsew")

		ttk.Label(self.dict_header, text="Word", width=20, anchor="c", background=COLOR_BG, font=("Helvetica", 10, "bold"), justify=RIGHT).grid(row=0, column=1, padx=(0, 0), sticky="nsew")

		ttk.Label(self.dict_header, text="Translation", width=15, anchor="e", background=COLOR_BG, font=("Helvetica", 10, "bold"), justify=RIGHT).grid(row=0, column=2, padx=(0, 0), sticky="nsew")

		ttk.Label(self.dict_header, text="Variants", width=18, anchor="e", background=COLOR_BG, wraplength=142, font=("Helvetica", 10, "bold"), justify=RIGHT).grid(row=0, column=3, padx=(0, 0), sticky="nsew")

		ttk.Label(self.dict_header, text="Rating  ", width=18, anchor="c", background=COLOR_BG, font=("Helvetica", 10, "bold"), justify=RIGHT).grid(row=0, column=4, padx=(0, 8), sticky="nsew")

		self.scrollContainer.pack(fill=BOTH, expand=True)
		self.scrollCanvas.pack(side="left", fill=BOTH, expand=True)
		self.scrollBar.pack(side="right", fill="y", expand=True)
		self.add_button.pack(side="right", pady=(10, 0), padx=(10, 0))
		self.reload_button.pack(side="left", pady=(10, 0), padx=(0, 10))
		self.reveal_button.pack(side="bottom", pady=(10, 0), fill=X)

		# CONTENT
		self.dictContainer.pack(fill=BOTH, expand=True)

		# ADD PAGE
		self.addContainer = ttk.Frame(self.dict_page, padding=10) # relief=SOLID, borderwidth=1

		self.formContainer = ttk.Frame(self.addContainer) # relief=SOLID, borderwidth=1
		self.formContainer.pack(fill=X, expand=True, pady=(0, 20), anchor="s")

		# HEADER WITH RATING
		self.word_info_frame = ttk.Frame(self.formContainer, height=40, relief=SOLID, borderwidth=1) # relief=SOLID, borderwidth=1
		
		self.word_edit_rating_text = ttk.Label(self.word_info_frame, text='Rating:', font=(FONT_MAIN, 12), anchor="c")
		self.word_edit_rating = ttk.Label(self.word_info_frame, text='0.0', font=(FONT_MAIN, 12, "bold"), anchor="c")
		self.word_edit_rating.pack(side="right")
		self.word_edit_rating_text.pack(side="right", padx=(0, 4))

		self.seq_info = list()
		

		# FORM
		self.word_label = ttk.Label(self.formContainer, text="Word:", font=(FONT_MAIN, 12), anchor="e")
		self.word_entry = ttk.Entry(self.formContainer, width=23, font=(FONT_MAIN, 18), justify="center")
		self.translation_label = ttk.Label(self.formContainer, text="Translation:", font=(FONT_MAIN, 12), anchor="e")
		self.translation_entry = ttk.Entry(self.formContainer, width=23, font=(FONT_MAIN, 18), justify="center")
		self.additional_label = ttk.Label(self.formContainer, text="Variants:", font=(FONT_MAIN, 12), anchor="e")
		self.additional_entry = ttk.Entry(self.formContainer, width=23, font=(FONT_MAIN, 18), justify="center")

		# Checkbox
		self.rating_cbox = ttk.Checkbutton(self.formContainer, text="Reset rating", takefocus=0, style="common.TCheckbutton")
		self.rating_cbox.state(["!selected"])
		self.rating_cbox.state(["!alternate"])
		self.rating_cbox.grid(row=4, column=0, sticky="nsew")


		self.word_label.grid(row=1, column=0, sticky="nsew", pady=(12, 12), padx=(0, 10))
		self.translation_label.grid(row=2, column=0, sticky="nsew", pady=(12, 12), padx=(0, 10))
		self.additional_label.grid(row=3, column=0, sticky="nsew", pady=(12, 12), padx=(0, 10))


		self.word_entry.grid(row=1, column=1, sticky="nsew", pady=(3, 4))
		self.translation_entry.grid(row=2, column=1, sticky="nsew", pady=(4, 4))
		self.additional_entry.grid(row=3, column=1, sticky="nsew", pady=(4, 3))


		self.add_info = ttk.Label(self.formContainer, text="", font=(FONT_MAIN, 12), anchor="c") # relief=SOLID, borderwidth=1
		self.add_info.grid(row=5, column = 1, pady=(10, 0), sticky="nsew")

		self.back_button = ttk.Button(self.addContainer, text="Back", takefocus=0, command=self.toggleDictionary, style="common.TButton")
		self.back_button.pack(side="left")

		self.delete_word_button = ttk.Button(self.addContainer, text="Delete", takefocus=0, style="common.TButton", command=lambda: self.deleteWord())
		self.delete_word_button.pack(side="bottom")

		self.save_word_button = ttk.Button(self.addContainer, text="Save", takefocus=0, style="common.TButton", command=lambda: self.saveWord())
		self.save_word_button.pack(side="right")

		# Get translate by google button
		image = Image.open(GOOGLE_IMAGE)
		image = image.resize((25, 25), Image.LANCZOS)
		self.gimg = ImageTk.PhotoImage(image)
		self.google_button = ttk.Button(self.formContainer, image=self.gimg, takefocus=0, style="g.TButton", command=lambda: self.googleTranslate())

		self.google_button.grid(row=1, column=2, sticky="nsew", padx=(6, 0), pady=(3, 4))


	def generateSeqInfo(self, iData):
		for i in self.seq_info:
			i.pack_forget()

		self.seq_info.clear()

		seq = "" if iData == -1 else self.data[iData]["seq"]

		for i in range((20 - len(seq))):
			item = ttk.Label(self.word_info_frame, text='|', width=0 , font=("Playbill", 14, "bold"), foreground=COLOR_DEFAULT)
			item.pack(side="left")
			self.seq_info.append(item)

		for i in seq:
			col = COLOR_BAD if i == '0' else COLOR_AVG if i == '1' else COLOR_GOOD if i == '2' else 'black'
			item = ttk.Label(self.word_info_frame, text='|', width=0 , font=("Playbill", 14, "bold"), foreground=col)
			item.pack(side="left")
			self.seq_info.append(item)


	def googleTranslate(self):
		w = self.word_entry.get().strip()
		if w == "":
			setLabelText(self.root, self.add_info, "Nothing to translate!", INFO_MSG_DELAY)
			return

		try:
			# t = TRANSLATOR.translate(w)
			t = TRANSLATOR.translate(w, src=LANG_FROM["tag"], dest=LANG_TO["tag"]).text.lower()
		except:
			setLabelText(self.root, self.add_info, "No internet connection!", INFO_MSG_DELAY)
			return

		if t == "":
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

		self.rating_cbox.state(["!selected"])
		self.rating_cbox.state(["disabled"])

		self.delete_word_button.configure(command=lambda: self.deleteWord())
		self.delete_word_button.state(["disabled"])

		self.save_word_button.state(["disabled"])

		self.generateSeqInfo(-1)
		self.word_edit_rating["text"] = 0.0

		self.reloadDictionary()
		self.clearAddForm()
		
		setLabelText(self.root, self.add_info, "Word '" + w + "' deleted!", INFO_MSG_DELAY)
		self.root.focus()


	def saveWord(self, iData=-1):
		# check = db.execute('SELECT * FROM ? WHERE word=?', LANG_FROM["token"], w.get().strip())
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

		# FORMAT USER INPUT FOR TRANSLATION AND VARIANTS
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

		status = ("added" if iData == -1 else "updated")
		setLabelText(self.root, self.add_info, "Word '" + word_to_add + "' " + status + "!", INFO_MSG_DELAY)
		# setLabelText(self.root, self.add_info, "Word '" + word_to_add + "' successfully updated!", 3)



	def clearAddForm(self):
		self.word_entry.delete(0,END)
		self.translation_entry.delete(0,END)
		self.additional_entry.delete(0,END)
		self.word_entry.focus_set()

	
	def reloadDictionary(self):
		slaves = self.dict_content.grid_slaves()
		for i in slaves:
			i.destroy()
		self.loadDictionary()
		self.reveal_button.configure(text = "Show translation")


	def toggleTranslation(self, forceHide=False):
		needShow = self.reveal_button["text"] == "Show translation"
		if forceHide:
			needShow = False
		slaves = self.dict_content.grid_slaves()[::-1]
		cntr = 2
		for i in range(len(self.data)):
			t = (self.data[i]['translation']).split(',') if needShow else ["***", "***"]
			slaves[cntr]["text"] = t[0]
			slaves[cntr + 1]["text"] = '\n'.join(t[1:])
			cntr += 6
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
			self.addContainer.pack(fill=BOTH, expand=True)
		else:
			self.addContainer.pack_forget()
			self.dictContainer.pack(fill=BOTH, expand=True)
			self.onShown()


	def onShown(self):
		if not self.DICT_LOADED:
			self.loadDictionary()
			self.DICT_LOADED = True
		else:
			self.reloadDictionary()


	def loadDictionary(self):
		for i in range(len(self.data)):
			translated = (self.data[i]['translation']).split(',')

			color = COLOR_BG_ALT if i % 2 else COLOR_BG

			ttk.Label(self.dict_content, text=str(i + 1), background=color, anchor="e", width=5).grid(row=i, column=0, 
				padx=(0, 0), sticky="nsew")

			ttk.Label(self.dict_content, text=str(self.data[i]['word']), background=color, anchor="c", width=23, justify=CENTER).grid(row=i, column=1, 
				padx=(0, 0), sticky="nsew")

			ttk.Label(self.dict_content, text="***", background=color, anchor="c", width=23, justify=CENTER).grid(row=i, column=2, 
				padx=(0, 0), sticky="nsew")
			ttk.Label(self.dict_content, text="***", background=color, wraplength=142, anchor="c", width=23, justify=CENTER).grid(row=i, column=3, 
				padx=(0, 0), sticky="nsew")

			ttk.Label(self.dict_content, text=str(self.data[i]['rating']), background=color, anchor="c", width=5).grid(row=i, column=4, 
				padx=(0, 4), sticky="nsew")

			ttk.Button(self.dict_content, text="...", takefocus=0, style="dict.TButton", command=lambda i=i: self.editEntry(i)).grid(row = i, column=5, sticky="nsew")
		print("Dictionary loaded!")
			
			# TABLE english // LANG_FROM["token"]
			# id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, 
			# word TEXT NOT NULL, 
			# translation TEXT DEFAULT "", 
			# rating REAL DEFAULT 0.0, 
			# seq TEXT DEFAULT "", 
			# info TEXT DEFAULT ""


	def editEntry(self, i):
		translated = (self.data[i]['translation']).split(',')

		self.toggleDictionary()
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
		self.rating_cbox.grid(row=4, column=1)

		self.word_entry.insert(0, self.data[i].get("word"))
		self.translation_entry.insert(0, translated[0].strip())
		self.additional_entry.insert(0, ', '.join(translated[1:]))
		# metka
		self.translation_entry.focus_set()
		self.word_entry.state(["disabled"])

		# DEBUG
		print("Edit row: " + str(i + 1) + ", id " + str(self.data[i]["id"]) + ", word : " + self.data[i].get("word"))

	
		if not self.DICT_LOADED:
			self.loadDictionary()
			self.DICT_LOADED = True
		else:
			self.reloadDictionary()


	def get(self):
		return [self.dict_page, self.page_button]


	def restart(self):
		self.addContainer.pack_forget()
		self.dictContainer.pack(fill=BOTH, expand=True)
		self.toggleTranslation(True)
		self.clearAddForm()







class ImportPage:
	def __init__(self, root, info_header, f_buttons, f_content, f_footer, db, data):

		self.root = root
		self.db = db
		self.data = data
		self.parent = f_content
		self.info = info_header

		self.STOP = False

		self.page_button = generateButton(f_buttons, "import")
		self.import_page = ttk.Frame(self.parent, relief=SOLID, borderwidth=1)


		self.importContainer = ttk.Frame(self.import_page, padding=10, relief=SOLID, borderwidth=1)
		self.importContainer.pack(expand=1)


		self.import_file_label = ttk.Label(self.importContainer, text="File: ", font=(FONT_MAIN, 12), anchor="e")
		self.import_file_label.grid(row=0, column=0, sticky="nsew")

		self.import_filepath = ttk.Entry(self.importContainer, font=(FONT_MAIN, 12), justify="center", width=30)
		self.import_filepath.grid(row=0, column=1, sticky="nsew", pady=10, columnspan=2)

		self.import_browse_button = ttk.Button(self.importContainer, text="Browse", takefocus=0, command=self.browserFile, style="common.TButton")
		self.import_browse_button.grid(row=0, column=3, sticky="nsew", pady=10, padx=(2, 0))



		self.import_minlen_label = ttk.Label(self.importContainer, text="Word min length: ", font=(FONT_MAIN, 12), anchor="e")
		self.import_minlen_label.grid(row=1, column=0, sticky="e", columnspan=2)

		self.import_minlen = ttk.Entry(self.importContainer, width=5, font=(FONT_MAIN, 12), justify="center")
		self.import_minlen.grid(row=1, column=2, sticky="w", pady=10)



		self.import_translate_cbox = ttk.Checkbutton(self.importContainer, text="Autotranslate", takefocus=0, style="common.TCheckbutton")
		self.import_translate_cbox.grid(row=2, column=0, sticky="w", pady=10, columnspan=2, padx=(8, 0))


		self.import_proper_cbox = ttk.Checkbutton(self.importContainer, text="Skip proper names", takefocus=0, style="common.TCheckbutton")
		self.import_proper_cbox.grid(row=3, column=0, sticky="w", pady=10, columnspan=2, padx=(8, 0))

		

		self.import_start_button = ttk.Button(self.importContainer, text="Start", takefocus=0, style="common.TButton", command=self.importStart)
		self.import_start_button.grid(row=3, column=3, sticky="nsew", pady=10)

		self.import_info = ttk.Label(self.importContainer, text="", font=(FONT_MAIN, 12), anchor="c", relief=SOLID, borderwidth=1)
		self.import_info.grid(row=4, column = 0, pady=(10, 0), sticky="nsew", columnspan=4)


		self.controls = [self.import_filepath, self.import_browse_button, self.import_minlen,
					     self.import_translate_cbox, 
					     PAGES['exam'].get()[1], PAGES['dict'].get()[1]]



	def browserFile(self):
		filepath = askopenfilename()
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

		threading.Thread(target = self.payload, args = (filepath,)).start()


	def stopping(self):
		self.STOP = True


	def payload(self, filepath):
		try:
			tempdict = list()
			with open(filepath, "r") as f:
				punctuation = ',.!?@#$%^&*()_+=\\/\'\"{}[]<>:;~`№|'
				count = 0
				for line in f:
					line = line.translate(str.maketrans('', '', punctuation))
					words = line.split()
					for w in words:
						if self.STOP:
							self.import_info["text"] = "Aborted! " + str(count) + " new words added."
							self.importStop()
							return
						if w.islower() and w.isalpha() and len(w) >= int(self.import_minlen.get()):
							if not w in [x['word'] for x in self.data] and not w in tempdict[::2]:
								t = ""
								if self.import_translate_cbox.instate(['selected']):
									t = TRANSLATOR.translate(w, src=LANG_FROM["tag"], dest=LANG_TO["tag"]).text.lower()

								if t == w:
									continue

								tempdict.extend([w, t])
								count += 1

			self.import_info["text"] = "Finished! " + str(count) + " new words added."
			self.importStop(tempdict)
		except:
			setLabelText(self.root, self.import_info, "Wrong file type", INFO_MSG_DELAY)
			self.importStop()
			return


	def importStop(self, newWords=None):
		self.STOP = False

		# Add new words to database and refresh dict in memory
		if newWords and len(newWords) > 0 and len(newWords) % 2 == 0:
			print(newWords)
			cmd = 'INSERT INTO ? (word, translation) VALUES' + ' (?,?),' * (len(newWords) // 2)
			self.db.execute(cmd[:-1], LANG_FROM["token"], *newWords)
			self.data.clear()
			self.data.extend(self.db.execute("SELECT * FROM ? ORDER BY word ASC", LANG_FROM["token"]))

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

		# DEBUG
		# self.import_filepath.insert(0, "G:/Dev/_CS50/Final Project/test_text.txt")

		self.import_minlen.delete(0, END)
		self.import_minlen.insert(0, "2")
		self.import_translate_cbox.state(["selected"])
		self.import_translate_cbox.state(["!alternate"])
		self.import_proper_cbox.state(["selected"])
		self.import_proper_cbox.state(["!alternate"])
		self.import_proper_cbox.state(["disabled"])
		self.import_info["text"] = ""
		






			

def setLabelText(root, label, text="", time=0):
	global INFO_CALLBACK
	if INFO_CALLBACK:
		root.after_cancel(INFO_CALLBACK)
		INFO_CALLBACK = None
	label["text"] = text
	if time:
		INFO_CALLBACK = root.after(time * 1000, lambda: setLabelText(root, label))


def generateButton(root, text):
	b = ttk.Button(root, text=text.upper(), padding=0, takefocus=0, command=lambda t=text: showPage(t), style="page.TButton")
	b.pack(fill=BOTH, expand=True, pady=(0, 4))
	return b


def showPage(name):
	for i in PAGES:
		if PAGES[i].get()[0].winfo_viewable():
			PAGES[i].get()[0].pack_forget()
			PAGES[i].get()[1].state(["!disabled"])
			PAGES[i].restart()
			break
	PAGES[name].get()[0].pack(fill=BOTH, expand=True)
	PAGES[name].get()[1].state(["disabled"])
	PAGES[name].onShown()


def selectColor(value):
	if value < 5.0: return '#DC3222'
	elif value < 10.0: return '#DE9420'
	elif value < 15.0: return '#D4C12A'
	elif value < 18.0: return '#8ADB23'
	elif value == 20.0: return '#B143FF'
	else: return '#23B139'


def insertTestData(db, LANG_FROM):
	test_dict = ['"cat", "кошка"', '"dog", "собака"', '"transient", "переходящий,временный"', '"roof", "крыша"',
				 '"ball", "мяч"', '"wall", "стена"', '"fly", "летать,муха"', '"hello", "привет"', '"piano", "пианино"',
				 '"ear", "ухо"', '"jorney", "путешествие,поездка"', '"zoo", "зоопарк"', '"weather", "погода"',
				 '"apple", "яблоко"', '"potato", "картошка"', '"onion", "лук"', '"extermination", "уничтожение"']
	for s in test_dict:
		db.execute('INSERT INTO ? (word, translation) VALUES (' + s + ')', LANG_FROM["token"])


# RESERVED
def combine_funcs(*funcs):
    def combined_func(*args, **kwargs):
        for f in funcs:
            f(*args, **kwargs)
    return combined_func


class Header:
	def __init__(self, root, data, f_header):

		self.total_rating = 0.0
		self.total_words = 0

		self.root = root
		self.data = data
		self.parent = f_header


		self.dict_info = ttk.Frame(self.parent, relief=SOLID, borderwidth=1)
		self.dict_info.pack(side="right", pady=(10, 10), padx=(30, 30))

		self.dictionary_total_text = ttk.Label(self.dict_info, text="Words: ", font=(FONT_MAIN, 10, "bold"))
		self.dictionary_total_count = ttk.Label(self.dict_info, text="999999", font=(FONT_MAIN, 10, "bold"))
		self.dictionary_progress_text = ttk.Label(self.dict_info, text="Progress: ", font=(FONT_MAIN, 10, "bold"))
		self.dictionary_progress_value = ttk.Label(self.dict_info, text="0.0%", font=(FONT_MAIN, 10, "bold"))

		self.lang_indicator = ttk.Label(self.parent, text="", font=(FONT_MAIN, 12, "bold"))

		
		self.dictionary_progress_text.pack(side="left")
		self.dictionary_progress_value.pack(side="left", padx=(0, 30))

		self.dictionary_total_count.pack(side="right")
		self.dictionary_total_text.pack(side="right", padx=(30, 0))

		self.lang_indicator.pack(side="left", padx=(40, 0))


	def setLangIndicator(self, lang_from, lang_to):
		self.lang_indicator["text"] = lang_from["short"] + "/" + lang_to["short"]


	def updateDictStatusInfo(self, rating_changed=0, words_changed=0):
		if rating_changed or words_changed:
			# Update on changedvalues
			self.total_rating += rating_changed
			self.total_words += words_changed
		else:
			# If no parameters given then force full update
			self.total_rating = 0.0
			self.total_words = 0
			for i in self.data:
				self.total_rating += i["rating"]
				self.total_words += 1

		self.dictionary_total_count["text"] = self.total_words
		calculated_rating = self.total_rating * 5 / max(self.total_words, 1)
		self.dictionary_progress_value["text"] = f'{calculated_rating:.2f}%'


if __name__ == '__main__':
	main()



