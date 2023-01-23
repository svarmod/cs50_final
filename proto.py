from constants import *

from tkinter import *
from tkinter import ttk
from ttkthemes import ThemedTk
from PIL import Image, ImageTk
from cs50 import SQL


PAGES = dict()
DATA = list()
INFO_CALLBACK = None

LANG_FROM = ENG
LANG_TO = RUS


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

	# Generate main components
	f_header = ttk.Frame(root, height=60, relief=SOLID, style="head.TFrame")
	f_buttons = ttk.Frame(root, width=100, relief=SOLID, padding=10)
	f_content = ttk.Frame(root, relief=SOLID)
	f_footer = ttk.Frame(root,height=40, relief=SOLID, style="foot.TFrame")
	
	# Set layout for main components
	f_header.pack(side="top", fill=X)
	f_footer.pack(side="bottom", fill=X)
	f_buttons.pack(side="left", anchor="nw")
	f_content.pack(fill=BOTH, expand=True)

	# Create pages and them to global dictionary
	PAGES.update({"exam": ExamPage(root, f_header, f_buttons, f_content, f_footer, db, data)})
	PAGES.update({"dict": DictPage(root, f_header, f_buttons, f_content, f_footer, db, data)})
	# And show first page after
	showPage("dict")

	root.protocol('WM_DELETE_WINDOW', root.destroy)
	root.mainloop()


class ExamPage:
	def __init__(self, root, f_header, f_buttons, f_content, f_footer, db, data):

		self.root = root
		self.db = db
		self.data = data
		self.parent = f_content

		self.page_button = generateButton(f_buttons, "exam")

		self.exam_page = ttk.Frame(self.parent, relief=SOLID, borderwidth=1)

		# START PAGE
		self.start_page = ttk.Frame(self.exam_page, relief=SOLID, borderwidth=1, padding=10)
		self.start_button = ttk.Button(self.start_page, text="START EXAM", takefocus=0, padding=8, style="common.TButton")
		self.start_info = ttk.Label(self.start_page, text="< some info >", font=(FONT_MAIN, 14), anchor="c")

		self.start_button.pack(side="top", expand=True)
		self.start_info.pack(side="bottom", fill=X)

		# EXAM PAGE
		self.quiz_page = ttk.Frame(self.exam_page, relief=SOLID, borderwidth=1, padding=10)

		self.target_word = ttk.Label(self.quiz_page, text="<          |          >", anchor="c")
		fSize = min(30, (14 + 80 // len(self.target_word["text"]))) # 27 letters max reasonable
		self.target_word.configure(font=(FONT_MAIN, fSize))

		self.guess_name = ttk.Label(self.quiz_page, text="Guess:", anchor="e", font=(FONT_MAIN, 12))
		self.answer_entry = ttk.Entry(self.quiz_page, font=(FONT_MAIN, 18), justify="center", width=26)
		self.check_button = ttk.Button(self.quiz_page, text="Check", takefocus=0, command=self.onCheck, style="common.TButton")
		self.stats_frame = ttk.Frame(self.quiz_page)

		self.rating_name = ttk.Label(self.stats_frame, text="Rating:", width=7, anchor="e", font=(FONT_MAIN, 10))
		self.rating_value = ttk.Label(self.stats_frame, text="20.0", width=4, anchor="w", font=(FONT_MAIN, 10, "bold"))

		self.guess_name.pack(side="left", anchor="w", pady=(30, 0), padx=(30, 0))
		self.stats_frame.pack(side="top", anchor="n", pady=(20, 0), fill=X, padx=(0, 10))
		self.target_word.pack(side="top", pady=(30, 0), padx=(0, 10))
		self.check_button.pack(side="bottom", anchor="n", fill=Y, pady=(0, 40), padx=(10, 10))
		self.answer_entry.pack(side="left", anchor="c", expand=True, padx=(0, 10))

		# Rating value colorization
		value = float(self.rating_value["text"])
		color = ''
		if value < 5.0: color = 	'#DC3222'
		elif value < 10.0: color = 	'#DE9420'
		elif value < 15.0: color = 	'#D4C12A'
		elif value < 18.0: color = 	'#8ADB23'
		elif value == 20.0: color = '#B143FF'
		else: color = 				'#23B139'

		self.rating_value.configure(foreground=color)

		self.rating_name.pack(side="left", expand=True, anchor="e")
		self.rating_value.pack(side="right", expand=True, anchor="w", padx=(0,0))

		# PACKING / DEBUG SELECTION
		self.start_page.pack(fill=BOTH, expand=True)
		# self.quiz_page.pack(fill=BOTH, expand=True)


	def onCheck(self):
		self.target_word["text"] = self.data[0]["word"]

	def onShown(self):
		pass


	def get(self):
		return [self.exam_page, self.page_button]


	def restart(self):
		print("exam restarted")


class DictPage:
	def __init__(self, root, f_header, f_buttons, f_content, f_footer, db, data):

		self.DICT_LOADED = False

		self.root = root
		self.db = db
		self.data = data
		self.parent = f_content

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
		ttk.Label(self.dict_header, text="Loading...", background=COLOR_BG)

		ttk.Label(self.dict_header, text="№", width=4, anchor="e", background=COLOR_BG, font=("Helvetica", 10, "bold"), justify=RIGHT).grid(row=0, column=0, padx=(0, 0), sticky="nsew")

		ttk.Label(self.dict_header, text="Word", width=20, anchor="c", background=COLOR_BG, font=("Helvetica", 10, "bold"), justify=RIGHT).grid(row=0, column=1, padx=(0, 0), sticky="nsew")

		ttk.Label(self.dict_header, text="Translation", width=15, anchor="e", background=COLOR_BG, font=("Helvetica", 10, "bold"), justify=RIGHT).grid(row=0, column=2, padx=(0, 0), sticky="nsew")

		ttk.Label(self.dict_header, text="Variants", width=18, anchor="e", background=COLOR_BG, wraplength=142, font=("Helvetica", 10, "bold"), justify=RIGHT).grid(row=0, column=3, padx=(0, 0), sticky="nsew")

		ttk.Label(self.dict_header, text="Rating  ", width=18, anchor="c", background=COLOR_BG, font=("Helvetica", 10, "bold"), justify=RIGHT).grid(row=0, column=4, padx=(0, 8), sticky="nsew")

		self.scrollContainer.pack(fill=BOTH, expand=True)
		self.scrollCanvas.pack(side="left", fill=BOTH, expand=True)
		self.scrollBar.pack(side="right", fill="y", expand=True)
		self.add_button.pack(side="right", pady=(10, 0))
		self.reload_button.pack(side="left", pady=(10, 0))
		self.reveal_button.pack(side="bottom", pady=(10, 0), padx=(10, 0))

		# CONTENT
		self.dictContainer.pack(fill=BOTH, expand=True)

		# ADD PAGE
		self.addContainer = ttk.Frame(self.dict_page, relief=SOLID, borderwidth=1, padding=10)

		self.formContainer = ttk.Frame(self.addContainer, relief=SOLID, borderwidth=1)
		self.formContainer.pack(fill=X, expand=True, pady=(0, 20), anchor="s")

		# HEADER WITH RATING
		self.word_info_frame = ttk.Frame(self.formContainer, relief=SOLID, borderwidth=1, height=40)
		
		self.word_edit_rating = ttk.Label(self.word_info_frame, text='0.0', font=(FONT_MAIN, 14, "bold"), anchor="c")
		self.word_edit_rating.pack(side="right")

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


		self.add_info = ttk.Label(self.formContainer, text="<       |       >", font=(FONT_MAIN, 12), anchor="c", relief=SOLID, borderwidth=1)
		self.add_info.grid(row=5, column = 1, pady=(10, 0), sticky="nsew")

		ttk.Button(self.addContainer, text="Back", takefocus=0, command=self.toggleDictionary, style="common.TButton").pack(side="left")

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
			t = TRANSLATOR.translate(w, src=LANG_FROM["tag"], dest=LANG_TO["tag"]).text
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
		else:
			# Update existed word
			newTranslation = translate + add
			resetRating = ', rating=0.0, seq=""' if self.rating_cbox.instate(['selected']) else ''

			self.db.execute('UPDATE ? SET translation=?' + resetRating + ' WHERE id=?', LANG_FROM["token"], newTranslation, self.data[iData]["id"])
			self.data[iData].update({"translation": newTranslation})

			if self.rating_cbox.instate(['selected']):
				# Refresh data
				self.data[iData].update({"rating": 0.0, "seq": ""})
				# Refresh UI
				self.generateSeqInfo(iData)
				self.word_edit_rating["text"] = self.data[iData]["rating"]

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
		self.scrollFrame.after(1000, self.loadDictionary)
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


	def loadDictionary(self):
		print("Dictionary loaded!")

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
		self.word_info_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=(0, 4))
		self.word_edit_rating["text"] = self.data[i]["rating"]

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


	def get(self):
		return [self.dict_page, self.page_button]


	def restart(self):
		self.addContainer.pack_forget()
		self.dictContainer.pack(fill=BOTH, expand=True)
		self.toggleTranslation(True)
		self.clearAddForm()
			

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


if __name__ == '__main__':
	main()