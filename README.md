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

5. **Load sample rooms**
   ```bash
   python manage.py loaddata escape_rooms.json
   ```

6. **Start the server**
   ```bash
   python manage.py runserver
   ```

7. **Open your browser**
   Navigate to `http://localhost:8000` and start playing

### Environment Variables

| Variable | Default | Description |
|---|---|---|
| `SECRET_KEY` | insecure dev key | Django secret key — **always set in production** |
| `DEBUG` | `True` | Set to `False` in production |
| `ALLOWED_HOSTS` | `*` | Comma-separated list of allowed hostnames |

Example `.env` (not committed; load with your preferred tool or export manually):
```
SECRET_KEY=your-production-secret-key
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
```

### Production (Gunicorn + WhiteNoise)

```bash
python manage.py collectstatic --noinput
gunicorn glitchgetaway.wsgi
```

## How to Play

1. Read the puzzle question carefully
2. Type your answer in the terminal input
3. Press Enter to submit
4. Use special commands:
   - `hint` - Get a hint after 3 attempts
   - `help` - Show available commands
   - `clear` - Clear the terminal screen
5. Solve all rooms to escape the glitch

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

## Running Tests

```bash
python manage.py test escape
```

## Technologies Used

- **Backend**: Django 5.2, Python
- **Frontend**: HTML5, CSS3, JavaScript
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
