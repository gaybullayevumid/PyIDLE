# PyIDLE

PyQt6 asosidagi yengil kod muharriri — **Python, Django, HTML, CSS, JavaScript va React** bilan frontend va backend ishlash uchun bitta oynada: muharrir, explorer, terminal va ishga tushirish tugmalari.

## Mundarija

- [O'rnatish](#ornatish)
- [Tezkor boshlash](#tezkor-boshlash)
- [Imkoniyatlar](#imkoniyatlar)
- [Klaviatura yorliqlari](#klaviatura-yorliqlari)
- [Ishga tushirish (Run)](#ishga-tushirish-run)
- [Yangi loyiha shablonlari](#yangi-loyiha-shablonlari)
- [Sozlamalar](#sozlamalar)
- [Exe va installer yig'ish](#exe-va-installer-yigish)
- [Muammolar va yechimlar](#muammolar-va-yechimlar)
- [Struktura](#struktura)

## O'rnatish

**Variant 1 — kod orqali**

```
git clone https://github.com/gaybullayevumid/PyIDLE.git
cd PyIDLE
pip install PyQt6
python main.py
```

**Variant 2 — installer (Windows)**: `PyIDLE-Setup.exe` ni ishga tushiring (administrator huquqi shart emas). Uni o'zingiz yig'ish uchun [Exe va installer yig'ish](#exe-va-installer-yigish) bo'limiga qarang.

**Dasturlar (kerak bo'lganda)**

| Nima uchun | Nima kerak |
|---|---|
| Muharrirning o'zi | Python 3.10+ va PyQt6 |
| Python fayllarini ishga tushirish (F5) | Python PATH da bo'lishi kerak |
| Django | `pip install django` (Run > Python > pip install django) |
| JavaScript / React | [Node.js](https://nodejs.org) (`node` va `npm`) |

## Tezkor boshlash

1. **File > Open Folder** (`Ctrl+Shift+O`) bilan loyiha papkasini oching — chapda explorer chiqadi.
2. Faylni ikki marta bosib oching, tahrirlang, `Ctrl+S` bilan saqlang.
3. `F5` bosing — pastdagi terminalda natija chiqadi.

Yangi bo'sh loyiha kerak bo'lsa: **File > New Project** va shablonni tanlang.

## Imkoniyatlar

**Muharrir**
- Ranglash: Python, JS/JSX/TS, HTML, CSS, JSON, Markdown. HTML ichida Django/Jinja teglari (`{% %}`, `{{ }}`), `<script>` va `<style>` ham ranglanadi. Til fayl kengaytmasidan aniqlanadi.
- Qator raqamlari, joriy qatorni ajratib ko'rsatish, avto-indent (Python'da 4, web fayllarda 2 bo'sh joy).
- `(`, `[`, `{`, `"`, `'` avtomatik juftlanadi; `<div>` yozilganda `</div>` o'zi qo'shiladi.
- Avto-to'ldirish: kalit so'zlar, Django/React/HTML/CSS so'zlari va hujjatdagi so'zlar (2 harf yozilganda chiqadi, `Enter`/`Tab` bilan tanlanadi).
- Jonli xato tekshirish: Python sintaksisi, JSON, JS/CSS qavslari. Xato qizil chiziq bilan, qator raqami qizil rangda va status barda ko'rsatiladi.
- Find / Replace, Go to Line, izohlash, qatorni nusxalash, blok indenti (`Tab` / `Shift+Tab`).
- Fayl qator oxiri (LF yoki CRLF) saqlanadi — git'da keraksiz o'zgarish chiqmaydi.
- 5 MB dan katta va binar fayllar ochilmaydi.

**Explorer**
- O'ng tugma: New File, New Folder, Rename, Delete, Copy Path, Reveal in File Manager.
- `node_modules`, `.git`, `__pycache__` va shunga o'xshash papkalar yashirilgan.
- Oxirgi ochilgan papka keyingi safar avtomatik ochiladi.

**Terminal**
- Istalgan buyruq (`git`, `pip`, `npm` ...), `cd` ishlaydi, `↑`/`↓` — buyruqlar tarixi.
- Jarayon ishlayotganda yozgan matn uning kirishiga yuboriladi (`input()` va so'rovlar uchun).
- **Stop** tugmasi `runserver` va `npm` kabi jarayonlarni bola jarayonlari bilan o'chiradi.

## Klaviatura yorliqlari

| Yorliq | Amal |
|---|---|
| `Ctrl+N` | Yangi fayl |
| `Ctrl+O` / `Ctrl+Shift+O` | Fayl / papka ochish |
| `Ctrl+S` / `Ctrl+Shift+S` / `Ctrl+Alt+S` | Saqlash / Boshqa nom bilan / Hammasini |
| `Ctrl+W` | Tabni yopish |
| `Ctrl+F` / `Ctrl+H` | Qidirish / Almashtirish |
| `Ctrl+G` | Qatorga o'tish |
| `Ctrl+/` | Izoh qo'yish / olib tashlash |
| `Ctrl+Shift+D` | Qatorni nusxalash |
| `Tab` / `Shift+Tab` | Indent / unindent (tanlangan bloklar uchun ham) |
| `Ctrl+B` | Explorer'ni ko'rsatish / yashirish |
| ``Ctrl+` `` | Terminalni ko'rsatish / yashirish |
| `Ctrl+=` / `Ctrl+-` | Shriftni kattalashtirish / kichraytirish |
| `Ctrl+,` | Sozlamalar |
| `F5` / `Shift+F5` | Ishga tushirish / to'xtatish |
| `F6` | HTML'ni brauzerda ochish |
| `F11` | To'liq ekran |

## Ishga tushirish (Run)

**`F5` — joriy fayl** (avval o'zgargan fayllar saqlanadi):

| Fayl | Nima bo'ladi |
|---|---|
| `.py` | `python -u fayl.py` (loyihada `.venv`/`venv` bo'lsa, shu Python ishlatiladi) |
| `manage.py` | `python manage.py runserver` |
| `.js`, `.mjs`, `.cjs` | `node fayl.js` |
| `.html` | Brauzerda ochiladi |
| `.jsx`, `.tsx`, `.ts` | Loyihadagi `npm run dev` yoki `npm run start` |

**Run menyusi**

- **Python**: virtual muhit yaratish (`.venv`), `pip install -r requirements.txt`, `pip install django`.
- **Django** (`manage.py` loyiha ildizida yoki bevosita ichki papkada bo'lishi kerak): `runserver`, `makemigrations`, `migrate`, `collectstatic`, `test`, `startapp...`. `createsuperuser` va `shell` alohida konsol oynasida ochiladi, chunki ular interaktiv.
- **npm / React**: `npm install` va `package.json` dagi barcha scriptlar (`npm run dev`, `npm run build` ...) menyuda avtomatik paydo bo'ladi.

## Yangi loyiha shablonlari

**File > New Project** — nom va joylashuvni tanlaysiz:

| Shablon | Nima yaratiladi | Talab |
|---|---|---|
| HTML / CSS / JS | `index.html`, `style.css`, `script.js` (tugma bosilganda hisoblagich) | — |
| Django | `python -m django startproject <nom>` | Django o'rnatilgan bo'lsin |
| React (Vite) | `npm create vite@latest <nom> -- --template react` | Node.js va internet |

Django va React yaratilgach papka avtomatik ochiladi. Keyin **Run > npm / React > npm install**, so'ng `npm run dev` yoki **Run > Django > runserver**.

## Sozlamalar

`File > Settings` (`Ctrl+,`): mavzu (dark / light), shrift, shrift o'lchami, uzun qatorlarni o'rash. Sozlamalar tizim reyestrida (Windows) yoki konfiguratsiya papkasida saqlanadi.

## Exe va installer yig'ish

Windows'da `build.bat` ni ishga tushirish kifoya. U ikki bosqichdan iborat:

```
pip install pyinstaller
python -m PyInstaller --noconfirm --clean --windowed --name PyIDLE --add-data "themes;themes" main.py
```

Natija: `dist\PyIDLE\PyIDLE.exe`. Installer uchun [Inno Setup 6](https://jrsoftware.org/isinfo.php) kerak:

```
ISCC installer\PyIDLE.iss
```

Natija: `dist\PyIDLE-Setup.exe`.

## Muammolar va yechimlar

| Muammo | Yechim |
|---|---|
| "Python topilmadi" | Python'ni o'rnating va o'rnatishda **Add to PATH** ni belgilang |
| "No module named django" | Run > Python > pip install django |
| "manage.py topilmadi" | Django loyihasining papkasini (yoki uning bevosita ustki papkasini) oching |
| "npm topilmadi" | Node.js o'rnating va dasturni qayta ishga tushiring |
| `createsuperuser` terminalda ishlamaydi | Menyudagi `(console)` variantidan foydalaning |
| Jarayon to'xtamayapti | Terminaldagi **Stop** yoki `Shift+F5` |
| Fayl ochilmayapti | Fayl 5 MB dan katta yoki binar bo'lishi mumkin |

## Struktura

```
main.py                  # kirish nuqtasi
build.bat                # exe + installer yig'ish
editor/
    window.py            # asosiy oyna, menyular, run va loyiha amallari
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
installer/
    PyIDLE.iss           # Inno Setup skripti
```
