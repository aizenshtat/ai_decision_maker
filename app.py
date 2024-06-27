import os
from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, current_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
import anthropic
from datetime import datetime
import logging
from logging.handlers import RotatingFileHandler

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///decisions.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['ANTHROPIC_API_KEY'] = os.environ.get('ANTHROPIC_API_KEY')

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

client = anthropic.Anthropic(api_key=app.config['ANTHROPIC_API_KEY'])

# Set up logging
if not app.debug:
    file_handler = RotatingFileHandler('decision_maker.log', maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('Decision Maker startup')

# User model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Decision model
class Decision(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    question = db.Column(db.String(500), nullable=False)
    framework = db.Column(db.String(50), nullable=False)
    response = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

# Decision Frameworks
DECISION_FRAMEWORKS = {
    "personal": {
        "name": "Personal Decision Framework",
        "steps": [
            "Identify the decision to be made",
            "List your options",
            "Weigh the potential outcomes of each option",
            "Consider your personal values and goals",
            "Make a choice based on the above factors"
        ]
    },
    "business": {
        "name": "Business Decision Framework",
        "steps": [
            "Define the problem or opportunity",
            "Gather relevant information",
            "Identify alternatives",
            "Weigh evidence and analyze options",
            "Choose among alternatives",
            "Take action",
            "Review decision and consequences"
        ]
    },
    "ethical": {
        "name": "Ethical Decision Framework",
        "steps": [
            "Identify the ethical issue",
            "Gather relevant facts",
            "Consider ethical principles (e.g., utilitarianism, deontology)",
            "Consult relevant ethical guidelines or codes",
            "Consider alternative actions",
            "Make a decision and justify it"
        ]
    },
    "swot": {
        "name": "SWOT Analysis Framework",
        "steps": [
            "Identify Strengths",
            "Identify Weaknesses",
            "Identify Opportunities",
            "Identify Threats",
            "Analyze how to leverage strengths and opportunities",
            "Plan how to address weaknesses and threats"
        ]
    },
    "risk_assessment": {
        "name": "Risk Assessment Framework",
        "steps": [
            "Identify potential risks",
            "Assess likelihood of each risk",
            "Evaluate potential impact of each risk",
            "Prioritize risks based on likelihood and impact",
            "Develop risk mitigation strategies",
            "Create a risk management plan"
        ]
    }
}

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def get_decision_framework(decision_type):
    return DECISION_FRAMEWORKS.get(decision_type, DECISION_FRAMEWORKS["personal"])

def get_ai_decision(prompt, decision_type):
    try:
        framework = get_decision_framework(decision_type)
        framework_steps = "\n".join(f"{i+1}. {step}" for i, step in enumerate(framework['steps']))
        
        message = client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=1000,
            messages=[
                {
                    "role": "user",
                    "content": f"Help me make a decision about: {prompt}\n\nUse the following framework ({framework['name']}):\n{framework_steps}\n\nNow, provide your decision advice, following each step of the framework:"
                }
            ]
        )
        return message.content[0].text
    except Exception as e:
        app.logger.error(f"Error in get_ai_decision: {str(e)}", exc_info=True)
        return f"Sorry, I couldn't make a decision at this time. Error: {str(e)}"

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        try:
            data = request.get_json()
            user_input = data.get('user_input')
            decision_type = data.get('decision_type')
            
            if not user_input or not decision_type:
                return jsonify({'error': 'User input and decision type are required'}), 400
            
            app.logger.info(f"New decision request - Type: {decision_type}, Input: {user_input[:50]}...")
            ai_response = get_ai_decision(user_input, decision_type)
            return jsonify({'decision': ai_response})
        except Exception as e:
            app.logger.error(f"Error in index: {str(e)}")
            return jsonify({'error': 'An error occurred while processing your request'}), 500
    return render_template('index.html')

@app.route('/frameworks', methods=['GET'])
def get_frameworks():
    return jsonify({key: value['name'] for key, value in DECISION_FRAMEWORKS.items()})

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            data = request.get_json()
            username = data.get('username')
            password = data.get('password')
            if not username or not password:
                return jsonify({'error': 'Username and password are required'}), 400
            if User.query.filter_by(username=username).first():
                return jsonify({'error': 'Username already exists'}), 400
            user = User(username=username)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            return jsonify({'message': 'User registered successfully'}), 201
        except Exception as e:
            app.logger.error(f"Error in register: {str(e)}")
            return jsonify({'error': 'An error occurred during registration'}), 500
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            data = request.get_json()
            username = data.get('username')
            password = data.get('password')
            if not username or not password:
                return jsonify({'error': 'Username and password are required'}), 400
            user = User.query.filter_by(username=username).first()
            if user and user.check_password(password):
                login_user(user)
                return jsonify({'message': 'Logged in successfully'}), 200
            return jsonify({'error': 'Invalid username or password'}), 401
        except Exception as e:
            app.logger.error(f"Error in login: {str(e)}")
            return jsonify({'error': 'An error occurred during login'}), 500
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return jsonify({'message': 'Logged out successfully'}), 200

@app.route('/save_decision', methods=['POST'])
@login_required
def save_decision():
    data = request.json
    new_decision = Decision(
        user_id=current_user.id,
        question=data['question'],
        framework=data['framework'],
        response=data['response']
    )
    db.session.add(new_decision)
    db.session.commit()
    return jsonify({'message': 'Decision saved successfully'}), 200

@app.route('/get_decisions', methods=['GET'])
@login_required
def get_decisions():
    decisions = Decision.query.filter_by(user_id=current_user.id).order_by(Decision.created_at.desc()).all()
    return jsonify([{
        'id': d.id,
        'question': d.question,
        'framework': d.framework,
        'response': d.response,
        'created_at': d.created_at.isoformat()
    } for d in decisions])

@app.route('/check_login')
def check_login():
    return jsonify({'logged_in': current_user.is_authenticated})

@app.errorhandler(Exception)
def handle_exception(e):
    app.logger.error(f'Unhandled exception: {str(e)}', exc_info=True)
    return jsonify({'error': 'An unexpected error occurred. Please try again later.'}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)