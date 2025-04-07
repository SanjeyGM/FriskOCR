# 📄 FriskOCR 🎯

![FriskOCR Logo](https://github.com/SanjeyGM/FriskOCR/blob/main/scripts/assets/icon.ico)

**FriskOCR** is a Python-powered OCR (Optical Character Recognition) tool that extracts text from manga, screenshots, and documents using AI. It's optimized for manga-style vertical text and Japanese scripts using EasyOCR and Manga-OCR.

> ✅ Installer available — Just download `FriskOCR.exe` from the [Releases](https://github.com/SanjeyGM/FriskOCR/releases) section and run it directly!

---

## 📋 Table of Contents

- [Key Features](#-key-features)
- [Installer](#-installer)
- [Project Structure](#-project-structure)
- [Usage](#-usage)
- [Contributing](#-contributing)

---

## 🚀 Key Features

- 🧠 **Advanced OCR** using EasyOCR + Manga-OCR
- 🌐 **Multilingual Support**: Handles Japanese, English, Korean, Arabic, etc.
- 📚 **Optimized for Manga**: Vertical/kanji-heavy text support
- 📋 **Clipboard Integration**: OCR from screenshots
- 🖥️ **Optional GUI** via PyQt5
- ⚡ **Portable**: Just run the EXE (no setup needed)

---

## 📦 Installer

Download the latest version of FriskOCR from the [Releases](https://github.com/SanjeyGM/FriskOCR/releases) page.  
Python will be automatically installed.

---

## 🗂 Project Structure

| File/Folder          | Description |
|----------------------|-------------|
| `friskocr/`          | Core OCR logic and helper scripts |
| `logs/`              | Contains logs of OCR activity and errors |
| `model_storage/`     | Stores downloaded OCR models (EasyOCR & Manga-OCR) |
| `Output/`            | All extracted text and processed outputs saved here |
| `FriskOCR.exe`       | Precompiled installer (runs the app) |
| `FriskOCR.spec`      | PyInstaller spec file for building the `.exe` |
| `friskocr_launcher`  | Launcher metadata or documentation |
| `launcher.py`        | The main launch script for GUI/CLI OCR |
| `main.py`            | Entrypoint script integrating OCR and input handling |
| `ocr_config.json`    | User config file for model language, output format, etc. |
| `requirements.txt`   | Lists all Python dependencies (for developers) |
| `setup.iss`          | Installer script (Inno Setup) used to generate `FriskOCR.exe` |
| `pyarmor/` & related | Licensing and obfuscation configs (optional) |
| `__init__.py`        | Makes project importable as a package (for devs) |

---

## 🤝 Contributing

We welcome contributions! To get started:

1. Fork the repository  
2. Create a feature branch:  
   `git checkout -b feature/new-feature`  
3. Commit your changes:  
   `git commit -m 'Add new feature'`  
4. Push to your branch:  
   `git push origin feature/new-feature`  
5. Submit a Pull Request

---



