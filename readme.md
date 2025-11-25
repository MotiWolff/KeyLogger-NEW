# KeyLogger Project

A comprehensive keylogging solution with secure web interface for monitoring and managing keystroke data across multiple devices.

## Features

- **User-Friendly Interface**: Clean, modern design with dark/light theme support
- **Multi-Device Support**: Monitor keystrokes across macOS and Windows devices
- **Real-Time Monitoring**: View keystroke logs as they happen
- **Secure Storage**: All data is encrypted and securely stored
- **Comprehensive Analytics**: Filter and analyze logs by device, time period, and more

## Technologies

### Frontend
- HTML5, CSS3, JavaScript (ES6+)
- Bootstrap for responsive design
- Font Awesome for icons

### Backend
- Flask (Python web framework)
- SQLAlchemy for database management
- Flask-Login for user authentication
- RESTful API architecture

### Database
- SQLite for development
- Structured storage for users, devices, logs, and sessions

## Requirements

- Python 3.11+
- pip (Python package manager)
- Git
- macOS or Windows operating system

## Installation

### 1. Clone the repository
```bash
git clone https://github.com/MotiWolff/KeyLogger-NEW.git
cd keylogger-project
```

### 2. Create and activate virtual environment

**macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows:**
```bash
python -m venv venv
.\venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment
Create a `.env` file in the project root with:
```
SECRET_KEY=your_secret_key
DATABASE_URL=sqlite:///keylogger.db
```

### 5. Initialize database
```bash
flask db upgrade
```

### 6. Run the application

**Development mode:**
```bash
# Quick start (recommended for development)
./run.sh

# Or run via flask CLI after activating the venv:
# source venv/bin/activate
# flask run --debug
```

**Production mode:**
```bash
flask run
```

### 7. Access the application
Open your browser and navigate to `http://127.0.0.1:5000`

## Quick Run (one command)

Use the included `run.sh` helper to create a virtual environment (if needed), install the minimal dependencies and start the server:

```bash
./run.sh
```

The development server will run on `http://127.0.0.1:12345` by default (or the address printed by the server).

## 📱 Application Features

### User Interface
- Responsive layout adapting to desktop, tablet, and mobile devices
- Intuitive navigation system
- Dark/light theme toggle

### Device Management
- OS-specific setup for macOS and Windows
- Real-time device status monitoring
- Remote device control capabilities

### Logging Capabilities
- Start/stop logging on demand
- View encrypted or decrypted logs
- Real-time log updates
- Device removal functionality

### Log Analysis
- Chronological viewing of logged keystrokes
- Filter by device, date range, or content
- Export functionality in multiple formats
- Statistical dashboard with usage insights

### Security
- Secure user authentication system
- End-to-end encrypted data storage
- Protected API endpoints
- Robust session management

## 🌐 Browser Compatibility
- Google Chrome (recommended)
- Mozilla Firefox
- Apple Safari
- Microsoft Edge

## ⚠️ Troubleshooting

### macOS Issues
If you encounter Xcode-related problems:
1. Install Xcode from App Store
2. Run `xcode-select --install`
3. Accept license with `sudo xcodebuild -license accept`

### Database Issues
If database errors occur:
1. Delete the existing database file
2. Run `flask db upgrade` again

## ⚖️ Important Note
- This software should only be used with proper authorization
- Administrator privileges may be required for certain features
- Linux support is currently not available
- Always ensure you comply with relevant privacy laws when using this software
