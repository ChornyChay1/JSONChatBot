import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import json
import os
import shutil


class BotConfigurator:
    def __init__(self, root):
        self.root = root
        self.root.title("Настройка Telegram бота")
        self.questions = {}
        self.current_qid = None
        self.filename = None 

        self.files_dir = os.path.join(os.path.dirname(__file__), "files")
        if not os.path.exists(self.files_dir):
            os.makedirs(self.files_dir)

        self.setup_ui()

    def setup_ui(self):
        # Левая часть - список вопросов и кнопки
        left_frame = tk.Frame(self.root)
        left_frame.pack(side=tk.LEFT, fill=tk.Y)

        self.question_listbox = tk.Listbox(left_frame, width=40)
        self.question_listbox.pack(fill=tk.Y, expand=True)
        self.question_listbox.bind("<<ListboxSelect>>", self.on_select_question)

        btn_frame = tk.Frame(left_frame)
        btn_frame.pack()
        tk.Button(btn_frame, text="Добавить", command=self.add_question).pack(side=tk.LEFT)
        tk.Button(btn_frame, text="Удалить", command=self.delete_question).pack(side=tk.LEFT)
        tk.Button(btn_frame, text="Сохранить", command=self.save_question).pack(side=tk.LEFT)

        # Правая часть - детали вопроса
        right_frame = tk.Frame(self.root)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Тип вопроса (выпадающий список)
        tk.Label(right_frame, text="Тип вопроса").pack()
        self.type_var = tk.StringVar()
        self.type_dropdown = ttk.Combobox(
            right_frame,
            textvariable=self.type_var,
            values=["text", "video", "audio"]
        )
        self.type_dropdown.pack(fill=tk.X)
        self.type_dropdown.bind("<<ComboboxSelected>>", self.update_media_fields)

        # Текст вопроса
        tk.Label(right_frame, text="Текст вопроса").pack()
        self.q_text = tk.Text(right_frame, height=4)
        self.q_text.pack(fill=tk.X)

        # Варианты ответа
        tk.Label(right_frame, text="Варианты ответа (по одному в строке)").pack()
        self.options_text = tk.Text(right_frame, height=4)
        self.options_text.pack(fill=tk.X)

        # Загрузка медиафайлов
        self.video_frame = tk.Frame(right_frame)
        self.video_frame.pack(fill=tk.X)
        tk.Label(self.video_frame, text="Видео файл").pack()
        self.video_file_entry = tk.Entry(self.video_frame)
        self.video_file_entry.pack(fill=tk.X)
        tk.Button(self.video_frame, text="Выбрать видео", command=self.select_video_file).pack()

        self.audio_frame = tk.Frame(right_frame)
        self.audio_frame.pack(fill=tk.X)
        tk.Label(self.audio_frame, text="Аудио файл").pack()
        self.audio_file_entry = tk.Entry(self.audio_frame)
        self.audio_file_entry.pack(fill=tk.X)
        tk.Button(self.audio_frame, text="Выбрать аудио", command=self.select_audio_file).pack()

        # Дополнительные изображения
        tk.Label(right_frame, text="Дополнительные изображения (через запятую)").pack()
        self.additional_images_entry = tk.Entry(right_frame)
        self.additional_images_entry.pack(fill=tk.X)
        tk.Button(right_frame, text="Добавить изображения", command=self.select_additional_images).pack()

        # Ветвление
        self.branches_frame = tk.Frame(right_frame)
        self.branches_frame.pack(fill=tk.X)
        tk.Label(self.branches_frame, text="Ветвление (в формате: вариант: ID)").pack()
        self.branches_text = tk.Text(self.branches_frame, height=4)
        self.branches_text.pack(fill=tk.X)

        # Меню
        menubar = tk.Menu(self.root)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Открыть JSON", command=self.load_json)
        file_menu.add_command(label="Сохранить", command=self.save_json)
        file_menu.add_command(label="Сохранить как...", command=lambda: self.save_json(save_as=True))
        menubar.add_cascade(label="Файл", menu=file_menu)
        self.root.config(menu=menubar)

        self.update_media_fields()

    def update_media_fields(self, event=None):
        qtype = self.type_var.get()
        self.video_frame.pack_forget()
        self.audio_frame.pack_forget()
        if qtype == "video":
            self.video_frame.pack(fill=tk.X)
        elif qtype == "audio":
            self.audio_frame.pack(fill=tk.X)

    def copy_to_files(self, src_path):
        filename = os.path.basename(src_path)
        dest_path = os.path.join(self.files_dir, filename)
        shutil.copy(src_path, dest_path)
        return os.path.relpath(dest_path, os.path.dirname(__file__))

    def select_video_file(self):
        path = filedialog.askopenfilename(filetypes=[("Video Files", "*.mp4 *.avi *.mkv")])
        if path:
            rel_path = self.copy_to_files(path)
            self.video_file_entry.delete(0, tk.END)
            self.video_file_entry.insert(0, rel_path)

    def select_audio_file(self):
        path = filedialog.askopenfilename(filetypes=[("Audio Files", "*.mp3 *.wav *.m4a")])
        if path:
            rel_path = self.copy_to_files(path)
            self.audio_file_entry.delete(0, tk.END)
            self.audio_file_entry.insert(0, rel_path)

    def select_additional_images(self):
        paths = filedialog.askopenfilenames(filetypes=[("Image Files", "*.png *.jpg *.jpeg")])
        if paths:
            copied_paths = [self.copy_to_files(p) for p in paths]
            self.additional_images_entry.delete(0, tk.END)
            self.additional_images_entry.insert(0, ",".join(copied_paths))

    def load_json(self):
        path = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")])
        if path:
            with open(path, "r", encoding="utf-8") as f:
                self.questions = json.load(f)
            self.filename = path
            self.refresh_question_list()

    def save_json(self, save_as=False):
        if not save_as and self.filename:
            path = self.filename
        else:
            path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON Files", "*.json")])
            if not path:
                return
            self.filename = path

        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.questions, f, ensure_ascii=False, indent=4)
        messagebox.showinfo("Сохранено", "Файл успешно сохранён!")

    def refresh_question_list(self):
        self.question_listbox.delete(0, tk.END)
        for qid in sorted(self.questions.keys()):
            q = self.questions[qid]
            self.question_listbox.insert(tk.END, f"{qid}: {q.get('question', '')[:40]}")

    def on_select_question(self, event):
        selection = self.question_listbox.curselection()
        if selection:
            index = selection[0]
            qid = list(sorted(self.questions.keys()))[index]
            self.current_qid = qid
            q = self.questions[qid]

            self.type_var.set(q.get("type", ""))
            self.q_text.delete(1.0, tk.END)
            self.q_text.insert(tk.END, q.get("question", ""))

            options = q.get("options", [])
            self.options_text.delete(1.0, tk.END)
            self.options_text.insert(tk.END, "\n".join(options))

            branches = q.get("branches", {})
            self.branches_text.delete(1.0, tk.END)
            self.branches_text.insert(tk.END, "\n".join([f"{k}: {v}" for k, v in branches.items()]))

            self.video_file_entry.delete(0, tk.END)
            self.video_file_entry.insert(0, q.get("video_file", ""))

            self.audio_file_entry.delete(0, tk.END)
            self.audio_file_entry.insert(0, q.get("audio_file", ""))

            images = q.get("addictional_images", [])
            self.additional_images_entry.delete(0, tk.END)
            self.additional_images_entry.insert(0, ",".join(images))  

    def save_question(self):
        if not self.current_qid:
            messagebox.showwarning("Нет выбранного вопроса", "Выберите вопрос для редактирования.")
            return
        branches = {}
        for line in self.branches_text.get(1.0, tk.END).strip().split("\n"):
            if ":" in line:
                opt, nid = line.split(":", 1)
                branches[opt.strip()] = nid.strip()

        q = {
            "type": self.type_var.get(),
            "question": self.q_text.get(1.0, tk.END).strip(),
            "options": [opt.strip() for opt in self.options_text.get(1.0, tk.END).strip().split("\n") if opt.strip()],
            "branching": True,
            "branches": branches,
            "next_id": "",
            "video_file": self.video_file_entry.get().strip(),
            "audio_file": self.audio_file_entry.get().strip(),
            "addictional_images": [img.strip() for img in self.additional_images_entry.get().strip().split(",") if img.strip()]
        }

        self.questions[self.current_qid] = q
        self.refresh_question_list()

    def add_question(self):
        existing_ids = set(self.questions.keys())
        base = "Q"
        i = 1
        while f"{base}{i}" in existing_ids:
            i += 1
        new_id = f"{base}{i}"
        self.questions[new_id] = {
            "type": "text",
            "question": "",
            "options": [],
            "branching": True,
            "branches": {},
            "next_id": "",
            "video_file": "",
            "audio_file": "",
            "addictional_images": [],
        }
        self.refresh_question_list()

    def delete_question(self):
        if self.current_qid and messagebox.askyesno("Удалить?", f"Удалить вопрос {self.current_qid}?"):
            del self.questions[self.current_qid]
            self.current_qid = None
            self.refresh_question_list()


if __name__ == "__main__":
    root = tk.Tk()
    app = BotConfigurator(root)
    root.mainloop()