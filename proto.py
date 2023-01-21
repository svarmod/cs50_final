from tkinter import *
from tkinter import ttk
from ttkthemes import ThemedTk

import os
import ctypes

from cs50 import SQL


DB_FILENAME = "test.db"
DB_FILEPATH = os.path.dirname(os.path.realpath(__file__)) + "\\" + DB_FILENAME

SCREEN_W = ctypes.windll.user32.GetSystemMetrics(0)
SCREEN_H = ctypes.windll.user32.GetSystemMetrics(1)

WND_W = 700
WND_H = 400

FONT_FAMILY = "Cascadia Code"
DICT_ALTBGCOLOR = "#d9c5ff"
DICT_BGCOLOR = "#fff"

PAGES = dict()


def main():

	#Preparing database
	if not os.access(DB_FILEPATH, os.R_OK):
		open(DB_FILEPATH, 'w').close()
	db = SQL("sqlite:///" + DB_FILEPATH)
	if len(db.execute('SELECT name FROM sqlite_master WHERE type="table" AND name="english"')) != 1:
		# Create dictionary table
		db.execute('CREATE TABLE english (id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, word TEXT NOT NULL, translation TEXT DEFAULT "", rating REAL DEFAULT 0.0, seq TEXT DEFAULT "", info TEXT DEFAULT "")')
		# Insert test data
		db.execute('INSERT INTO english(word, translation) VALUES ("cat", "кошка")')
		db.execute('INSERT INTO english(word, translation) VALUES ("dog", "собака")')
		db.execute('INSERT INTO english(word, translation) VALUES ("transient", "переходящий,временный")')
		# db.execute('INSERT INTO english(word, translation) VALUES ("transient", "переходящий,временный,скоротечный,мимолетный")')

		db.execute('INSERT INTO english(word, translation) VALUES ("roof", "крыша")')
		db.execute('INSERT INTO english(word, translation) VALUES ("ball", "мяч")')
		db.execute('INSERT INTO english(word, translation) VALUES ("wall", "стена")')
		db.execute('INSERT INTO english(word, translation) VALUES ("fly", "летать,муха")')
		db.execute('INSERT INTO english(word, translation) VALUES ("hello", "привет")')
		db.execute('INSERT INTO english(word, translation) VALUES ("piano", "пианино")')
		db.execute('INSERT INTO english(word, translation) VALUES ("ear", "ухо")')
		db.execute('INSERT INTO english(word, translation) VALUES ("jorney", "путешествие,поездка")')
		db.execute('INSERT INTO english(word, translation) VALUES ("zoo", "зоопарк")')
		db.execute('INSERT INTO english(word, translation) VALUES ("weather", "погода")')
		db.execute('INSERT INTO english(word, translation) VALUES ("apple", "яблоко")')
		db.execute('INSERT INTO english(word, translation) VALUES ("potato", "картошка")')
		db.execute('INSERT INTO english(word, translation) VALUES ("onion", "лук")')
		db.execute('INSERT INTO english(word, translation) VALUES ("extermination", "уничтожение")')


	# Root
	root = ThemedTk(theme="plastik")
	# root = Tk()
	root.resizable(False, False)
	root.geometry("{}x{}+{}+{}".format(WND_W, WND_H, (SCREEN_W - WND_W) // 2, (SCREEN_H - WND_H) // 2))
	root.configure(background="black")

	# STYLES
	style = ttk.Style()
	# style.configure('TFrame', background = '#ab23ff')
	style.configure('head.TFrame', background = DICT_ALTBGCOLOR)
	style.configure('foot.TFrame', background = DICT_ALTBGCOLOR)
	style.configure('page.TButton', background = '#ab23ff', font=(FONT_FAMILY, 14, "bold"))
	style.configure('common.TButton', font=(FONT_FAMILY, 10, "bold"), width=16)
	style.configure('dict.TButton', font=("Helvetica", 8, "bold"), width=3)
	style.configure('alt_dict.TButton', font=("Helvetica", 8, "bold"), width=3)

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

	# Create pages and it to global dictionary
	PAGES.update({"exam": ExamPage(f_header, f_buttons, f_content, f_footer, db)})
	PAGES.update({"dict": DictPage(f_header, f_buttons, f_content, f_footer, db)})
	# And show first page after
	showPage("dict")

	root.protocol('WM_DELETE_WINDOW', root.destroy)
	root.mainloop()



class ExamPage:
	def __init__(self, f_header, f_buttons, f_content, f_footer, db):

		self.db = db

		self.parent = f_content
		# self.buttons = f_buttons
		self.page_button = generateButton(f_buttons, "exam")

		self.exam_page = ttk.Frame(self.parent, relief=SOLID, borderwidth=1)

		# START PAGE
		self.start_page = ttk.Frame(self.exam_page, relief=SOLID, borderwidth=1, padding=10)
		self.start_button = ttk.Button(self.start_page, text="START EXAM", takefocus=0, padding=8, style="common.TButton")
		self.start_info = ttk.Label(self.start_page, text="< some info >", font=(FONT_FAMILY, 14), anchor="c")

		
		self.start_button.pack(side="top", expand=True)
		self.start_info.pack(side="bottom", fill=X)



		# EXAM PAGE
		self.quiz_page = ttk.Frame(self.exam_page, relief=SOLID, borderwidth=1, padding=10)

		self.target_word = ttk.Label(self.quiz_page, text="<          |          >", anchor="c")
		fSize = min(30, (14 + 80 // len(self.target_word["text"]))) # 27 letters max reasonable
		self.target_word.configure(font=(FONT_FAMILY, fSize))

		self.guess_name = ttk.Label(self.quiz_page, text="Guess:", anchor="e", font=(FONT_FAMILY, 12))
		self.answer_entry = ttk.Entry(self.quiz_page, font=(FONT_FAMILY, 18), justify="center", width=26)
		self.check_button = ttk.Button(self.quiz_page, text="Check", takefocus=0, style="common.TButton")
		self.stats_frame = ttk.Frame(self.quiz_page)

		self.rating_name = ttk.Label(self.stats_frame, text="Rating:", width=7, anchor="e", font=(FONT_FAMILY, 10))
		self.rating_value = ttk.Label(self.stats_frame, text="20.0", width=4, anchor="w", font=(FONT_FAMILY, 10, "bold"))


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

		# PACKING
		# self.start_page.pack(fill=BOTH, expand=True)
		self.quiz_page.pack(fill=BOTH, expand=True)


	def onShown(self):
		pass


	def get(self):
		return [self.exam_page, self.page_button]


	def restart(self):
		print("exam restarted")


class DictPage:
	def __init__(self, f_header, f_buttons, f_content, f_footer, db):

		self.db = db
		self.DICT_LOADED = False

		self.parent = f_content
		# self.buttons = f_buttons
		self.page_button = generateButton(f_buttons, "dict")

		self.dict_page = ttk.Frame(self.parent, relief=SOLID, borderwidth=1)

		
		# DICT PAGE
		self.dictContainer = ttk.Frame(self.dict_page, padding=10)
		self.scrollContainer = ttk.Frame(self.dictContainer, relief=SUNKEN, borderwidth=1)
		self.scrollCanvas = Canvas(self.scrollContainer, width=514, height=80, bg=DICT_BGCOLOR)
		self.scrollBar = ttk.Scrollbar(self.scrollContainer, orient="vertical", command=self.scrollCanvas.yview)
		self.scrollFrame = ttk.Frame(self.scrollCanvas)
		self.scrollFrame.bind(
			"<Configure>",
			lambda e: self.scrollCanvas.configure(scrollregion=self.scrollCanvas.bbox("all"))
		)
		self.scrollCanvas.create_window((0, 0), window=self.scrollFrame, anchor="nw")
		self.scrollCanvas.configure(yscrollcommand=self.scrollBar.set)

		# self.dict_content = ttk.Label(self.scrollFrame, text="Loading...", wraplength=460, background=self.DICT_BGCOLOR)
		self.add_button = ttk.Button(self.dictContainer, text="Add new word", takefocus=0, command=self.toggleDictionary, style="common.TButton")
		self.reload_button = ttk.Button(self.dictContainer, text="Reload", takefocus=0, command=self.reloadDictionary, style="common.TButton")

		self.reveal_button = ttk.Button(self.dictContainer, text="Show translation", width=24, takefocus=0, command=self.toggleTranslation, style="common.TButton")


		self.dict_header = ttk.Frame(self.scrollFrame)
		self.dict_content = ttk.Frame(self.scrollFrame)

		self.dict_header.pack(fill=BOTH, expand=True, anchor="c", pady=(0, 8))
		self.dict_content.pack(fill=BOTH, expand=True, anchor="c")

		# Dictionary header
		ttk.Label(self.dict_header, text="Loading...", background=DICT_BGCOLOR)
		ttk.Label(self.dict_header, text="№", background=DICT_BGCOLOR, font=("Helvetica", 10, "bold"), width=4, anchor="e").grid(row=0, column=0, padx=(0, 2), sticky="nsew")
		ttk.Label(self.dict_header, text="Word", background=DICT_BGCOLOR, font=("Helvetica", 10, "bold"), width=18, anchor="c").grid(row=0, column=1, padx=(0, 0), sticky="nsew")
		ttk.Label(self.dict_header, text="Translation", background=DICT_BGCOLOR, font=("Helvetica", 10, "bold"), width=18, anchor="c").grid(row=0, column=2, padx=(0, 0), sticky="nsew")
		ttk.Label(self.dict_header, text="Additional", background=DICT_BGCOLOR, wraplength=142, font=("Helvetica", 10, "bold"), width=20, anchor="c").grid(row=0, column=3, padx=(0, 0), sticky="nsew")
		ttk.Label(self.dict_header, text="Rating", background=DICT_BGCOLOR, font=("Helvetica", 10, "bold"), width=7, anchor="c").grid(row=0, column=4, padx=(0, 8), sticky="nsew")

		self.scrollContainer.pack(fill=BOTH, expand=True)
		self.scrollCanvas.pack(side="left", fill=BOTH, expand=True)
		self.scrollBar.pack(side="right", fill="y", expand=True)
		self.add_button.pack(side="right", pady=(10, 0))
		self.reload_button.pack(side="left", pady=(10, 0))
		self.reveal_button.pack(side="bottom", pady=(10, 0), padx=(10, 0))

		# CONTENT
		# self.dict_content.grid()
		self.dictContainer.pack(fill=BOTH, expand=True)


		# ADD PAGE
		self.addContainer = ttk.Frame(self.dict_page, relief=SOLID, borderwidth=1, padding=10)
		# ttk.Label(self.addContainer, text="< ADD NEW WORD >", font=(FONT_FAMILY, 14), anchor="c").pack(fill=BOTH, expand=True, pady=(0, 10))


		self.formContainer = ttk.Frame(self.addContainer)
		self.formContainer.pack(fill=Y, expand=True, pady=(50, 0))


		self.word_label = ttk.Label(self.formContainer, text="Word:", font=(FONT_FAMILY, 12), anchor="e")
		self.word_entry = ttk.Entry(self.formContainer, width=23, font=(FONT_FAMILY, 18), justify="center")
		self.translation_label = ttk.Label(self.formContainer, text="Translation:", font=(FONT_FAMILY, 12), anchor="e")
		self.translation_entry = ttk.Entry(self.formContainer, width=23, font=(FONT_FAMILY, 18), justify="center")
		self.additional_label = ttk.Label(self.formContainer, text="Additional:", font=(FONT_FAMILY, 12), anchor="e")
		self.additional_entry = ttk.Entry(self.formContainer, width=23, font=(FONT_FAMILY, 18), justify="center")


		self.word_label.grid(row=0, column=0, sticky="nsew", pady=(12, 12), padx=(0, 10))
		self.translation_label.grid(row=1, column=0, sticky="nsew", pady=(12, 12), padx=(0, 10))
		self.additional_label.grid(row=2, column=0, sticky="nsew", pady=(12, 12), padx=(0, 10))

		self.word_entry.grid(row=0, column=1)
		self.translation_entry.grid(row=1, column=1)
		self.additional_entry.grid(row=2, column=1)

		self.add_info = ttk.Label(self.addContainer, text="<       |       >", font=(FONT_FAMILY, 12), anchor="c")
		self.add_info.pack(fill=X, pady=(0, 20), padx=(123, 0))

		ttk.Button(self.addContainer, text="Back", takefocus=0, command=self.toggleDictionary, style="common.TButton").pack(side="left")
		ttk.Button(self.addContainer, text="Save", takefocus=0, style="common.TButton", command=self.saveWord).pack(side="right")

		



		# lWord = ttk.Label(frame, text="Word", width=15, padding=0, anchor="e").grid(column=0, row=4)
		# eWord = ttk.Entry(frame, width=58)
		# eWord.grid(column=1, row=4, pady=(2, 2), padx=(8, 8))

		# lTranslation = ttk.Label(frame, text="Translation", width=15, padding=0, anchor="e").grid(column=0, row=5)
		# eTranslation = ttk.Entry(frame, width=58)
		# eTranslation.grid(column=1, row=5, pady=(2, 2))

		# lAdditional = ttk.Label(frame, text="Additional", width=15, padding=0, anchor="e").grid(column=0, row=6)
		# eAdditional = ttk.Entry(frame, width=58)
		# eAdditional.grid(column=1, row=6, pady=(2, 2))


		# ttk.Button(self.addContainer, text="Back", takefocus=0, command=self.toggleDictionary, style="common.TButton").pack(side="left")
		# ttk.Button(self.addContainer, text="Save", takefocus=0, style="common.TButton", command=lambda: self.saveWord()).pack(side="right")



	def saveWord(self):
		pass

	
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
			slaves[cntr + 1]["text"] = t[1:]
			cntr += 6
		self.reveal_button["text"] = "Hide translation" if needShow else "Show translation"


	def toggleDictionary(self):
		if self.dictContainer.winfo_viewable():
			self.dictContainer.pack_forget()
			self.addContainer.pack(fill=BOTH, expand=True)
			self.word_entry.focus_set()
			self.word_entry.delete(0,END)
			self.translation_entry.delete(0,END)
			self.additional_entry.delete(0,END)
			self.toggleTranslation(True)
		else:
			self.addContainer.pack_forget()
			self.dictContainer.pack(fill=BOTH, expand=True)
			self.onShown()


	def onShown(self):
		if not self.DICT_LOADED:
			self.loadDictionary()
			self.DICT_LOADED = True


	def loadDictionary(self):
		# print(self.dict_content["text"])

		self.data = self.db.execute("SELECT * FROM english ORDER BY word ASC")
		print("Dictionary loaded!")

		out = ''

		# ttk.Label(self.scrollFrame, text="Loading...", background=DICT_BGCOLOR)

		# ttk.Label(self.scrollFrame, text="№", background=DICT_BGCOLOR, font=("Helvetica", 10, "bold"), width=4, anchor="e").grid(row=0, column=0, 
		# 	padx=(0, 2), pady=(0, 10), sticky="nsew")

		# ttk.Label(self.scrollFrame, text="Word", background=DICT_BGCOLOR, font=("Helvetica", 10, "bold"), width=18, anchor="c").grid(row=0, column=1, 
		# 	padx=(0, 0), pady=(0, 10), sticky="nsew")

		# ttk.Label(self.scrollFrame, text="Translation", background=DICT_BGCOLOR, font=("Helvetica", 10, "bold"), width=18, anchor="c").grid(row=0, column=2, 
		# 	padx=(0, 0), pady=(0, 10), sticky="nsew")

		# ttk.Label(self.scrollFrame, text="Additional", background=DICT_BGCOLOR, wraplength=142, font=("Helvetica", 10, "bold"), width=20, anchor="c").grid(row=0, column=3, 
		# 	padx=(0, 0), pady=(0, 10), sticky="nsew")

		# ttk.Label(self.scrollFrame, text="Rating", background=DICT_BGCOLOR, font=("Helvetica", 10, "bold"), width=7, anchor="c").grid(row=0, column=4, padx=(0, 8), pady=(0, 10), sticky="nsew")

		for i in range(len(self.data)):
			translated = (self.data[i]['translation']).split(',')

			color = DICT_ALTBGCOLOR if i % 2 else DICT_BGCOLOR
			# style = "alt_dict.TButton" if i % 2 else "dict.TButton"

			ttk.Label(self.dict_content, text=str(i + 1), background=color, anchor="e", width=4).grid(row=i + 1, column=0, 
				padx=(0, 0), sticky="nsew")
			ttk.Label(self.dict_content, text=str(self.data[i]['word']), background=color, anchor="c", width=23).grid(row=i + 1, column=1, 
				padx=(0, 0), sticky="nsew")
			# ttk.Label(self.scrollFrame, text=translated[0], background=color, anchor="c").grid(row=i + 1, column=2, 
			# 	padx=(0, 0), sticky="nsew")
			# ttk.Label(self.scrollFrame, text=str(translated[1:]), background=color, wraplength=142, anchor="c").grid(row=i + 1, column=3, 
			# 	padx=(0, 0), sticky="nsew")

			ttk.Label(self.dict_content, text="***", background=color, anchor="c", width=19).grid(row=i + 1, column=2, 
				padx=(0, 0), sticky="nsew")
			ttk.Label(self.dict_content, text="***", background=color, wraplength=142, anchor="c", width=26).grid(row=i + 1, column=3, 
				padx=(0, 0), sticky="nsew")

			ttk.Label(self.dict_content, text=str(self.data[i]['rating']), background=color, anchor="c", width=6).grid(row=i + 1, column=4, 
				padx=(0, 6), sticky="nsew")

			ttk.Button(self.dict_content, text="...", takefocus=0, style="dict.TButton", command=lambda row=i+1, id=self.data[i]['id']: self.editEntry(row, id)).grid(row = i + 1, column=5, sticky="e")
			




	# TABLE english
	# id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, 
	# word TEXT NOT NULL, 
	# translation TEXT DEFAULT "", 
	# rating REAL DEFAULT 0.0, 
	# seq TEXT DEFAULT "", 
	# info TEXT DEFAULT ""

	def editEntry(self, row, id):
		print("Edit row: " + str(row) + ",  id " + str(id) + " word : " + self.data[row - 1].get("word"))


	def get(self):
		return [self.dict_page, self.page_button]


	def restart(self):
		self.addContainer.pack_forget()
		self.dictContainer.pack(fill=BOTH, expand=True)

		self.toggleTranslation(True)

		self.word_entry.focus_set()
		self.word_entry.delete(0,END)
		self.translation_entry.delete(0,END)
		self.additional_entry.delete(0,END)
		# TODO clear fields on add page
			


def generateButton(root, text):
	b = ttk.Button(root, text=text.upper(), padding=0, takefocus=0, command=lambda t=text: showPage(t), style="page.TButton")
	b.pack(fill=BOTH, expand=True)
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


































if __name__ == '__main__':
	main()