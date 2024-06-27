from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, current_user, logout_user
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
import anthropic
from datetime import datetime
import logging
from logging.handlers import RotatingFileHandler
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///decisions.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['ANTHROPIC_API_KEY'] = os.environ.get('ANTHROPIC_API_KEY')

db = SQLAlchemy(app)
migrate = Migrate(app, db)
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

# Feedback model
class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

# Decision Frameworks
DECISION_FRAMEWORKS = {
    "personal": {
        "name": "Personal Decision Framework",
        "steps": [
            {"title": "Identify the decision", "description": "Clearly state the decision you need to make."},
            {"title": "List options", "description": "Write down all possible options you can think of."},
            {"title": "Weigh outcomes", "description": "Consider the potential outcomes of each option."},
            {"title": "Align with values", "description": "Reflect on how each option aligns with your personal values and goals."},
            {"title": "Make a choice", "description": "Based on the above factors, make your decision."}
        ],
        "explanation": "Use this framework for personal decisions that affect your life and well-being.",
        "example": "Choosing a career path or deciding whether to move to a new city."
    },
    "business": {
        "name": "Business Decision Framework",
        "steps": [
            {"title": "Define the problem", "description": "Clearly state the business problem or opportunity."},
            {"title": "Gather information", "description": "Collect relevant data and insights."},
            {"title": "Identify alternatives", "description": "List possible solutions or courses of action."},
            {"title": "Evaluate options", "description": "Assess the pros and cons of each alternative."},
            {"title": "Choose the best option", "description": "Select the most promising solution."},
            {"title": "Implement and monitor", "description": "Put the decision into action and track its effectiveness."}
        ],
        "explanation": "Use this framework for decisions that impact your business or organization.",
        "example": "Deciding whether to launch a new product line or expand into a new market."
    },
    "ethical": {
        "name": "Ethical Decision Framework",
        "steps": [
            {"title": "Identify the ethical issue", "description": "Clearly state the ethical dilemma or question."},
            {"title": "Gather relevant facts", "description": "Collect all pertinent information about the situation."},
            {"title": "Consider ethical principles", "description": "Evaluate the situation using ethical theories (e.g., utilitarianism, deontology)."},
            {"title": "Consult guidelines", "description": "Review any relevant ethical codes or guidelines."},
            {"title": "Consider alternatives", "description": "Brainstorm possible courses of action."},
            {"title": "Make and justify decision", "description": "Choose the most ethical option and explain your reasoning."}
        ],
        "explanation": "Use this framework when facing moral dilemmas or ethical challenges.",
        "example": "Deciding whether to report a colleague's misconduct or determining how to allocate limited resources fairly."
    }
}

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id)) 

def get_decision_framework(decision_type):
    return DECISION_FRAMEWORKS.get(decision_type, DECISION_FRAMEWORKS["personal"])

def get_ai_decision(prompt, decision_type):
    try:
        framework = get_decision_framework(decision_type)
        suggestions = []
        
        for step in framework['steps']:
            step_prompt = f"For the decision: '{prompt}', provide advice for the step: {step['title']}. {step['description']}"
            
            message = client.messages.create(
                model="claude-3-5-sonnet-20240620",
                max_tokens=300,
                messages=[{"role": "user", "content": step_prompt}]
            )
            suggestions.append({"step": step['title'], "advice": message.content[0].text})
        
        return suggestions
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
    return jsonify(DECISION_FRAMEWORKS)

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

@app.route('/compare_decisions', methods=['POST'])
@login_required
def compare_decisions():
    data = request.json
    decision_ids = data.get('decision_ids', [])
    decisions = Decision.query.filter(Decision.id.in_(decision_ids), Decision.user_id == current_user.id).all()
    
    comparison = client.messages.create(
        model="claude-3-5-sonnet-20240620",
        max_tokens=1000,
        messages=[{
            "role": "user", 
            "content": f"Compare the following decisions:\n\n" + "\n\n".join([f"Decision {i+1}:\nQuestion: {d.question}\nFramework: {d.framework}\nResponse: {d.response}" for i, d in enumerate(decisions)])
        }]
    )
    
    return jsonify({'comparison': comparison.content[0].text})

@app.route('/submit_feedback', methods=['POST'])
@login_required
def submit_feedback():
    data = request.json
    new_feedback = Feedback(
        user_id=current_user.id,
        rating=data['rating'],
        comment=data.get('comment', '')
    )
    db.session.add(new_feedback)
    db.session.commit()
    return jsonify({'message': 'Feedback submitted successfully'}), 200

@app.route('/get_feedback', methods=['GET'])
@login_required
def get_feedback():
    feedback = Feedback.query.filter_by(user_id=current_user.id).order_by(Feedback.created_at.desc()).all()
    return jsonify([{
        'id': f.id,
        'rating': f.rating,
        'comment': f.comment,
        'created_at': f.created_at.isoformat()
    } for f in feedback])

@app.errorhandler(Exception)
def handle_exception(e):
    app.logger.error(f'Unhandled exception: {str(e)}', exc_info=True)
    return jsonify({'error': 'An unexpected error occurred. Please try again later.'}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)