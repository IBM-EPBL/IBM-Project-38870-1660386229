import os
import random,io,base64
from PIL import Image
from werkzeug.utils import secure_filename
from flask import Flask,render_template,request,url_for,redirect,session,send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin,LoginManager, login_user, login_required, logout_user
from flask_wtf import FlaskForm
from wtforms import StringField,PasswordField,SubmitField
from wtforms.validators import InputRequired,Length,ValidationError
from flask_bcrypt import Bcrypt
import phonenumbers,sqlite3
from twilio.rest import Client
from models import models

UPLOAD_FOLDER = os.path.join('static','uploads')
ALLOWED_EXTENSIONS = {'jpg' ,'png','jpeg'}
app = Flask(__name__)
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///user.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = "kishoreakash"

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model,UserMixin):
    id = db.Column(db.Integer,primary_key=True)
    username = db.Column(db.String(20),nullable=False,unique=True)
    phonenum = db.Column(db.String(14),nullable=False,unique=True)
    password = db.Column(db.String(80),nullable=False)

class RegisterForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Username"})
    phonenum = StringField(validators=[InputRequired(), Length(min=13, max=14)], render_kw={"placeholder": "Phonenumber"})
    password = PasswordField(validators=[InputRequired(), Length(min=8, max=20)], render_kw={"placeholder": "Password"})
    submit = SubmitField('Register')

    def validate_username(self, username):
        existing_user_username = User.query.filter_by(username=username.data).first()
        if existing_user_username:
            raise ValidationError('That username already exists. Please choose a different one.')

    def validate_phonenum(self, phonenum):
        existing_user_phonenum = User.query.filter_by(phonenum=phonenum.data).first()
        if existing_user_phonenum:
            raise ValidationError('The phone number already exists. Please choose a different one.')
        try:
            p = phonenumbers.parse(phonenum.data)
            if not phonenumbers.is_valid_number(p):
                raise ValueError()
        except (phonenumbers.phonenumberutil.NumberParseException, ValueError):
            raise ValidationError('Invalid phone number')

class LoginForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Username"})
    password = PasswordField(validators=[InputRequired(), Length(min=8, max=20)], render_kw={"placeholder": "Password"})
    submit = SubmitField('Login')

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login',methods=['POST','GET'])
def login():
    global ans,name,error
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            if bcrypt.check_password_hash(user.password, form.password.data):
                login_user(user)
                connection = sqlite3.connect("user.db")
                crsr = connection.cursor()
                crsr.execute(f'SELECT phonenum FROM user WHERE username = "{form.username.data}" ')
                ans = crsr.fetchone()
                name = form.username.data
                val = getOTPapi(ans[0])
                if val:
                    # return render_template('redirect.html',name=name)
                    return render_template('otp.html',num="******"+str(ans[0][9:]))
        else:
            error = "Username or Password is incorrect"
            return render_template('login.html', form=form, error=error)
    return render_template('login.html',form=form)

def generate_otp():
    return random.randrange(100000,999999)

def getOTPapi(number):
    client = Client(account_sid,auth_token)
    otp = generate_otp()
    body = "Your OTP is "+ str(otp)
    session['response'] = str(otp)
    message = client.messages.create(from_='+13023033155', body=body,to=number)
    if message.sid:
        return True
    else:
        return False

@app.route('/validateotp',methods=['POST','GET'])
def validateotp():
    validate = request.form['otp']
    if 'response' in session:
        s = session['response']
        session.pop('response',None)
        if s == validate:
            return render_template('redirect.html',name=name)
        else:
            val = getOTPapi(ans[0])
            if val:
                return render_template('otp.html',num="******"+str(ans[0][9:]),error="We have resent your OTP. Please enter it correctly.")


@app.route('/register',methods=['POST','GET'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data)
        new_user = User(username=form.username.data, phonenum=form.phonenum.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html',form=form)

@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/show',methods=['POST','GET'])
def show():
    if request.method=="POST":
        img = request.files["image"]
        img = Image.open(img)
        genus = request.form["dropdown"]
        data = io.BytesIO()
        img.save(data,"JPEG")
        # img_filename = secure_filename(img.filename)
        # img.save(os.path.join(app.config['UPLOAD_FOLDER'], img_filename))
        # session['uploaded_img_filepath'] = os.path.join(app.config['UPLOAD_FOLDER'], img_filename)
        # img_filepath = session.get('uploaded_img_filepath',None)
        img_filepath = base64.b64encode(data.getvalue())
        prediction = models.predict(data,genus)
        return render_template('output.html',value=img_filepath.decode('utf-8'),flag=True,pred = prediction[0],content=prediction[1])


@app.route('/predict')
def predict():
    return render_template('predict.html')

@app.route('/redirect')
def redirect():
    return render_template('redirect.html')

if __name__=='__main__':
    app.run(debug=True)
