# PyIDLE

PyQt6 asosidagi yengil kod muharriri — **Python, Django, HTML, CSS, JavaScript va React** (frontend + backend) uchun.

## Ishga tushirish

```
pip install PyQt6
python main.py
```

## Imkoniyatlar

**Muharrir**
- Python, JS/JSX/TS, HTML (Django/Jinja teglari, ichki `<script>`/`<style>`), CSS, JSON, Markdown ranglash
- Qator raqamlari, avto-indent, avtomatik qavs/qo'shtirnoq, `<div>` yozilganda `</div>` ni avto-yopish
- Avtomatik to'ldirish (kalit so'zlar, Django/React/HTML/CSS so'zlari + hujjatdagi so'zlar)
- Xatolarni jonli tekshirish (Python sintaksisi, JSON, JS/CSS qavslari) — qizil chiziq + status bar
- Find / Replace (Ctrl+F / Ctrl+H), Go to Line (Ctrl+G), izoh (Ctrl+/), qatorni nusxalash (Ctrl+Shift+D)
- Dark / Light mavzu, shrift va o'lcham sozlamalari (Ctrl+,), zoom (Ctrl+= / Ctrl+-)
- Fayl qator oxiri (LF/CRLF) saqlanadi

**Loyiha**
- Explorer (o'ng tugma: New File/Folder, Rename, Delete, Copy Path, Reveal)
- File > New Project: **HTML/CSS/JS**, **Django**, **React (Vite)**
- Oxirgi ochilgan papka eslab qolinadi

**Ishga tushirish (Run)**
- `F5` — joriy faylni ishga tushirish (`.py` → Python, `.js` → Node, `.html` → brauzer), `Shift+F5` — to'xtatish
- Python: `.venv` bo'lsa avtomatik ishlatiladi; venv yaratish, `pip install -r requirements.txt`
- Django: `runserver`, `makemigrations`, `migrate`, `collectstatic`, `test`, `startapp`, `createsuperuser`/`shell` (alohida konsolda)
- React/Node: `npm install` va `package.json` dagi barcha `npm run <script>` lar
- Pastki terminal (Ctrl+`): istalgan buyruq, `cd`, tarix (↑/↓), ishlayotgan jarayonga kiritish yuborish

## Talablar

- Python 3.10+ va PyQt6
- Django uchun: `pip install django` (Run > Python > pip install django)
- React/Node uchun: [Node.js](https://nodejs.org)

## Struktura

```
main.py                  # kirish nuqtasi
editor/
    window.py            # asosiy oyna, menyular, run/loyiha amallari
    editor_widget.py     # CodeEditor (qator raqamlari, indent, autocomplete, lint)
    file_explorer.py     # chap panel
    terminal.py          # pastki terminal
    find_bar.py          # qidirish / almashtirish
    settings.py          # sozlamalar va dialog
core/
    syntax.py            # ko'p tilli syntax highlighter
    autocomplete.py      # so'zlar ro'yxati
    linter.py            # xatolarni tekshirish
    runner.py            # buyruqlar, Django/npm yordamchilari, shablonlar
themes/
    dark.qss / light.qss
```
