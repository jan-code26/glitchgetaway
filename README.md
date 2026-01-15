# 🎮 GlitchGetaway

[![Live Demo](https://img.shields.io/badge/demo-live-brightgreen?style=for-the-badge&logo=github)](https://jan-code26.github.io/glitchgetaway/)
[![GitHub Pages](https://img.shields.io/badge/GitHub-Pages-blue?style=for-the-badge&logo=github)](https://jan-code26.github.io/glitchgetaway/)
[![Python](https://img.shields.io/badge/python-3.8+-blue?style=for-the-badge&logo=python)](https://www.python.org)
[![Django](https://img.shields.io/badge/django-5.2-green?style=for-the-badge&logo=django)](https://www.djangoproject.com)

An educational puzzle escape room where users solve coding/logic puzzles to move from one "glitched room" to another. **Learn coding while playing!** 🚀

## 🌟 Try the Interactive Demo!

**[🎯 Play Demo Now - No Installation Required!](https://jan-code26.github.io/glitchgetaway/)**

Experience GlitchGetaway instantly in your browser. Solve a sample puzzle and see how the game works!

![GlitchGetaway Demo](demo.gif)

## ✨ Features

- 💻 **Multiple Programming Languages**: Learn HTML, CSS, JavaScript, Python, and more
- 🎯 **Interactive Puzzles**: Solve real coding challenges in a fun, engaging format
- 🌙 **Dark/Light Themes**: Comfortable coding experience with theme switching
- 📱 **Mobile Friendly**: Play anywhere, on any device
- 🖥️ **Terminal-Style Interface**: Authentic developer experience with command history
- 🔐 **Admin Panel**: Add, edit, and manage puzzle rooms

## 🚀 Quick Start

### Play the Full Game Locally

1. **Clone the repository**
   ```bash
   git clone https://github.com/jan-code26/glitchgetaway.git
   cd glitchgetaway
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run migrations**
   ```bash
   python manage.py migrate
   ```

4. **Load sample rooms**
   ```bash
   python manage.py loaddata escape_rooms.json
   ```

5. **Start the server**
   ```bash
   python manage.py runserver
   ```

6. **Open your browser**
   Navigate to `http://localhost:8000` and start playing!

## 🎮 How to Play

1. Read the puzzle question carefully
2. Type your answer in the terminal input
3. Press Enter to submit
4. Use special commands:
   - `hint` - Get a hint after 3 attempts
   - `help` - Show available commands
   - `clear` - Clear the terminal screen
5. Solve all rooms to escape the glitch!

## 🛠️ Admin Features

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

## 📝 Technologies Used

- **Backend**: Django 5.2, Python
- **Frontend**: HTML5, CSS3, JavaScript
- **Styling**: Custom terminal-themed CSS with animations
- **Deployment**: GitHub Pages (demo), Gunicorn + WhiteNoise (full app)

## 🤝 Contributing

Contributions are welcome! Feel free to:
- Add new puzzle rooms
- Improve the UI/UX
- Add new features
- Fix bugs
- Improve documentation

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

## 👨‍💻 Author

Created with ❤️ by [jan-code26](https://github.com/jan-code26)

---

**[⭐ Star this repo](https://github.com/jan-code26/glitchgetaway)** if you find it useful!
