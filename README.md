# 📄 FriskOCR 🎯

![FriskOCR Logo](link_to_logo_if_any)

**FriskOCR** is an AI-powered OCR (Optical Character Recognition) tool designed to extract text from images, comics, scanned documents, and manga pages. Built using state-of-the-art deep learning libraries like EasyOCR and Manga-OCR, it offers robust multilingual support, including Japanese, with an optional GUI for ease of use.

---

## 📋 Table of Contents

- [Key Features](#-key-features)
- [Requirements](#️-requirements)
- [Installation Guide](#-installation-guide)
- [Usage](#-usage)
- [Requirements File](#-requirements-file)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🚀 Key Features

- 🧠 **High-Precision OCR**: Extract text from complex image layouts using EasyOCR and Manga-OCR.
- 🌐 **Multilingual Support**: Recognize over 80 languages including Japanese, English, Korean, and more.
- 📚 **Manga/Comic OCR Mode**: Special handling for kanji-rich comic panels and light novels.
- 🖥 **Clipboard OCR**: Detect and extract text directly from clipboard images using hotkeys.
- 🧰 **Simple Setup**: No Docker needed, everything runs locally with Python.
- 🖼 **GUI Interface**: PyQt5-based interface for user-friendly interaction.

---

## ⚙️ Requirements

**System**
- Python 3.10
- 8GB RAM (minimum)
- 3GB free storage
- Internet connection (for model downloads)

---

## 📥 Installation Guide

### 1. Clone the Repository

```bash
git clone https://github.com/FriskOCR/friskocr.git
cd friskocr
```
### 2. Create a Virtual Environment
```bash
python -m venv friskocr
source friskocr/bin/activate    # On Windows: venv\Scripts\activate
```
### 3. Install Dependencies
```bash
pip install -r requirements.txt
```
