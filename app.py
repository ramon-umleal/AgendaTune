import os
from flask_migrate import Migrate
from flask_wtf import FlaskForm
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required
from wtforms import StringField, PasswordField, SubmitField, ValidationError
from wtforms.validators import DataRequired, Length, EqualTo
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from models import User, db, Schedule
from formularios.forms import LoginForm, RegisterForm, CadastrarIntervalosForm



app = Flask(__name__)
app.config['SECRET_KEY'] = '123456789'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
migrate = Migrate(app, db)

db.init_app(app)
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            return redirect(url_for('dashboard'))
        flash('Usuário ou senha incorretos', 'error')
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data)
        new_user = User(username=form.username.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash('Usuário criado com sucesso!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/cadastrar_intervalos', methods=['GET', 'POST'])
def cadastrar_intervalos():
    form = CadastrarIntervalosForm()
    if form.validate_on_submit():
        day = form.day.data
        start_time = form.start_time.data
        end_time = form.end_time.data
        audio_file = request.files['audio_file']

        # Verifica se foi enviado um arquivo de áudio
        if audio_file:
            # Salva o arquivo de áudio na pasta "audio" na raiz do seu programa
            filename = secure_filename(audio_file.filename)
            audio_path = os.path.join(app.config['UPLOAD_FOLDER'], 'audio', filename)
            audio_file.save(audio_path)

            # Salva o nome do arquivo e o caminho completo no banco de dados
            agenda = Schedule(
                day=day,
                start_time=start_time,
                end_time=end_time,
                audio_filename=filename,
                audio_path=audio_path,
                duration=30  # Você pode ajustar a duração conforme necessário
            )
            db.session.add(agenda)
            db.session.commit()

            flash('Intervalo cadastrado com sucesso!', 'success')
            return redirect(url_for('cadastrar_intervalos'))

    agendas = Schedule.query.all()
    return render_template('cadastrarintervalos.html', form=form, agendas=agendas, translate_day=translate_day)

def translate_day(day):
    days_translation = {
        'Monday': 'Segunda-feira',
        'Tuesday': 'Terça-feira',
        'Wednesday': 'Quarta-feira',
        'Thursday': 'Quinta-feira',
        'Friday': 'Sexta-feira'
    }
    return days_translation.get(day, day)  #tradução


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=3001, debug=True)
