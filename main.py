from flask import (
    Flask, render_template, url_for,
    request, flash, get_flashed_messages,
    redirect, session, abort, g, make_response
)
import sqlite3
import os
from FDataBase import FDataBase
from werkzeug.security import generate_password_hash, check_password_hash
from UserLogin import UserLogin
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from forms import LoginForm, RegisterForm
from admin.admin import admin

# Config
DATABASE = '/flsite.db'
DEBUG = True
SECRET_KEY = 'a97b1a690e9d69c214a9988e06bb3fb024c44010'
MAX_CONTENT_LENGHT = 1024 * 1024

app = Flask(__name__)
app.config.from_object(__name__)
app.config.update(dict(DATABASE=os.path.join(app.root_path, 'flsite.db')))

app.register_blueprint(admin, url_prefix='/admin')

login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = "Авторизуйтесь для доступа к закрытым страницам"
login_manager.login_message_category = 'success'


@login_manager.user_loader
def load_user(user_id):
    return UserLogin().fromDB(user_id, DBASE)


def connect_db():
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn


def create_db():
    db = connect_db()
    with app.open_resource('sq_db.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()
    db.close()


def get_db():
    if not hasattr(g, 'link_db'):
        g.link_db = connect_db()
    return g.link_db


DBASE = None


@app.before_request
def before_request():
    global DBASE
    db = get_db()
    DBASE = FDataBase(db)


@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'link_db'):
        g.link_db.close()


@app.route('/')
def index():
    return render_template('index.html', menu=DBASE.getMenu(), posts=DBASE.getPostsAnonce())


@app.route('/add_post', methods=["POST", "GET"])
def addPost():
    if request.method == "POST":
        if len(request.form["name"]) > 4 and len(request.form["post"]) > 10:
            res = DBASE.addPost(request.form["name"], request.form["post"], request.form["url"])
            if not res:
                flash("Ошибка добавления статьи", category='error')
            else:
                flash("Статья добавлена успешно", category="success")
        else:
            flash("Ошибка добавления статьи", category='error')

    return render_template('add_post.html', title='Добавление статьи', menu=DBASE.getMenu())


@app.route("/post/<alias>")
@login_required
def showPost(alias):
    title, post = DBASE.getPost(alias)
    if not title:
        abort(404)
    return render_template('post.html', title=title, menu=DBASE.getMenu(), post=post)


@app.route('/about')
def about():
    return render_template('about.html', title='О нас', menu=DBASE.getMenu())


@app.route('/contact', methods=["POST", "GET"])
def contact():
    if request.method == "POST":
        if len(request.form["username"]) > 4 and len(request.form["message"]) > 10:
            res = DBASE.addContact(request.form["username"], request.form["email"], request.form["message"])
            if not res:
                flash("Ошибка добавления статьи", category='error')
            else:
                flash("Статья добавлена успешно", category="success")
        else:
            flash("Ошибка добавления статьи", category='error')

    return render_template('contact.html', title='Оставь свой комментарий', menu=DBASE.getMenu())


@app.route("/profile")
@login_required
def profile():
    return render_template("profile.html", menu=DBASE.getMenu(), title="Профиль")


@app.route('/login', methods=["POST", "GET"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('profile'))

    form = LoginForm()

    if form.validate_on_submit():
        user = DBASE.getUserByEmail(form.email.data)
        if user and check_password_hash(user["psw"], form.psw.data):
            userlogin = UserLogin().create(user)
            rm = form.remember.data
            login_user(userlogin, remember=rm)
            return redirect(request.args.get("next") or url_for("profile"))
        flash("Неверная пара логин и пароль", "error")
    return render_template("login.html", menu=DBASE.getMenu(), title='Авторизация', form=form)


@app.route("/register", methods=["POST", "GET"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        hash = generate_password_hash(form.psw.data)
        res = DBASE.addUser(form.name.data, form.email.data, hash)
        if res:
            flash("Вы успешно зарегистрированы", "success")
            return redirect(url_for('login'))
        else:
            flash("Ошибка при добавлении в БД", "error")

    return render_template("register.html", menu=DBASE.getMenu(), title="Регистрация", form=form)


@login_required
@app.route('/logout')
def logout():
    logout_user()
    flash('Вы вышли из аккаунта', "success")
    return redirect(url_for("login"))


@app.errorhandler(404)
def pageNotFound(error):
    return render_template('page404.html', title='Страница не найдена', menu=DBASE.getMenu())


@app.route('/userava')
@login_required
def userava():
    img = current_user.getAvatar(app)
    if not img:
        return ''

    h = make_response(img)
    h.headers['Content-Type'] = 'image/png'
    return h


@app.route('/upload', methods=["POST", "GET"])
@login_required
def upload():
    if request.method == 'POST':
        file = request.files['file']
        if file and current_user.verifyExt(file.filename):
            try:
                img = file.read()
                res = DBASE.updateUserAvatar(img, current_user.get_id())
                if not res:
                    flash("Ошибка обновления аватара", "error")
                flash("Аватар обновлен", "success")
            except FileNotFoundError as e:
                flash("Ошибка чтения файла", "error")
        else:
            flash("Ошибка обновления аватара", "error")

    return redirect(url_for('profile'))


if __name__ == '__main__':
    app.run(debug=True)
