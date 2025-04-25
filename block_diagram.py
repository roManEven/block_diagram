import tkinter as tk
from tkinter import scrolledtext, messagebox, filedialog
import re
import graphviz
from openai import OpenAI
from io import BytesIO
from PIL import Image, ImageTk
import pandas as pd
import threading
import os

# Настройки API для Grok
XAI_API_KEY = "Your KEY"
client = OpenAI(api_key=XAI_API_KEY, base_url="https://api.x.ai/v1")


class BlockDiagramAssistant:
    def __init__(self, root):
        self.root = root
        self.root.title("Помощник по рисованию блок-схем")
        self.root.geometry("1000x900")
        self.root.minsize(850, 850)
        self.loaded_files = {}  # Словарь: {file_path: {"data": pd.DataFrame/str, "selected": tk.BooleanVar, "type": "excel"/"text"}}
        self.scale = 1.0
        self.min_scale = 0.1
        self.max_scale = 10.0
        self.image_x = 0
        self.image_y = 0
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.mode = tk.StringVar(value="generate")
        self.mode.trace("w", self.on_mode_change)

        self.create_widgets()
        self.setup_llm_client()
        self.create_context_menus()

    def setup_llm_client(self):
        """Инициализация клиента для работы с LLM"""
        self.llm_client = client

    def create_widgets(self):
        """Создание элементов интерфейса"""
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True)

        paned_container = tk.Frame(main_frame)
        paned_container.pack(fill=tk.BOTH, expand=True)

        main_paned = tk.PanedWindow(paned_container, orient=tk.VERTICAL, sashrelief=tk.RAISED, sashwidth=5)
        main_paned.pack(fill=tk.BOTH, expand=True)

        self.diagram_frame = tk.Frame(main_paned, bg='white', bd=2, relief=tk.SUNKEN)
        main_paned.add(self.diagram_frame, minsize=300)

        self.canvas_frame = tk.Frame(self.diagram_frame)
        self.canvas_frame.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(self.canvas_frame, bg='white')
        self.h_scrollbar = tk.Scrollbar(self.canvas_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        self.h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.v_scrollbar = tk.Scrollbar(self.canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.canvas.configure(xscrollcommand=self.h_scrollbar.set, yscrollcommand=self.v_scrollbar.set)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.canvas.bind("<MouseWheel>", self.zoom)
        self.canvas.bind("<Button-4>", self.zoom)
        self.canvas.bind("<Button-5>", self.zoom)
        self.canvas.bind("<ButtonPress-1>", self.start_drag)
        self.canvas.bind("<B1-Motion>", self.drag)
        self.canvas.bind("<Button-3>", self.show_canvas_menu)
        self.canvas.focus_set()

        bottom_paned = tk.PanedWindow(main_paned, orient=tk.HORIZONTAL, sashrelief=tk.RAISED, sashwidth=5)
        main_paned.add(bottom_paned, minsize=200)

        # Панель с описанием и списком загруженных файлов (вертикально)
        desc_paned = tk.PanedWindow(bottom_paned, orient=tk.VERTICAL, sashrelief=tk.RAISED, sashwidth=5)
        bottom_paned.add(desc_paned, minsize=200)

        input_frame = tk.Frame(desc_paned)
        desc_paned.add(input_frame, minsize=100)

        tk.Label(input_frame, text="Описание блок-схемы:").pack(anchor=tk.W)
        self.description_entry = scrolledtext.ScrolledText(input_frame, wrap=tk.WORD)
        self.description_entry.pack(fill=tk.BOTH, expand=True)
        self.description_entry.bind("<Return>", lambda event: self.generate_or_edit_diagram())

        files_frame = tk.Frame(desc_paned)
        desc_paned.add(files_frame, minsize=100)

        tk.Label(files_frame, text="Загруженные файлы:").pack(anchor=tk.W)
        self.file_list_frame = tk.Frame(files_frame)
        self.file_list_frame.pack(fill=tk.BOTH, expand=True)

        code_frame = tk.Frame(bottom_paned)
        bottom_paned.add(code_frame, minsize=200)

        tk.Label(code_frame, text="Код блок-схемы (DOT):").pack(anchor=tk.W)
        self.code_text = scrolledtext.ScrolledText(code_frame, wrap=tk.WORD)
        self.code_text.pack(fill=tk.BOTH, expand=True)

        button_frame = tk.Frame(main_frame)
        button_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=5)

        mode_frame = tk.Frame(button_frame)
        mode_frame.pack(side=tk.LEFT, padx=10)
        tk.Radiobutton(mode_frame, text="Генерация схемы", variable=self.mode, value="generate").pack(side=tk.LEFT)
        tk.Radiobutton(mode_frame, text="Правка схемы", variable=self.mode, value="edit").pack(side=tk.LEFT, padx=10)

        tk.Button(button_frame, text="Загрузить файл", command=self.load_file).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Сгенерировать/Исправить схему",
                  command=self.generate_or_edit_diagram).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Применить код",
                  command=self.apply_code_changes).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Сбросить масштаб", command=self.reset_zoom).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Очистить",
                  command=self.clear_all).pack(side=tk.LEFT, padx=5)

        self.root.bind("<Configure>", self.on_resize)

    def create_context_menus(self):
        """Создает контекстные меню для текстовых полей и canvas"""
        self.desc_menu = tk.Menu(self.root, tearoff=0)
        self.desc_menu.add_command(label="Копировать выделенное",
                                   command=lambda: self.copy_selected(self.description_entry))
        self.desc_menu.add_command(label="Копировать все",
                                   command=lambda: self.copy_all(self.description_entry))
        self.desc_menu.add_command(label="Вставить",
                                   command=lambda: self.paste_text(self.description_entry))

        self.code_menu = tk.Menu(self.root, tearoff=0)
        self.code_menu.add_command(label="Копировать выделенное",
                                   command=lambda: self.copy_selected(self.code_text))
        self.code_menu.add_command(label="Копировать все",
                                   command=lambda: self.copy_all(self.code_text))
        self.code_menu.add_command(label="Вставить",
                                   command=lambda: self.paste_text(self.code_text))
        self.code_menu.add_command(label="Сохранить схему",
                                   command=self.save_scheme)

        self.canvas_menu = tk.Menu(self.root, tearoff=0)
        self.canvas_menu.add_command(label="Сохранить как...", command=self.save_diagram)

        self.description_entry.bind("<Button-3>", self.show_context_menu)
        self.code_text.bind("<Button-3>", self.show_context_menu)

    def show_context_menu(self, event):
        """Показывает контекстное меню для текстового поля"""
        widget = event.widget
        if widget == self.description_entry:
            self.desc_menu.tk_popup(event.x_root, event.y_root)
        elif widget == self.code_text:
            self.code_menu.tk_popup(event.x_root, event.y_root)

    def show_canvas_menu(self, event):
        """Показывает контекстное меню для canvas"""
        self.canvas_menu.tk_popup(event.x_root, event.y_root)

    def copy_selected(self, text_widget):
        """Копирует выделенный текст в буфер обмена"""
        try:
            selected = text_widget.get(tk.SEL_FIRST, tk.SEL_LAST)
            self.root.clipboard_clear()
            self.root.clipboard_append(selected)
        except tk.TclError:
            pass

    def copy_all(self, text_widget):
        """Копирует весь текст из виджета в буфер обмена"""
        all_text = text_widget.get("1.0", tk.END)
        self.root.clipboard_clear()
        self.root.clipboard_append(all_text)

    def paste_text(self, text_widget):
        """Вставляет текст из буфера обмена"""
        try:
            text_widget.insert(tk.INSERT, self.root.clipboard_get())
        except tk.TclError:
            pass

    def save_diagram(self):
        """Сохраняет схему в файл"""
        if not hasattr(self, 'original_image'):
            messagebox.showwarning("Предупреждение", "Нет схемы для сохранения")
            return

        file_types = [
            ("PNG files", "*.png"),
            ("JPEG files", "*.jpg"),
            ("PDF files", "*.pdf")
        ]

        file_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=file_types,
            title="Сохранить схему как"
        )

        if not file_path:
            return

        try:
            dot_code = self.code_text.get("1.0", tk.END).strip()

            if file_path.endswith('.pdf'):
                if "digraph" in dot_code and "dpi" not in dot_code:
                    lines = dot_code.splitlines()
                    for i, line in enumerate(lines):
                        if "digraph" in line and "{" in line:
                            lines[i] = line.replace("{", "{\n    dpi=300;")
                            break
                    dot_code = "\n".join(lines)

                graph = graphviz.Source(dot_code)
                graph.render(file_path.replace('.pdf', ''), format='pdf', cleanup=True)
            else:
                format = 'PNG' if file_path.endswith('.png') else 'JPEG'
                self.original_image.save(file_path, format=format)

            messagebox.showinfo("Успех", f"Схема успешно сохранена в {file_path}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить схему: {str(e)}")

    def save_scheme(self):
        """Сохраняет DOT-код как текстовый файл и добавляет его в список загруженных файлов"""
        dot_code = self.code_text.get("1.0", tk.END).strip()
        if not dot_code or "digraph" not in dot_code:
            messagebox.showwarning("Предупреждение", "Поле с кодом DOT пустое или не содержит валидного кода.")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".dot",
            filetypes=[("DOT files", "*.dot"), ("Text files", "*.txt"), ("All files", "*.*")],
            title="Сохранить схему как"
        )

        if not file_path:
            return

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(dot_code)

            # Добавляем файл в список загруженных
            if file_path not in self.loaded_files:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = f.read()
                selected = tk.BooleanVar(value=True)
                self.loaded_files[file_path] = {"data": data, "selected": selected, "type": "text"}
                self.update_file_list()
                messagebox.showinfo("Успех",
                                    f"Схема сохранена как {os.path.basename(file_path)} и добавлена в загруженные файлы.")
            else:
                messagebox.showinfo("Информация", f"Файл {os.path.basename(file_path)} уже загружен.")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить файл: {str(e)}")

    def load_file(self):
        """Загрузка Excel или текстового файла"""
        file_paths = filedialog.askopenfilenames(filetypes=[
            ("All supported files", "*.xlsx *.xls *.dot *.txt"),
            ("Excel files", "*.xlsx *.xls"),
            ("DOT/Text files", "*.dot *.txt")
        ])
        for file_path in file_paths:
            if file_path in self.loaded_files:
                messagebox.showinfo("Информация", f"Файл {os.path.basename(file_path)} уже загружен.")
                continue
            try:
                if file_path.endswith(('.xlsx', '.xls')):
                    data = pd.read_excel(file_path).head(50)  # Ограничиваем 50 строками
                    file_type = "excel"
                else:  # .dot или .txt
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = f.read()
                    file_type = "text"

                selected = tk.BooleanVar(value=True)
                self.loaded_files[file_path] = {"data": data, "selected": selected, "type": file_type}
                self.update_file_list()
                messagebox.showinfo("Успех", f"Файл {os.path.basename(file_path)} успешно загружен!")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось загрузить файл {os.path.basename(file_path)}: {str(e)}")

    def update_file_list(self):
        """Обновляет список загруженных файлов с чек-боксами, фильтруя по режиму"""
        for widget in self.file_list_frame.winfo_children():
            widget.destroy()

        current_mode = self.mode.get()
        for file_path, info in self.loaded_files.items():
            # В режиме правки показываем только текстовые файлы с валидным DOT-кодом
            if current_mode == "edit" and (info["type"] != "text" or "digraph" not in info["data"]):
                continue

            frame = tk.Frame(self.file_list_frame)
            frame.pack(fill=tk.X, pady=2)
            chk = tk.Checkbutton(frame, variable=info["selected"])
            chk.pack(side=tk.LEFT)
            file_label = f"{os.path.basename(file_path)} ({info['type']})"
            tk.Label(frame, text=file_label, anchor=tk.W).pack(side=tk.LEFT, fill=tk.X, expand=True)

    def on_mode_change(self, *args):
        """Обработчик изменения режима для обновления списка файлов"""
        self.update_file_list()

    def ask_grok(self, question, is_edit_mode=False):
        """Отправляет вопрос к Grok и возвращает ответ."""
        try:
            system_message = """Ты - полезный помощник, который генерирует или исправляет DOT-код Graphviz для блок-схем. 
            Всегда присылайте только тот блок DOT-кода, который может быть напрямую выполнен библиотекой Python graphviz.
            Названия узлов должны оставаться на языке, указанном в описании или данных файлов, без перевода.
            Используйте стандартные формы блок-схем: прямоугольники для процессов, ромбы для решений и т. д.
            Если предоставлены данные из Excel или текстовых файлов, используйте их для создания блок-схемы, следуя описанию пользователя.
            Обязательно добавь атрибут dpi=300 в определение графа, например: digraph G { dpi=300; ... }"""

            if is_edit_mode:
                system_message += """\nТвоя задача - исправить предоставленный DOT-код, улучшив его читаемость, структуру или устранив ошибки, сохраняя исходный язык названий.
                Если предоставлены дополнительные DOT-коды из загруженных файлов, используйте их как справочный материал для улучшения основного кода, но не заменяйте его напрямую."""

            completion = self.llm_client.chat.completions.create(
                model="grok-3-mini-beta",
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": question},
                ],
            )
            return completion.choices[0].message.content
        except Exception as e:
            return f"Ошибка: {str(e)}"

    def extract_dot_code(self, text):
        """Извлекает DOT код из ответа LLM"""
        matches = re.findall(r'```(?:dot)?\s*(.*?)\s*```', text, re.DOTALL)
        if matches:
            return matches[0]
        return text

    def generate_or_edit_diagram(self, event=None):
        """Генерация или правка блок-схемы в зависимости от режима"""
        if self.mode.get() == "edit":
            dot_code = self.code_text.get("1.0", tk.END).strip()
            if not dot_code or "digraph" not in dot_code:
                messagebox.showwarning(
                    "Предупреждение",
                    "Пожалуйста, сгенерируйте или введите DOT-код для правки.\n"
                    "Код должен начинаться с 'digraph'."
                )
                return
        else:
            description = self.description_entry.get("1.0", tk.END).strip()
            if not description and not any(info["selected"].get() for info in self.loaded_files.values()):
                messagebox.showwarning("Предупреждение",
                                       "Пожалуйста, введите описание блок-схемы или выберите хотя бы один файл.")
                return

        # Сохраняем текущий код перед обработкой
        current_code = self.code_text.get("1.0", tk.END).strip()

        # Показываем индикацию выполнения
        self.code_text.delete("1.0", tk.END)
        if self.mode.get() == "generate":
            self.code_text.insert(tk.END, "Генерация кода... Выполняется...\n")
        else:
            self.code_text.insert(tk.END, f"Исходный код:\n{current_code}\n\nПравка кода... Выполняется...\n")
        self.root.update()

        # Запускаем обработку в фоновом потоке
        description = self.description_entry.get("1.0", tk.END).strip()
        thread = threading.Thread(target=self._process_diagram, args=(description, current_code))
        thread.start()

    def _process_diagram(self, description, current_code):
        """Фоновая обработка запроса"""
        try:
            if self.mode.get() == "generate":
                prompt = f"""Создай блок-схему на языке DOT для следующего: {description}.
                Используйте простую, четкую структуру с соответствующими формами для каждого элемента.
                Названия узлов должны быть на языке, указанном в описании, без перевода.
                Убедитесь, что график правильно соединен и его легко проследить."""

                # Добавляем данные из выбранных файлов
                selected_files = [fp for fp, info in self.loaded_files.items() if info["selected"].get()]
                if selected_files:
                    prompt += "\n\nДанные из файлов для использования в блок-схеме:"
                    for file_path in selected_files:
                        data = self.loaded_files[file_path]["data"]
                        file_type = self.loaded_files[file_path]["type"]
                        prompt += f"\n\nФайл: {os.path.basename(file_path)} (Тип: {file_type})\n"
                        if file_type == "excel":
                            prompt += data.to_string(index=False)
                        else:  # text
                            prompt += data
            else:
                edit_prompt = f"""Исправь следующий DOT-код, улучшив его читаемость, структуру или устранив ошибки. 
                Сохраняй язык названий узлов, как в исходном коде.
                Не изменяй общую структуру графа без необходимости.
                Сохраняй все оригинальные узлы и связи между ними.
                Если в описании нет конкретных указаний, оставь граф максимально близким к исходному."""

                if description:
                    edit_prompt += f"\n\nУчти следующее описание при правке: {description}"

                # Добавляем данные из выбранных текстовых файлов
                selected_files = [fp for fp, info in self.loaded_files.items() if
                                  info["selected"].get() and info["type"] == "text" and "digraph" in info["data"]]
                if selected_files:
                    edit_prompt += "\n\nДополнительные DOT-коды для справки:"
                    for file_path in selected_files:
                        data = self.loaded_files[file_path]["data"]
                        edit_prompt += f"\n\nФайл: {os.path.basename(file_path)}\n{data}"

                edit_prompt += f"\n\nИсходный код:\n{current_code}"
                prompt = edit_prompt

            # Выполняем запрос к Grok
            response = self.ask_grok(prompt, is_edit_mode=(self.mode.get() == "edit"))
            dot_code = self.extract_dot_code(response)

            # Передаем результат в основной поток для обновления GUI
            self.root.after(0, self._update_diagram, dot_code)

        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Ошибка", f"Произошла ошибка: {str(e)}"))
            self.root.after(0, lambda: self.code_text.insert(tk.END, f"\n\nОшибка: {str(e)}"))

    def _update_diagram(self, dot_code):
        """Обновление интерфейса после завершения обработки"""
        self.code_text.delete("1.0", tk.END)
        self.code_text.insert(tk.END, dot_code)
        self.canvas.delete("all")
        self.render_diagram(dot_code)

    def apply_code_changes(self):
        """Применяет изменения, внесенные пользователем в код DOT"""
        dot_code = self.code_text.get("1.0", tk.END).strip()

        if not dot_code or "digraph" not in dot_code:
            messagebox.showwarning("Предупреждение",
                                   "Поле с кодом DOT пустое или не содержит валидного кода.\n"
                                   "Код должен начинаться с 'digraph'.")
            return

        # Сохраняем текущий код перед обработкой
        self.current_code_before_apply = dot_code

        # Показываем индикацию выполнения (не заменяя код)
        self.code_text.insert(tk.END, "\n\nПрименение кода... Выполняется...")
        self.root.update()

        # Запускаем рендеринг в фоновом потоке
        thread = threading.Thread(target=self._apply_code_in_background, args=(dot_code,))
        thread.start()

    def _apply_code_in_background(self, dot_code):
        """Фоновая обработка применения кода"""
        try:
            self.root.after(0, lambda: self.canvas.delete("all"))
            self.root.after(0, self.render_diagram, dot_code)
            # После успешного применения восстанавливаем исходный код (без сообщения о выполнении)
            self.root.after(0, lambda: self.code_text.delete("1.0", tk.END))
            self.root.after(0, lambda: self.code_text.insert(tk.END, self.current_code_before_apply))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Ошибка", f"Не удалось применить изменения: {str(e)}"))
            # В случае ошибки также восстанавливаем исходный код
            self.root.after(0, lambda: self.code_text.delete("1.0", tk.END))
            self.root.after(0, lambda: self.code_text.insert(tk.END, self.current_code_before_apply))
            self.root.after(0, lambda: self.code_text.insert(tk.END, f"\n\nОшибка: {str(e)}"))

    def render_diagram(self, dot_code):
        """Рендеринг блок-схемы с помощью Graphviz"""
        try:
            # Создаем копию кода для модификации (чтобы не менять исходный)
            modified_dot_code = dot_code

            if "digraph" in modified_dot_code and "dpi" not in modified_dot_code:
                lines = modified_dot_code.splitlines()
                for i, line in enumerate(lines):
                    if "digraph" in line and "{" in line:
                        lines[i] = line.replace("{", "{\n    dpi=300;")
                        break
                modified_dot_code = "\n".join(lines)

            graph = graphviz.Source(modified_dot_code, engine='dot')
            png_data = graph.pipe(format='png')
            self.original_image = Image.open(BytesIO(png_data))

            # Сбрасываем масштаб и позицию
            self.scale = 1.0
            self.image_x = 0
            self.image_y = 0

            # Обновляем размеры canvas
            self.canvas.update_idletasks()
            canvas_width = max(self.canvas.winfo_width(), 100)  # Минимальная ширина
            canvas_height = max(self.canvas.winfo_height(), 100)  # Минимальная высота

            img_width, img_height = self.original_image.size

            # Вычисляем масштаб так, чтобы схема помещалась в canvas
            scale_w = canvas_width / img_width
            scale_h = canvas_height / img_height
            self.scale = min(scale_w, scale_h, 1.0)

            # Устанавливаем минимальный масштаб, чтобы схема оставалась видимой
            if self.scale < self.min_scale:
                self.scale = self.min_scale

            # Центрируем изображение
            self.image_x = (canvas_width - img_width * self.scale) / 2
            self.image_y = (canvas_height - img_height * self.scale) / 2

            self.root.after(0, self.update_image)

        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Ошибка рендеринга",
                                                            f"Не удалось отобразить блок-схему: {str(e)}"))
            self.root.after(0, lambda: self.code_text.insert(tk.END, f"\n\nОшибка при рендеринге: {str(e)}"))

    def update_image(self):
        """Обновляет отображение изображения с учетом масштаба и смещения"""
        if not hasattr(self, 'original_image'):
            return

        new_width = int(self.original_image.size[0] * self.scale)
        new_height = int(self.original_image.size[1] * self.scale)

        if new_width < 1 or new_height < 1:
            self.scale = self.min_scale  # Увеличиваем масштаб, если изображение слишком маленькое
            new_width = int(self.original_image.size[0] * self.scale)
            new_height = int(self.original_image.size[1] * self.scale)

        try:
            resized_image = self.original_image.resize((new_width, new_height), Image.LANCZOS)
            self.photo = ImageTk.PhotoImage(resized_image)

            self.canvas.delete("all")
            self.canvas.create_image(
                self.image_x,
                self.image_y,
                anchor="nw",
                image=self.photo
            )

            self.canvas.configure(scrollregion=(0, 0, new_width, new_height))
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось обновить изображение: {str(e)}")

    def zoom(self, event):
        """Масштабирование изображения колесом мыши"""
        if not hasattr(self, 'original_image'):
            return

        delta = 0
        if event.type == "38":  # Windows/MacOS
            delta = event.delta / 120
        elif event.type == "4":  # Linux
            if event.num == 4:
                delta = 1
            elif event.num == 5:
                delta = -1

        if delta == 0:
            return

        if delta > 0:
            new_scale = self.scale * 1.1
        else:
            new_scale = self.scale / 1.1

        # Ограничиваем масштаб
        new_scale = max(self.min_scale, min(new_scale, self.max_scale))

        mouse_x = self.canvas.canvasx(event.x)
        mouse_y = self.canvas.canvasy(event.y)
        self.image_x = (self.image_x - mouse_x) * (new_scale / self.scale) + mouse_x
        self.image_y = (self.image_y - mouse_y) * (new_scale / self.scale) + mouse_y
        self.scale = new_scale
        self.update_image()

    def reset_zoom(self):
        """Сбрасывает масштаб и центрирует изображение"""
        if not hasattr(self, 'original_image'):
            return
        self.scale = 1.0
        self.image_x = 0
        self.image_y = 0
        self.canvas.update_idletasks()
        canvas_width = max(self.canvas.winfo_width(), 100)
        canvas_height = max(self.canvas.winfo_height(), 100)
        img_width, img_height = self.original_image.size
        scale_w = canvas_width / img_width
        scale_h = canvas_height / img_height
        self.scale = min(scale_w, scale_h, 1.0)
        if self.scale < self.min_scale:
            self.scale = self.min_scale
        self.image_x = (canvas_width - img_width * self.scale) / 2
        self.image_y = (canvas_height - img_height * self.scale) / 2
        self.update_image()

    def start_drag(self, event):
        """Начало перетаскивания изображения"""
        self.drag_start_x = event.x
        self.drag_start_y = event.y

    def drag(self, event):
        """Перетаскивание изображения"""
        if not hasattr(self, 'original_image'):
            return

        dx = event.x - self.drag_start_x
        dy = event.y - self.drag_start_y
        self.image_x += dx
        self.image_y += dy
        self.drag_start_x = event.x
        self.drag_start_y = event.y
        self.update_image()

    def clear_all(self):
        """Очистка всех полей"""
        self.description_entry.delete("1.0", tk.END)
        self.code_text.delete("1.0", tk.END)
        self.canvas.delete("all")
        self.loaded_files = {}
        self.update_file_list()
        self.scale = 1.0
        self.image_x = 0
        self.image_y = 0
        self.min_scale = 0.1
        if hasattr(self, 'original_image'):
            del self.original_image

    def on_resize(self, event):
        """Обработчик изменения размера окна"""
        self.root.update_idletasks()
        self.canvas.update_idletasks()
        if hasattr(self, 'original_image'):
            self.update_image()


if __name__ == "__main__":
    root = tk.Tk()
    app = BlockDiagramAssistant(root)
    root.mainloop()