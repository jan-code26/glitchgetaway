# GlitchGetaway

[![CI](https://github.com/jan-code26/glitchgetaway/actions/workflows/ci.yml/badge.svg)](https://github.com/jan-code26/glitchgetaway/actions/workflows/ci.yml)
[![Live Demo](https://img.shields.io/badge/demo-live-brightgreen?style=for-the-badge&logo=github)](https://jan-code26.github.io/glitchgetaway/)
[![GitHub Pages](https://img.shields.io/badge/GitHub-Pages-blue?style=for-the-badge&logo=github)](https://jan-code26.github.io/glitchgetaway/)
[![Python](https://img.shields.io/badge/python-3.8+-blue?style=for-the-badge&logo=python)](https://www.python.org)
[![Django](https://img.shields.io/badge/django-5.2-green?style=for-the-badge&logo=django)](https://www.djangoproject.com)

An educational puzzle escape room where users solve coding and logic puzzles to move from one glitched room to another. Learn coding while playing.

## Try the Interactive Demo

**[Play Demo Now - No Installation Required](https://jan-code26.github.io/glitchgetaway/)**

Experience GlitchGetaway instantly in your browser. Solve a sample puzzle and see how the game works.

## Repository Layout

```
glitchgetaway/          ← Django project package (settings, urls, wsgi)
escape/                 ← Django app (models, views, templates, tests)
escape/fixtures/        ← Sample fixture data for seeding the database
manage.py               ← Django management entry point
requirements.txt        ← Python dependencies
portfolio/              ← GitHub Pages demo & portfolio site (not part of the Django app)
.github/workflows/      ← CI (ci.yml) and GitHub Pages deploy (pages.yml)
```

## Features

- **Multiple Programming Languages**: Learn HTML, CSS, JavaScript, Python, and more
- **Interactive Puzzles**: Solve real coding challenges in a fun, engaging format
- **AI-Powered Puzzle Generation**: Auto-generate puzzles using Anthropic Claude, OpenAI GPT, or Google Gemini
- **User Accounts**: Register and login to track your scores persistently
- **Live Game Timer**: Elapsed time counter ticks in real time during gameplay
- **Competitive Leaderboard**: Top-10 completions ranked by speed and accuracy
- **Dark/Light Themes**: Comfortable coding experience with theme switching
- **Mobile Friendly**: Play anywhere, on any device
- **Terminal-Style Interface**: Authentic developer experience with command history
- **Admin Panel**: Add, edit, and manage puzzle rooms

## Quick Start

### Play the Full Game Locally

1. **Clone the repository**
   ```bash
   git clone https://github.com/jan-code26/glitchgetaway.git
   cd glitchgetaway
   ```

2. **Create and activate a virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate   # Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run migrations**
   ```bash
   python manage.py migrate
   ```

5. **Create a superuser (admin)**
   ```bash
   python manage.py createsuperuser
   ```
   You'll be prompted to enter a username, email, and password. This account provides access to the Django admin panel at `/admin/`.

6. **Load sample rooms**
   ```bash
   python manage.py loaddata escape_rooms.json
   ```

7. **Start the server**
   ```bash
   python manage.py runserver
   ```

8. **Open your browser**
   Navigate to `http://localhost:8000` and start playing
   - Play the game: `http://localhost:8000/play/`
   - Admin panel: `http://localhost:8000/admin/` (use superuser credentials)

### Environment Variables

| Variable | Default | Description |
|---|---|---|
| `SECRET_KEY` | insecure dev key | Django secret key — **always set in production** |
| `DEBUG` | `True` | Set to `False` in production |
| `ALLOWED_HOSTS` | `*` | Comma-separated list of allowed hostnames |
| `ADMIN_PASSWORD` | `admin123` | Game admin terminal password — **always change in production** |
| `AI_PROVIDER` | auto-detect | AI provider for puzzle generation: `anthropic`, `openai`, or `gemini` |
| `ANTHROPIC_API_KEY` | — | API key for Anthropic Claude (optional, for AI puzzle generation) |
| `OPENAI_API_KEY` | — | API key for OpenAI GPT (optional, for AI puzzle generation) |
| `GOOGLE_API_KEY` | — | API key for Google Gemini (optional, for AI puzzle generation) |

Example `.env` (not committed; load with your preferred tool or export manually):
```
SECRET_KEY=your-production-secret-key
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
ADMIN_PASSWORD=your-secure-admin-password
ANTHROPIC_API_KEY=your-anthropic-key
```

### Production (Gunicorn + WhiteNoise)

```bash
python manage.py collectstatic --noinput
gunicorn glitchgetaway.wsgi
```

## How to Play

1. (Optional) **Register** at `/play/register/` or **Login** at `/play/login/` to save your score
2. Read the puzzle question carefully
3. Type your answer in the terminal input
4. Press Enter to submit
5. Use special commands:
   - `hint` - Get a hint after 3 attempts
   - `help` - Show available commands
   - `clear` - Clear the terminal screen
   - `leaderboard` - Jump to the leaderboard
6. Solve all rooms to escape the glitch
7. View your time, attempts, and rank on the **Success** screen
8. Challenge others by checking `/play/leaderboard/`

## Admin Features

Access the admin terminal with:
```
sudo login admin123
```

Available admin commands:
- `list_rooms` - View all puzzle rooms
- `add_room` - Add a new puzzle room
- `delete_room <id>` - Remove a room
- `upload_rooms` - Bulk upload rooms via JSON
- `logout` - Exit admin mode

## AI-Powered Puzzle Generation

GlitchGetaway can automatically generate new puzzles using AI. Supports **Anthropic Claude**, **OpenAI GPT**, and **Google Gemini**.

### Setup

1. Install AI dependencies (already in requirements.txt):
   ```bash
   pip install anthropic openai google-generativeai python-dotenv
   ```

2. Set your API key as an environment variable:
   ```bash
   export ANTHROPIC_API_KEY="your-api-key"
   # OR
   export OPENAI_API_KEY="your-api-key"
   # OR
   export GOOGLE_API_KEY="your-api-key"
   ```

3. (Optional) Specify which provider to use:
   ```bash
   export AI_PROVIDER="anthropic"  # or "openai" or "gemini"
   ```

### Generate Puzzles

Generate puzzles by topic:
```bash
python manage.py generate_puzzles --topic "CSS" --count 5
```

Generate with custom prompt:
```bash
python manage.py generate_puzzles --prompt "Create puzzles about Python list comprehensions"
```

Specify a provider:
```bash
python manage.py generate_puzzles --topic "JavaScript" --count 3 --provider anthropic
```

Generated puzzles are saved to the database as `GeneratedPuzzle` objects with a "Pending Review" status. Review them in the Django admin panel (`/admin/`) before approving them as actual game rooms.

## Running Tests

```bash
python manage.py test escape
```

This command discovers and runs all tests in `escape/tests.py`. There are currently **34 tests** across six test classes, all of which pass:

| Test class | # tests | What it covers |
|---|---|---|
| `SmokeTests` | 7 | Key routes return expected HTTP status codes: health check, portfolio page, home redirect, room GET, correct/wrong answer submission, and the success page. |
| `AlternateAnswersTests` | 6 | The multiple-accepted-answers feature on `Room`: primary answer, each alternate answer, case-insensitive matching, and that submitting an alternate answer via the room view redirects correctly. |
| `RoomOrderingTests` | 2 | Rooms are returned in `order`-field sequence, and a correct answer advances the session to the next ordered room. |
| `UserAuthTests` | 8 | Register and login pages load; registration creates a user and redirects; duplicate username shows an error; valid/invalid login credentials; logout redirects to portfolio; authenticated users are redirected away from the register page. |
| `GameSessionTests` | 6 | A `GameSession` is created when a game starts; it is linked to the logged-in user; wrong answers increment `total_attempts`; the success view finalises the session (`completed`, `finished_at`); `elapsed_display` formats time correctly for finished and unfinished sessions. |
| `LeaderboardTests` | 5 | Leaderboard page loads; completed sessions appear on it; entries are ordered fastest-first; typing `leaderboard` in the room redirects there; the success view displays the player's rank. |

## Technologies Used

- **Backend**: Django 5.2, Python 3.8+
- **Frontend**: HTML5, CSS3, JavaScript
- **AI Integration**: Anthropic Claude, OpenAI GPT, Google Gemini (for puzzle generation)
- **Styling**: Custom terminal-themed CSS with animations
- **Deployment**: GitHub Pages (demo), Gunicorn + WhiteNoise (full app)

## Contributing

Contributions are welcome. Feel free to:
- Add new puzzle rooms
- Improve the UI/UX
- Add new features
- Fix bugs
- Improve documentation

## License

This project is open source and available under the [MIT License](LICENSE).

## Author

Created by [jan-code26](https://github.com/jan-code26)

---

**[Star this repo](https://github.com/jan-code26/glitchgetaway)** if you find it useful.
