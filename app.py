import os
import json
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, current_user, logout_user
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
import anthropic
from datetime import datetime
from dotenv import load_dotenv

# Import the new framework and prompt template
from decision_framework import PERSONAL_DECISION_FRAMEWORK
from prompt_template import generate_prompt

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
    if not os.path.exists('logs'):
        os.mkdir('logs')
    file_handler = RotatingFileHandler('logs/decision_maker.log', maxBytes=10240, backupCount=10)
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
    data = db.Column(json, nullable=False, default={})
    current_step = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


# Feedback model
class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    decision_id = db.Column(db.Integer, db.ForeignKey('decision.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/start_decision', methods=['POST'])
@login_required
def start_decision():
    data = request.json
    new_decision = Decision(
        user_id=current_user.id,
        question=data['question'],
        framework='personal',
        data={'initial_question': data['question']},
        current_step=0
    )
    db.session.add(new_decision)
    db.session.commit()
    first_step = PERSONAL_DECISION_FRAMEWORK['steps'][0]
    return jsonify({
        'decision_id': new_decision.id, 
        'first_step': first_step
    }), 200

@app.route('/api/get_step', methods=['GET'])
@login_required
def get_step():
    decision_id = request.args.get('decision_id')
    decision = Decision.query.get(decision_id)
    if decision.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    step = PERSONAL_DECISION_FRAMEWORK['steps'][decision.current_step]
    current_context = json.dumps(decision.data, indent=2)
    
    ai_prompt = generate_prompt(step, current_context)
    ai_response = get_ai_suggestion(ai_prompt)
    
    return jsonify({
        'step': step,
        'ai_suggestion': ai_response['suggestion'],
        'pre_filled_data': ai_response['pre_filled_data']
    }), 200

@app.route('/api/get_suggestion', methods=['GET'])
@login_required
def get_suggestion():
    decision_id = request.args.get('decision_id')
    step_index = int(request.args.get('step'))
    decision = db.session.get(Decision, decision_id)
    if decision.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    step = PERSONAL_DECISION_FRAMEWORK['steps'][step_index]
    
    # Prepare the full context for the AI prompt
    current_context = {
        'initial_question': decision.question
    }
    
    # Ensure decision.data is a dictionary
    if not isinstance(decision.data, dict):
        decision.data = {}
    
    # Include data from all previous steps
    for i in range(step_index):
        previous_step = PERSONAL_DECISION_FRAMEWORK['steps'][i]
        step_data = decision.data.get(previous_step['title'], {})
        current_context[previous_step['title']] = step_data
    
    app.logger.info(f"Decision ID: {decision_id}, Current step: {step_index}")
    app.logger.info(f"Decision data: {json.dumps(decision.data, indent=2)}")
    app.logger.info(f"Current context for AI prompt: {json.dumps(current_context, indent=2)}")
    
    ai_prompt = generate_prompt(step, current_context)
    ai_response = get_ai_suggestion(ai_prompt)
    
    return jsonify(ai_response), 200

@app.route('/api/submit_step', methods=['POST'])
@login_required
def submit_step():
    data = request.json
    decision = db.session.get(Decision, data['decision_id'])
    if decision.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    current_step_title = PERSONAL_DECISION_FRAMEWORK['steps'][decision.current_step]['title']
    
    # Ensure decision.data is a dictionary
    if not isinstance(decision.data, dict):
        decision.data = {}
    
    # Update the decision data with the new step data
    decision.data[current_step_title] = data['step_data']
    
    app.logger.info(f"Updating decision {decision.id}, step: {current_step_title}")
    app.logger.info(f"New step data: {json.dumps(data['step_data'], indent=2)}")
    app.logger.info(f"Updated decision data: {json.dumps(decision.data, indent=2)}")
    
    try:
        db.session.commit()
        app.logger.info(f"Decision {decision.id} updated successfully")
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error updating decision: {str(e)}")
        return jsonify({'error': 'Error saving decision data'}), 500
    
    # Increment the step after saving the data
    decision.current_step += 1
    db.session.commit()
    
    if decision.current_step >= len(PERSONAL_DECISION_FRAMEWORK['steps']):
        summary = generate_decision_summary(decision)
        decision.current_step = -1  # Indicate decision process is complete
        db.session.commit()
        return jsonify({'completed': True, 'summary': summary}), 200
    
    next_step = PERSONAL_DECISION_FRAMEWORK['steps'][decision.current_step]
    return jsonify({'completed': False, 'next_step': next_step}), 200

@app.route('/login', methods=['POST'])
def login():
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

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return jsonify({'message': 'Logged out successfully'}), 200

@app.route('/api/get_decisions', methods=['GET'])
@login_required
def get_decisions():
    decisions = Decision.query.filter_by(user_id=current_user.id).order_by(Decision.created_at.desc()).all()
    return jsonify([{
        'id': d.id,
        'question': d.question,
        'framework': d.framework,
        'created_at': d.created_at.isoformat(),
        'current_step': d.current_step,
        'data': d.data
    } for d in decisions])

@app.route('/api/check_login')
def check_login():
    return jsonify({'logged_in': current_user.is_authenticated})

@app.route('/api/submit_feedback', methods=['POST'])
@login_required
def submit_feedback():
    data = request.json
    decision_id = data.get('decision_id')
    
    if not decision_id:
        return jsonify({'error': 'No decision_id provided'}), 400
    
    decision = Decision.query.get(decision_id)
    if not decision or decision.user_id != current_user.id:
        return jsonify({'error': 'Invalid decision_id'}), 400
    
    new_feedback = Feedback(
        user_id=current_user.id,
        decision_id=decision_id,
        rating=data['rating'],
        comment=data.get('comment', '')
    )
    db.session.add(new_feedback)
    db.session.commit()
    app.logger.info(f"Feedback submitted for decision {decision_id}")
    return jsonify({'message': 'Feedback submitted successfully'}), 200

def get_ai_suggestion(prompt):
    try:
        app.logger.info(f"Sending prompt to AI: {prompt}")
        response = client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=1024,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        app.logger.info(f"Received AI response: {response.content[0].text}")
        return json.loads(response.content[0].text)
    except json.JSONDecodeError:
        app.logger.error(f"Error decoding JSON from AI response: {response.content[0].text}")
        return {"suggestion": "Error parsing AI suggestion", "pre_filled_data": {}}
    except Exception as e:
        app.logger.error(f"Error in get_ai_suggestion: {str(e)}", exc_info=True)
        return {"suggestion": "Error generating AI suggestion", "pre_filled_data": {}}

def generate_decision_summary(decision):
    prompt = f"""
    Please provide a comprehensive summary of the decision-making process for the following decision:
    
    Decision Question: {decision.question}
    
    Step-by-step data:
    {json.dumps(decision.data, indent=2)}
    
    Please structure your summary in markdown format, including:
    1. A restatement of the decision question
    2. Key points considered during the process
    3. Options evaluated and their outcomes
    4. The final decision or recommendation
    """
    
    try:
        response = client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=2048,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return response.content[0].text
    except Exception as e:
        app.logger.error(f"Error generating decision summary: {str(e)}", exc_info=True)
        return "Error generating decision summary"

def __init__(self, **kwargs):
        super(Decision, self).__init__(**kwargs)
        if self.data is None:
            self.data = {}

@app.errorhandler(Exception)
def handle_exception(e):
    app.logger.error(f'Unhandled exception: {str(e)}', exc_info=True)
    return jsonify({'error': 'An unexpected error occurred. Please try again later.'}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)

    