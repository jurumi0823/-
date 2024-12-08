from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import os

app = Flask(__name__)
# 使用環境變數，如果環境變數未設置，則使用默認值

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', f'sqlite:///{os.path.join(basedir, "users.db")}')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default_secret_key')  # 默認密鑰
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    gmail = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

class SleepRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    sleep_time = db.Column(db.Time, nullable=False)
    wake_time = db.Column(db.Time, nullable=False)
    sleep_quality = db.Column(db.Integer, nullable=False)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        gmail = request.form['gmail']
        password = request.form['password']
        user = User.query.filter_by(gmail=gmail, password=password).first()
        if user:
            session['user_id'] = user.id
            return redirect(url_for('dashboard'))
        else:
            flash('帳號或密碼錯誤')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        gmail = request.form['gmail']
        password = request.form['password']
        existing_user = User.query.filter_by(gmail=gmail).first()
        if existing_user:
            flash('Gmail已經註冊過')
        else:
            new_user = User(gmail=gmail, password=password)
            db.session.add(new_user)
            db.session.commit()
            flash('註冊成功，請登入')
            return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    if request.method == 'POST':
        date = request.form['date']
        sleep_time = request.form['sleep_time']
        wake_time = request.form['wake_time']
        sleep_quality = request.form['sleep_quality']

        new_record = SleepRecord(
            user_id=user_id,
            date=datetime.strptime(date, '%Y-%m-%d').date(),
            sleep_time=datetime.strptime(sleep_time, '%H:%M').time(),
            wake_time=datetime.strptime(wake_time, '%H:%M').time(),
            sleep_quality=int(sleep_quality)
        )
        db.session.add(new_record)
        db.session.commit()
        flash('睡眠紀錄已保存')

    records = SleepRecord.query.filter_by(user_id=user_id).order_by(SleepRecord.date.asc()).all()
    return render_template('dashboard.html', records=records)

@app.route('/record')
def view_all_records():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    records = SleepRecord.query.filter_by(user_id=user_id).order_by(SleepRecord.date.asc()).all()
    return render_template('view_all_records.html', records=records)

@app.route('/record/<int:record_id>')
def view_record(record_id):
    record = SleepRecord.query.get_or_404(record_id)
    sleep_duration = datetime.combine(datetime.min, record.wake_time) - datetime.combine(datetime.min, record.sleep_time)
    if sleep_duration < timedelta(0):
        sleep_duration += timedelta(days=1)
    return render_template('view_record.html', record=record, sleep_duration=sleep_duration)

@app.route('/sleep_trends')
def sleep_trends():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    records = SleepRecord.query.filter_by(user_id=user_id).all()
    # Calculate weekly and monthly sleep trends (e.g., average sleep duration, quality)
    # Placeholder for trend calculation logic
    return render_template('sleep_trends.html', records=records)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # 在第一次執行時建立資料表
    app.run(debug=True)