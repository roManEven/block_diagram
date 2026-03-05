https://youtu.be/0I4l7JE23-g

Block Diagram Assistant
Block Diagram Assistant is a Python-based application designed for generating and editing flowcharts using Graphviz, Tkinter, and the xAI Grok API. The program allows users to create diagrams from natural language descriptions, edit DOT code, import data from Excel or text files, and export the final diagrams in multiple formats (PNG, JPEG, PDF).

Key Features
AI Diagram Generation: Create complex flowcharts from simple natural language descriptions using the Grok API.

AI-Powered Editing: Enhance and fix existing DOT code with AI assistance.

Data Integration: Load Excel files (.xlsx, .xls) or text files (.dot, .txt) to build diagrams based on external data.

Interactive Interface: A user-friendly Tkinter UI with support for zooming, panning, and direct canvas interaction.

DOT Code Editor: Built-in editor for manual Graphviz code adjustments with syntax verification.

Context Menus: Convenient right-click shortcuts for copying, pasting, and saving content.

Installation & Setup
Install Dependencies:

Bash
pip install -r requirements.txt
Install Graphviz:

Download and install Graphviz from the official website.

Crucial: Ensure Graphviz is added to your system's PATH environment variable.

API Configuration:

Obtain an API key from xAI Console.

Replace "Your KEY" in the script with your actual API key.

How to Use
1. Launch the Application
Bash
python block_diagram_assistant.py
2. Generating a Flowchart
Select "Generation Mode".

Enter a description in the text field (e.g., "A two-step process connected by an arrow").

(Optional) Upload an Excel or text file. Note: The default data processing is limited to the first 50 rows.

Click "Generate/Fix Diagram" or press Enter.

Review the generated DOT code and the rendered diagram on the canvas.

3. Editing a Flowchart
Select "Edit Mode".

Paste or manually edit the DOT code in the code editor.

(Optional) Provide additional instructions in the description field for the AI to refine the code.

Click "Generate/Fix Diagram" to apply AI improvements or manual changes.

4. Saving Your Work
Canvas: Right-click the diagram to save it as PNG, JPEG, or PDF.

Code Editor: Right-click to save the source code as a .dot or .txt file.

Requirements
Python: 3.10 or higher

Core Libraries (see requirements.txt):

tk==0.1.0

graphviz==0.20.3

openai==1.74.0

pillow==11.1.0

pandas==2.2.3

System: Graphviz installed and added to PATH.

Access: Active xAI API Key.

Example
To create a simple process:

Enter: "start-process-end" in the description.

Click "Generate/Fix Diagram".

The program generates the following DOT code and renders it immediately:

Фрагмент кода
digraph G {
    dpi=300;
    start [shape=ellipse, label="Start"];
    process [shape=box, label="Process"];
    end [shape=ellipse, label="End"];
    
    start -> process;
    process -> end;
}
Would you like me to help you format this into a professional README.md file for GitHub, including icons and better styling?






"**Помощник по созданию блок-схем**"

Python-приложение для генерации и редактирования блок-схем с использованием Graphviz, Tkinter и API Grok от xAI. Программа позволяет создавать диаграммы на основе текстовых описаний, редактировать DOT-код, загружать файлы Excel или текстовые файлы для создания диаграмм на основе данных, а также сохранять диаграммы в различных форматах (PNG, JPEG, PDF).

**Возможности**

Генерация диаграмм: Создание блок-схем на основе описаний на естественном языке с помощью API Grok.

Редактирование диаграмм: Улучшение и правка существующего DOT-кода с поддержкой ИИ.

Поддержка файлов: Загрузка файлов Excel (.xlsx, .xls) или текстовых файлов (.dot, .txt) для использования данных в диаграммах.

Интерактивный интерфейс: Масштабирование, перемещение и сохранение диаграмм через удобный интерфейс Tkinter.

Редактор DOT-кода: Просмотр и ручное редактирование кода Graphviz с проверкой синтаксиса.

Контекстные меню: Удобное копирование, вставка и сохранение содержимого через контекстное меню.

**Установите зависимости:**
 pip install -r requirements.txt

Установите Graphviz:
Скачайте и установите Graphviz с официального сайта.
https://graphviz.org/download/

Добавьте Graphviz в системную переменную PATH.

Получите API-ключ на xAI и Замените "Your KEY" в скрипте на ваш ключ.
https://console.x.ai

**Использование**

Запустите приложение:
python block_diagram_assistant.py

Генерация блок-схемы
Выберите режим «Генерация схемы».
Введите описание блок-схемы в текстовое поле (например, «Процесс с двумя шагами, соединенными стрелкой»).
(Опционально) Загрузите файлы Excel или текстовые файлы с данными.
Установлено ограничение на 50 строк (можно увеличить)
data = pd.read_excel(file_path).head(50)  # Ограничиваем 50 строками

Нажмите «Сгенерировать/Исправить схему» или клавишу Enter для создания диаграммы.

Просмотрите сгенерированный DOT-код и диаграмму на холсте.

Редактирование блок-схемы

Выберите режим «Правка схемы».

Вставьте или отредактируйте существующий DOT-код в редакторе кода.

(Опционально) Укажите дополнительные инструкции в поле описания.

Нажмите «Сгенерировать/Исправить схему» для улучшения кода contingencies.

Примените изменения для обновления диаграммы.

Сохранение диаграмм

Щелкните правой кнопкой мыши на холсте, чтобы сохранить диаграмму в формате PNG, JPEG или PDF.

Щелкните правой кнопкой мыши в редакторе DOT-кода, чтобы сохранить код как файл .dot или .txt.

**Требования**

Python 3.10+
Библиотеки, указанные в requirements.txt:
tk==0.1.0 
graphviz==0.20.3
openai==1.74.0
pillow==11.1.0
pandas==2.2.3

Установленный Graphviz, добавленный в PATH
API-ключ xAI для интеграции с Grok

**Пример**
Для создания простой блок-схемы:

В поле описания введите: «начало-процесс-конец».

Нажмите «Сгенерировать/Исправить схему».

Программа выведет DOT-код, например:

digraph G {
    dpi=300;
    начало [shape=ellipse, label="начало"];
    процес [shape=box, label="процес"];
    конец [shape=ellipse, label="конец"];
    начало -> процес;
    процес -> конец;
}

Диаграмма отобразится на холсте.
![1](https://github.com/user-attachments/assets/7091971a-b9d6-4d7b-a2a6-cea650b6b1d8)

Приветствуются любые улучшения и предложения. Спасибо.
