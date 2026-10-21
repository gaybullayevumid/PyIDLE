# PyIDLE

PyQt6 asosidagi oddiy Python code editor.

## Ishga tushirish

```
pip install PyQt6
python main.py
```

## Imkoniyatlar

- Papka ochish (File > Open Folder) va chapdagi explorer
- Papka ichida yangi fayl yaratish (Ctrl+N)
- Tab'lar, saqlash (Ctrl+S / Ctrl+Shift+S), o'zgarishlar belgisi
- Python ranglash, qator raqamlari, auto-indent
- Dark theme (`themes/dark.qss`)

## Struktura

```
main.py                  # kirish nuqtasi
editor/
    window.py            # asosiy oyna, menyu, fayl amallari
    editor_widget.py     # CodeEditor (qator raqamlari, indent)
    file_explorer.py     # chap panel
core/
    syntax.py            # Python syntax highlighter
themes/
    dark.qss
```
