from translator import translator
from worker import TranslationWorker
from excel_manager import translate_excel
from tkinter import filedialog
import customtkinter as ctk
import config   
import os
import sys
import tkinter as tk

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class App(ctk.CTk):

    def __init__(self):
        super().__init__()
        self.title("AI Excel Translator")
        if getattr(sys, "frozen", False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))

        icon_path = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "translatorAI.ico"
)

        if os.path.exists(icon_path):
            self.iconbitmap(icon_path)    
        self.geometry("900x800")    
        self.resizable(False, False)

        self.filename = ""

        title = ctk.CTkLabel(
            self,
            text="🌍 AI Excel Translator",
            font=("Segoe UI",28,"bold")
        )
        title.pack(pady=20)

        subtitle = ctk.CTkLabel(
    self,
    text="Offline Neural Machine Translation",
    font=("Segoe UI", 14)
)

        subtitle.pack(pady=(0, 20))
        file_label = ctk.CTkLabel(
    self,
    text="📂 Excel file",
    font=("Segoe UI", 16, "bold")
)

        file_label.pack(anchor="w", padx=25)
        
        frame = ctk.CTkFrame(self)
        frame.pack(fill="x", padx=25)

        self.path = ctk.CTkEntry(frame)
        self.path.pack(
            side="left",
            fill="x",
            expand=True,
            padx=(15, 10),
            pady=20
        )


        self.language = ctk.CTkOptionMenu(
            frame,
            values=[
                "🇦🇿 Azerbaijani",
                "🇹🇷 Turkish"
            ],
            width=150
        )

        self.language.set("🇦🇿 Azerbaijani")
        self.language.pack(side="right", padx=(0, 10))

        btn = ctk.CTkButton(
            frame,
            text="Browse",
            command=self.open_file,
            width=100
        )

        btn.pack(side="right", padx=(0, 15))

        self.progress = ctk.CTkProgressBar(self,width=800)

        self.progress.pack(pady=(20, 25))

        self.progress.set(0)

        self.status = ctk.CTkLabel(
            self,
            text="🟡 Status: Ready"
        )

        self.status.pack()

        self.speed_label = ctk.CTkLabel(
    self,
    text="⚡ Speed: -- rows/min"
)

        self.speed_label.pack()

        self.remaining_label = ctk.CTkLabel(
    self,
    text="⏳ Remaining: --"
)

        self.remaining_label.pack()

        device = "🟢 CUDA" if translator.device == "cuda" else "🟡 CPU"

        self.device_label = ctk.CTkLabel(
            self,
            text=f"Device: {device}"
        )

        self.device_label.pack()

        self.start = ctk.CTkButton(
            self,
            text="🚀 Start Translation",
            width=240,
            height=50,
            command=self.start_translate
        )

        self.start.pack(pady=10)

        self.open_button = ctk.CTkButton(
    self,
    text="📂 Open translated file",
    command=self.open_translated_file,
    width=240,
    height=45
)


        log_label = ctk.CTkLabel(
        self,
        text="📋 Logs",
        font=("Segoe UI",16,"bold")
    )

        log_label.pack(anchor="w", padx=25)
        self.log = ctk.CTkTextbox(
            self,
            width=840,
            height=150
        )

        self.log.pack(pady=25)

        self.write_log("🚀 Application started")

        

    

    def open_file(self):

        file = filedialog.askopenfilename(
            filetypes=[("Excel","*.xlsx")]
        )

        if file:

            self.filename=file

            self.path.delete(0,"end")

            self.path.insert(0,file)

            self.write_log("📂 File selected")
            self.write_log(file)


    def write_log(self, text):  
        self.log.insert("end", text + "\n")
        self.log.see("end")

    def start_translate(self):

        import time

        self.start_time = time.time()

        if self.filename == "":

            self.write_log("⚠️ Choose an Excel file first")

            return

        self.status.configure(text="🟢 Status: Translating")
        self.start.configure(
    text="⏳ Translating...",
    state="disabled"
)

        self.write_log("📂 Opening Excel")

        config.TARGET_LANG = config.LANGUAGES[self.language.get()]
        translator.load_memory()

        self.write_log(f"🌐 Language: {config.TARGET_LANG}")

        def progress(current,total):

            percent=current/total

            self.progress.set(percent)

            self.status.configure(
                text=f"{current}/{total}"
            )
            elapsed = time.time() - self.start_time

            speed = 0

            if elapsed > 0:
                speed = current / (elapsed / 60)

            remaining_rows = total - current

            if speed > 0:
                remaining_minutes = remaining_rows / speed
            else:
                remaining_minutes = 0

            self.speed_label.configure(
                text=f"⚡ {speed:.0f} rows/min"
            )
            
            self.remaining_label.configure(
    text=f"⏳ Remaining: {remaining_minutes:.1f} min"
)
        def job():

            output = translate_excel(
                self.filename,
                progress
            )
            self.last_output = output
            self.write_log(f"✅ Finished!\n{output}")

            self.status.configure(
                text="✅ Status: Completed"
            )

            self.progress.set(1)

            self.start.configure(
    text="🚀 Start Translation",
    state="normal"
)
            self.open_button.pack(pady=(5, 15))

        TranslationWorker(job).start()


    def open_translated_file(self):

        if hasattr(self, "last_output"):
            os.startfile(self.last_output)


app=App()

app.mainloop()