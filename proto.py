from tkinter import *
from tkinter import ttk
from ttkthemes import ThemedTk

import os
import ctypes



SCREEN_W = ctypes.windll.user32.GetSystemMetrics(0)
SCREEN_H = ctypes.windll.user32.GetSystemMetrics(1)

WND_W = 600
WND_H = 400

FONT_FAMILY = "Cascadia Code"

PAGES = dict()

def main():
	root = ThemedTk(theme="plastik")
	root.resizable(False, False)
	root.geometry("{}x{}+{}+{}".format(WND_W, WND_H, (SCREEN_W - WND_W) // 2, (SCREEN_H - WND_H) // 2))
	root.configure(background="black")

	# STYLES
	style = ttk.Style()
	style.configure('TFrame', background = '#ab23ff')
	style.configure('page.TButton', background = '#ab23ff', font=(FONT_FAMILY, 14, "bold"))
	style.configure('common.TButton', font=(FONT_FAMILY, 12, "bold"))

	# Generate main components
	f_header = ttk.Frame(root, height=60, relief=SOLID)
	f_buttons = ttk.Frame(root, width=100, relief=SOLID, padding=10)
	f_content = ttk.Frame(root, relief=SOLID)
	f_footer = ttk.Frame(root,height=40, relief=SOLID)
	
	# Set layout for main components
	f_header.pack(side="top", fill=X)
	f_footer.pack(side="bottom", fill=X)
	f_buttons.pack(side="left", anchor="nw")
	f_content.pack(fill=BOTH, expand=True)

	# Create pages and it to global dictionary
	PAGES.update({"exam": ExamPage(f_content, f_buttons)})
	PAGES.update({"dict": DictPage(f_content, f_buttons)})
	# And show first page after
	showPage("exam")





	root.protocol('WM_DELETE_WINDOW', root.destroy)
	root.mainloop()



class ExamPage:
	def __init__(self, f_content, f_buttons):
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

		self.target_word = ttk.Label(self.quiz_page, text="< ENGLISH WORD HERE >", anchor="c")
		fSize = min(30, (14 + 80 // len(self.target_word["text"]))) # 27 letters max reasonable
		self.target_word.configure(font=(FONT_FAMILY, fSize))

		self.guess_name = ttk.Label(self.quiz_page, text="Guess:", width=6, anchor="e", font=(FONT_FAMILY, 14))
		self.answer_entry = ttk.Entry(self.quiz_page, font=(FONT_FAMILY, 18), justify="center")
		self.check_button = ttk.Button(self.quiz_page, text="Check", takefocus=0, style="common.TButton")
		self.stats_frame = ttk.Frame(self.quiz_page)

		self.rating_name = ttk.Label(self.stats_frame, text="Rating:", width=7, anchor="e", font=(FONT_FAMILY, 10))
		self.rating_value = ttk.Label(self.stats_frame, text="20.0", width=4, anchor="w", font=(FONT_FAMILY, 10, "bold"))


		self.guess_name.pack(side="left", anchor="w", fill=Y, pady=(10, 0))
		self.stats_frame.pack(side="top", anchor="n", pady=(0, 0), fill=X, padx=(10, 10))
		self.target_word.pack(side="top", pady=(30, 0), padx=(10, 10))
		self.check_button.pack(side="bottom", anchor="n", fill=Y, pady=(0, 40), padx=(10, 10))
		self.answer_entry.pack(side="left", anchor="w", fill=X, expand=True, padx=(10, 10))

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
	def __init__(self, f_content, f_buttons):
		self.parent = f_content
		# self.buttons = f_buttons
		self.page_button = generateButton(f_buttons, "dict")

		self.dict_page = ttk.Frame(self.parent, relief=SOLID, borderwidth=1)

		
		# DICT PAGE
		self.DICTBGCOLOR = "#fff"
		self.dictContainer = ttk.Frame(self.dict_page, padding=10)
		self.scrollContainer = ttk.Frame(self.dictContainer, relief=SUNKEN, borderwidth=1)
		self.scrollCanvas = Canvas(self.scrollContainer, height=80, bg=self.DICTBGCOLOR)
		self.scrollBar = ttk.Scrollbar(self.scrollContainer, orient="vertical", command=self.scrollCanvas.yview)
		self.scrollFrame = ttk.Frame(self.scrollCanvas)
		self.scrollFrame.bind(
			"<Configure>",
			lambda e: self.scrollCanvas.configure(scrollregion=self.scrollCanvas.bbox("all"))
		)
		self.scrollCanvas.create_window((0, 0), window=self.scrollFrame, anchor="nw")
		self.scrollCanvas.configure(yscrollcommand=self.scrollBar.set)

		self.dict_content = ttk.Label(self.scrollFrame, text="Loading...", wraplength=460, background=self.DICTBGCOLOR)
		self.add_button = ttk.Button(self.dictContainer, text="Add new word", takefocus=0, command=self.toggleDictionary, style="common.TButton")

		self.scrollContainer.pack(fill=BOTH, expand=True)
		self.scrollCanvas.pack(side="left", fill="both", expand=True)
		self.scrollBar.pack(side="right", fill="y")
		self.add_button.pack(side="right", pady=(10, 0))
		# CONTENT
		self.dict_content.grid()

		self.dictContainer.pack(fill=BOTH, expand=True)

		# ADD PAGE
		self.addContainer = ttk.Frame(self.dict_page, relief=SOLID, borderwidth=1, padding=10)
		ttk.Label(self.addContainer, text="< ADD NEW WORD >", font=(FONT_FAMILY, 14), anchor="c").pack(fill=BOTH, expand=True, pady=(0, 10))
		ttk.Button(self.addContainer, text="Back", takefocus=0, command=self.toggleDictionary, style="common.TButton").pack(side="left")
		ttk.Button(self.addContainer, text="Save", takefocus=0, style="common.TButton").pack(side="right")

	


	def toggleDictionary(self):
		if self.dictContainer.winfo_viewable():
			self.dictContainer.pack_forget()
			self.addContainer.pack(fill=BOTH, expand=True)
		else:
			self.addContainer.pack_forget()
			self.dictContainer.pack(fill=BOTH, expand=True)


	def onShown(self):
		pass


	def get(self):
		return [self.dict_page, self.page_button]


	def restart(self):
		self.addContainer.pack_forget()
		self.dictContainer.pack(fill=BOTH, expand=True)
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






		# text = "CATERPILLARIZATION"

		# fSize = 20 + 50 // len(text)
		# lWord = ttk.Label(PAGES[0], text=text, anchor="c", font=(FONT_FAMILY, fSize))
		# lAnswer = ttk.Label(PAGES[0], text="Guess:", width=6, anchor="e", font=(FONT_FAMILY, 14))
		# eAnswer = ttk.Entry(PAGES[0], width=20, font=(FONT_FAMILY, 18), justify="center")
		# bCheck = ttk.Button(PAGES[0], text="Check", takefocus=0)
		# fStats = ttk.Frame(PAGES[0]) #, relief=SOLID, height=40)

		# lRatingWord = ttk.Label(fStats, text="Rating:", width=7, anchor="e", font=(FONT_FAMILY, 10))
		# lRatingValue = ttk.Label(fStats, text="20.0", width=4, anchor="w", font=(FONT_FAMILY, 10, "bold"))


		# fStats.pack(side="top", anchor="n", pady=(0, 0), fill=X)
		# lWord.pack(side="top", pady=(30, 0))#B143FFFF
		# bCheck.pack(side="bottom", anchor="n", pady=(0, 40))
		# lAnswer.pack(side="left", anchor="w")
		# eAnswer.pack(side="left", anchor="w", padx=(10, 10))

		# lRatingWord.pack(side="left", expand=True, anchor="e")
		# lRatingValue.pack(side="right", expand=True, anchor="w", padx=(0,0))



# def toggleDictionary():
# 	if (PAGES_ADD["add"].winfo_viewable()):
# 		PAGES_ADD["add"].pack_forget()
# 		PAGES[1].pack(fill=BOTH, expand=True)
# 	else:
# 		PAGES[1].pack_forget()
# 		PAGES_ADD["add"].pack(side="top", fill=BOTH, expand=True)





# def changePage(s):
# 	for i in range(len(PAGES)):
# 		if PAGES[i].winfo_viewable():
# 			PAGES[i].pack_forget()
# 			BUTTONS[i].state(["!disabled"])
# 			break	
# 	s.pack(fill=BOTH, expand=True)
# 	BUTTONS[PAGES.index(s)].state(["disabled"])































if __name__ == '__main__':
	main()