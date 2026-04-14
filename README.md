# Brawl Stars Telegram Bot

A Telegram bot that can send friend requests and spectators to Brawl Stars players using the game's native protocol.

## Features

- Send friend requests to any Brawl Stars player
- Send spectators/viewers to Brawl TV matches
- User-friendly interface with inline buttons
- Multi-threaded connection handling

## Commands

| Command | Description |
|---------|-------------|
| `/start` | Start the bot |
| `/help` | Show all commands |
| `/ping` | Check if bot is online |
| `/friend #TAG` | Send 30 friend requests |
| `/friend #TAG 50` | Send 50 friend requests |
| `/spectate #TAG 100` | Send 100 spectators |

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure `config.py` if needed (token already set)

3. Run the bot:
```bash
python main.py
```

## Technical Details

The bot connects directly to Brawl Stars servers (game.brawlstarsgame.com:9339) using:
- TCP socket connections
- Curve25519 key exchange (NaCl/libsodium)
- Brawl Stars native protocol (Piranha/Laser)

## Credits

Based on:
- [FMZNkdv/BsUtils](https://github.com/FMZNkdv/BsUtils)
- [PeterHackz/BrawlStars-Client](https://github.com/PeterHackz/BrawlStars-Client)
