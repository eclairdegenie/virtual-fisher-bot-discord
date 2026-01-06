# Virtual Fisher Bot (Human-Like)

A sophisticated Python-based automation tool designed for "Virtual Fisher" mechanics. This bot mimics human behavior using randomized movements, reaction times, and intelligent visual recognition to perform fishing tasks while avoiding detection.

**⚠️ DISCLAIMER: This tool is strictly for educational and training purposes only.**
It was created to demonstrate computer vision and automation concepts. The author encourages users to respect the Terms of Service of any platform they interact with.

## Features

- **Human-Like Mouse Movements**: Uses Bezier curves and randomized speeds to simulate real hand movements.
- **Smart Visual Recognition**: Detects game elements like target buttons, chat inputs, and verification requests using OpenCV and EasyOCR.
- **Safety Mechanisms**:
  - **Auto-Stop on Danger**: Immediately stops if words like "admin", "banned", or "verify" are detected on screen.
  - **Remote Control**: Start/Stop the bot remotely via Telegram.
  - **Randomized Intervals**: Variable sleep times to avoid pattern detection.
- **GUI Interface**: User-friendly control panel to start/stop and adjust settings.

## Prerequisites

- **Python 3.10+**
- **Tesseract OCR** (Optional but recommended for better accuracy, depending on EasyOCR setup)
- A screen resolution of at least 1920x1080 (recommended for best image matching).

## Installation

1. **Clone the repository**:
   ```bash
   git clone <your-repo-url>
   cd virtual-fisher-bot
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   *Note: If you have issues with `easyocr` or `torch`, refer to their official documentation for your specific hardware (CUDA/CPU).*

## Configuration

Before running the bot, you **MUST** configure the `config.py` file:

1. Open `config.py` in a text editor.
2. **Telegram Setup** (Required for remote control):
   - Create a bot via `@BotFather` on Telegram.
   - Get your `TELEGRAM_TOKEN`.
   - Get your `TELEGRAM_CHAT_ID` (using `@userinfobot`).
   - Paste them into `config.py`.
3. **Pushover** (Optional):
   - Add your User Key and API Token if you want mobile push notifications.

## Usage

1. **Start the GUI**:
   ```bash
   python gui.py
   ```
2. **Setup your environment**:
   - Ensure the "Target Button" (fishing bobber/button) is visible on screen.
   - Ensure the chat input box is visible (for commands like `/sell`).
3. **Click "START BOT"**.
4. **Stopping**:
   - Click "STOP BOT" in the GUI.
   - Or send `STOP` to your Telegram bot.
   - Or move your mouse rapidly to a corner (Failsafe).

## Customization

- **Images**: If the bot fails to find targets, take new screenshots of:
  - `target_button.png` (The button to click)
  - `chat_input.png` (The chat bar)
  - `verify_header.png` (The "Verification Required" header text)
  - Save them in the root directory, replacing the existing ones.

## Credits

Created by eclair-web.
