# PyQt6 Conversion Guide for Telegram Media Downloader

## Overview
This guide shows the key patterns for converting your Tkinter application to PyQt6.

## Installation
```bash
pip install PyQt6
```

## Key Conversion Patterns

### 1. Imports
**Tkinter:**
```python
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox, simpledialog, font as tkFont
```

**PyQt6:**
```python
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QCheckBox, QTextEdit, QProgressBar,
    QGroupBox, QFileDialog, QMessageBox, QInputDialog, QMenu, QFrame
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QUrl
from PyQt6.QtGui import QFont, QTextCursor, QDesktopServices, QCursor
```

### 2. Main Window Class
**Tkinter:**
```python
class TelegramDownloaderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("App Title")
        self.root.minsize(600, 650)
```

**PyQt6:**
```python
class TelegramDownloaderGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("App Title")
        self.setMinimumSize(600, 650)
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
```

### 3. Widgets Mapping

| Tkinter | PyQt6 |
|---------|-------|
| `ttk.Label` | `QLabel` |
| `ttk.Entry` | `QLineEdit` |
| `ttk.Button` | `QPushButton` |
| `ttk.Checkbutton` | `QCheckBox` |
| `scrolledtext.ScrolledText` | `QTextEdit` |
| `ttk.Progressbar` | `QProgressBar` |
| `ttk.LabelFrame` | `QGroupBox` |
| `ttk.Frame` | `QWidget` or `QFrame` |

### 4. Variable Binding
**Tkinter:**
```python
self.api_id_var = tk.StringVar(value="")
self.api_id_entry = ttk.Entry(textvariable=self.api_id_var)
value = self.api_id_var.get()
self.api_id_var.set("new value")
```

**PyQt6:**
```python
self.api_id_entry = QLineEdit()
self.api_id_entry.setText("")
value = self.api_id_entry.text()
self.api_id_entry.setText("new value")
```

### 5. Layouts
**Tkinter (grid):**
```python
label.grid(row=0, column=0, sticky=tk.W, padx=5, pady=3)
entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5, pady=3)
```

**PyQt6:**
```python
layout = QGridLayout()
layout.addWidget(label, 0, 0, Qt.AlignmentFlag.AlignLeft)
layout.addWidget(entry, 0, 1)
widget.setLayout(layout)
```

**Tkinter (pack):**
```python
button.pack(side=tk.TOP, fill=tk.X, pady=5)
```

**PyQt6:**
```python
layout = QVBoxLayout()
layout.addWidget(button)
widget.setLayout(layout)
```

### 6. Buttons and Commands
**Tkinter:**
```python
self.login_button = ttk.Button(frame, text="Login", command=self.start_login)
```

**PyQt6:**
```python
self.login_button = QPushButton("Login")
self.login_button.clicked.connect(self.start_login)
```

### 7. Checkboxes
**Tkinter:**
```python
self.skip_var = tk.BooleanVar(value=True)
self.skip_cb = ttk.Checkbutton(frame, text="Skip", variable=self.skip_var)
value = self.skip_var.get()
```

**PyQt6:**
```python
self.skip_cb = QCheckBox("Skip")
self.skip_cb.setChecked(True)
value = self.skip_cb.isChecked()
```

### 8. Message Boxes
**Tkinter:**
```python
messagebox.showinfo("Title", "Message", parent=self.root)
messagebox.showerror("Title", "Error", parent=self.root)
result = messagebox.askyesno("Title", "Question?", parent=self.root)
```

**PyQt6:**
```python
QMessageBox.information(self, "Title", "Message")
QMessageBox.critical(self, "Title", "Error")
result = QMessageBox.question(self, "Title", "Question?",
    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
result_bool = (result == QMessageBox.StandardButton.Yes)
```

### 9. File Dialog
**Tkinter:**
```python
path = filedialog.askdirectory(initialdir="/path", title="Select", parent=self.root)
```

**PyQt6:**
```python
path = QFileDialog.getExistingDirectory(self, "Select", "/path")
```

### 10. Input Dialog
**Tkinter:**
```python
result = simpledialog.askstring("Title", "Prompt:", show='*', parent=self.root)
```

**PyQt6:**
```python
result, ok = QInputDialog.getText(self, "Title", "Prompt:", 
    QLineEdit.EchoMode.Password)
if not ok:
    result = None
```

### 11. Text Widget (Logs)
**Tkinter:**
```python
self.log_text = scrolledtext.ScrolledText(frame, state=tk.DISABLED, height=10)
self.log_text.configure(state=tk.NORMAL)
self.log_text.insert(tk.END, message + '\n')
self.log_text.configure(state=tk.DISABLED)
self.log_text.yview(tk.END)
```

**PyQt6:**
```python
self.log_text = QTextEdit()
self.log_text.setReadOnly(True)
self.log_text.append(message)
self.log_text.moveCursor(QTextCursor.MoveOperation.End)
```

### 12. Progress Bar
**Tkinter:**
```python
self.progress_var = tk.DoubleVar()
self.progress_bar = ttk.Progressbar(frame, variable=self.progress_var, maximum=100)
self.progress_var.set(50)
```

**PyQt6:**
```python
self.progress_bar = QProgressBar()
self.progress_bar.setMaximum(100)
self.progress_bar.setValue(50)
```

### 13. Widget State
**Tkinter:**
```python
widget.config(state=tk.DISABLED)
widget.config(state=tk.NORMAL)
```

**PyQt6:**
```python
widget.setEnabled(False)
widget.setEnabled(True)
```

### 14. Fonts
**Tkinter:**
```python
font = tkFont.Font(family='Arial', size=10, underline=True)
widget.configure(font=font)
```

**PyQt6:**
```python
font = QFont('Arial', 10)
font.setUnderline(True)
widget.setFont(font)
```

### 15. Colors
**Tkinter:**
```python
widget.config(foreground='red', background='white')
```

**PyQt6:**
```python
palette = widget.palette()
palette.setColor(QPalette.ColorRole.WindowText, QColor('red'))
palette.setColor(QPalette.ColorRole.Window, QColor('white'))
widget.setPalette(palette)
# Or use stylesheets:
widget.setStyleSheet("color: red; background-color: white;")
```

### 16. Timer / After
**Tkinter:**
```python
self.root.after(100, self.process_queue)
```

**PyQt6:**
```python
QTimer.singleShot(100, self.process_queue)
# Or for repeating:
self.timer = QTimer()
self.timer.timeout.connect(self.process_queue)
self.timer.start(100)
```

### 17. Close Event
**Tkinter:**
```python
self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
```

**PyQt6:**
```python
def closeEvent(self, event):
    # Your closing logic here
    if should_close:
        event.accept()
    else:
        event.ignore()
```

### 18. Context Menu (Right-click)
**Tkinter:**
```python
menu = tk.Menu(root, tearoff=0)
menu.add_command(label="Copy", command=self.copy)
widget.bind("<Button-3>", lambda e: menu.tk_popup(e.x_root, e.y_root))
```

**PyQt6:**
```python
def contextMenuEvent(self, event):
    menu = QMenu(self)
    menu.addAction("Copy", self.copy)
    menu.exec(event.globalPos())
```

### 19. Clickable Label (Link)
**Tkinter:**
```python
label = ttk.Label(frame, text="Link", cursor="hand2")
label.bind("<Button-1>", self.open_link)
```

**PyQt6:**
```python
label = QLabel('<a href="url">Link</a>')
label.setOpenExternalLinks(True)
# Or with custom handler:
label = QLabel("Link")
label.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
label.mousePressEvent = lambda e: self.open_link()
```

### 20. Main Application Loop
**Tkinter:**
```python
if __name__ == "__main__":
    root = tk.Tk()
    app = TelegramDownloaderGUI(root)
    root.mainloop()
```

**PyQt6:**
```python
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TelegramDownloaderGUI()
    window.show()
    sys.exit(app.exec())
```

## Complete Example Structure

```python
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
import sys

class TelegramDownloaderGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Telegram Media Downloader")
        self.setMinimumSize(600, 650)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        
        # Add your widgets here
        self.setup_ui()
        
    def setup_ui(self):
        # Create widgets and layouts
        pass
    
    def closeEvent(self, event):
        # Handle window close
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TelegramDownloaderGUI()
    window.show()
    sys.exit(app.exec())
```

## Notes

1. **No direct variable binding**: PyQt6 doesn't have `StringVar`, `BooleanVar`, etc. Access widget values directly.

2. **Layouts are explicit**: You must create layout objects and add widgets to them.

3. **Signals and Slots**: Use `.connect()` instead of `command=` parameter.

4. **Read-only text**: Use `setReadOnly(True)` instead of `state=tk.DISABLED`.

5. **Geometry management**: Choose ONE layout type per widget (Grid, VBox, HBox, Form).

6. **Widget parenting**: Pass parent as first argument when creating widgets.

7. **Event handling**: Override event methods like `closeEvent`, `contextMenuEvent`, etc.

8. **Threading**: Use `QThread` with signals for thread-safe GUI updates instead of `threading.Thread`.

## Additional Resources

- PyQt6 Documentation: https://www.riverbankcomputing.com/static/Docs/PyQt6/
- Qt6 Documentation: https://doc.qt.io/qt-6/

## Installation

```bash
pip install PyQt6
```

The original app also needs:
```bash
pip install telethon plyer
```
