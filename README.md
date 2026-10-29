# Playlist Music Bot

Telegram bot for creating and managing personal music playlists.

## Current status

The project currently connects to Telegram, supports Persian and English language selection, and stores users, playlists, and songs in SQLite.

## Requirements

- Python 3.11 or newer
- A Telegram bot token from [@BotFather](https://t.me/BotFather)

## Local setup

### 1. Create a virtual environment

```bash
python -m venv .venv
```

Activate it on Windows:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Copy `.env.example` to `.env` and set your Telegram bot token:

```powershell
Copy-Item .env.example .env
```

Never commit `.env` to GitHub.

### 4. Run the project

Make sure `.env` contains a valid token from BotFather.

```bash
python main.py
```

Then open your bot in Telegram and send `/start`. The first run creates the local `playlist_bot.db` database automatically. To add a song, open a playlist, choose **Add song**, and send an audio file. Use `/playlists` to open your playlists quickly.

## Project structure

```text
app/
├── database/
├── handlers/
├── keyboards/
├── models/
└── services/
tests/
main.py
```

## Development roadmap

1. Project scaffold
2. Telegram bot startup and `/start`
3. User registration
4. Playlist management
5. Adding songs to playlists
6. Viewing and managing playlist songs
7. Tests and documentation

