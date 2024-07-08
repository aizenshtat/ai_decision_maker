import json
from json.decoder import JSONDecodeError
import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, send_from_directory
from flask_login import LoginManager, UserMixin, login_user, login_required, current_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.dialects.sqlite import JSON
from flask_migrate import Migrate
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
    data = db.Column(MutableDict.as_mutable(JSON), nullable=False, default={})
    current_step = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    status = db.Column(db.String(20), default='in_progress')

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

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.svg', mimetype='image/svg+xml')

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
    return jsonify({
        'decision_id': new_decision.id, 
        'steps': PERSONAL_DECISION_FRAMEWORK['steps'],
        'total_steps': len(PERSONAL_DECISION_FRAMEWORK['steps'])
    }), 200

@app.route('/api/get_step', methods=['GET'])
@login_required
def get_step():
    decision_id = request.args.get('decision_id')
    step_index = int(request.args.get('step'))
    app.logger.info(f"Fetching step {step_index} for decision {decision_id}")
    decision = Decision.query.get(decision_id)
    if decision.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    if step_index >= len(PERSONAL_DECISION_FRAMEWORK['steps']):
        return jsonify({'error': 'Step index out of range'}), 400
    
    step = PERSONAL_DECISION_FRAMEWORK['steps'][step_index]
    step_title = step['title']
    
    # Retrieve saved data for this step
    saved_data = decision.data.get(step_title, {})
    
    # Retrieve saved AI suggestion for this step
    ai_suggestion = decision.data.get(f"{step_title}_ai_suggestion", "")
    
    return jsonify({
        'step': step,
        'saved_data': saved_data,
        'ai_suggestion': ai_suggestion
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
    
    # Prepare the context for the AI prompt
    current_context = {
        'initial_question': decision.question
    }
    
    # Include data from all previous steps
    for i in range(step_index):
        previous_step = PERSONAL_DECISION_FRAMEWORK['steps'][i]
        step_data = decision.data.get(previous_step['title'], {})
        current_context[previous_step['title']] = step_data
    
    ai_prompt = generate_prompt(step, current_context)
    ai_response = get_ai_suggestion(ai_prompt)
    
    return jsonify(ai_response), 200

@app.route('/api/submit_step', methods=['POST'])
@login_required
def submit_step():
    data = request.json
    decision = Decision.query.get(data['decision_id'])
    if decision.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    step_index = data['step_index']
    step_title = PERSONAL_DECISION_FRAMEWORK['steps'][step_index]['title']
    
    # Save step data
    decision.data[step_title] = data['step_data']
    
    # Save AI suggestion
    decision.data[f"{step_title}_ai_suggestion"] = data['ai_suggestion']
    decision.current_step = step_index
    
    try:
        db.session.commit()
        app.logger.info(f"Decision {decision.id} updated successfully")
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error updating decision: {str(e)}")
        return jsonify({'error': 'Error saving decision data'}), 500
    
    if decision.current_step >= len(PERSONAL_DECISION_FRAMEWORK['steps']) - 1:
        summary = generate_decision_summary(decision)
        decision.status = 'completed'
        db.session.commit()
        return jsonify({'completed': True, 'summary': summary}), 200
    return jsonify({'completed': False}), 200

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        if request.is_json:
            data = request.get_json()
            username = data.get('username')
            password = data.get('password')
        else:
            username = request.form.get('username')
            password = request.form.get('password')
        
        if not username or not password:
            return jsonify({'error': 'Username and password are required'}), 400
        
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return jsonify({'message': 'Login successful'}), 200
        
        return jsonify({'error': 'Invalid username or password'}), 401
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        if request.is_json:
            data = request.get_json()
            username = data.get('username')
            password = data.get('password')
        else:
            username = request.form.get('username')
            password = request.form.get('password')
        
        if not username or not password:
            return jsonify({'error': 'Username and password are required'}), 400
        
        if User.query.filter_by(username=username).first():
            return jsonify({'error': 'Username already exists'}), 400
        
        new_user = User(username=username)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        
        return jsonify({'message': 'Registration successful'}), 200
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

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
        'status': d.status,
        'total_steps': len(PERSONAL_DECISION_FRAMEWORK['steps'])
    } for d in decisions])

@app.route('/api/resume_decision/<int:decision_id>', methods=['GET'])
@login_required
def resume_decision(decision_id):
    decision = Decision.query.get(decision_id)
    if not decision or decision.user_id != current_user.id:
        return jsonify({'error': 'Decision not found'}), 404
    
    current_step = PERSONAL_DECISION_FRAMEWORK['steps'][decision.current_step]
    return jsonify({
        'decision_id': decision.id,
        'current_step': current_step,
        'question': decision.question,
        'framework': decision.framework,
        'data': decision.data
    })

@app.route('/api/delete_decision/<int:decision_id>', methods=['DELETE'])
@login_required
def delete_decision(decision_id):
    decision = Decision.query.get(decision_id)
    if not decision or decision.user_id != current_user.id:
        return jsonify({'error': 'Decision not found'}), 404
    
    db.session.delete(decision)
    db.session.commit()
    return jsonify({'message': 'Decision deleted successfully'})

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
        
        response_text = response.content[0].text
        
        def balance_json(json_string):
            stack = []
            in_string = False
            escape = False
            for i, char in enumerate(json_string):
                if char == '"' and not escape:
                    in_string = not in_string
                elif not in_string:
                    if char in '{[':
                        stack.append(char)
                    elif char in '}]':
                        if stack and ((stack[-1] == '{' and char == '}') or (stack[-1] == '[' and char == ']')):
                            stack.pop()
                        else:
                            # Mismatched closing bracket, JSON is malformed
                            return None
                
                escape = char == '\\' and not escape
            
            # Close any unclosed strings
            if in_string:
                json_string += '"'
            
            # Add closing brackets in reverse order
            closing = ''.join('}' if c == '{' else ']' for c in reversed(stack))
            return json_string + closing

        # Try to parse the original response
        try:
            return json.loads(response_text)
        except JSONDecodeError:
            # If parsing fails, try to balance and parse again
            balanced_json = balance_json(response_text)
            if balanced_json is not None:
                try:
                    return json.loads(balanced_json)
                except JSONDecodeError:
                    app.logger.error(f"Failed to parse JSON even after balancing. Response: {balanced_json}")
            else:
                app.logger.error(f"JSON structure is malformed. Response: {response_text}")
            
            # If it still fails, extract whatever we can
            suggestion = ""
            pre_filled_data = {}
            
            if '"suggestion":' in response_text:
                suggestion_parts = response_text.split('"suggestion":', 1)[1].split('"', 2)
                suggestion = suggestion_parts[1] if len(suggestion_parts) > 1 else ""
            
            if '"pre_filled_data":' in response_text:
                pre_filled_data_str = response_text.split('"pre_filled_data":', 1)[1]
                try:
                    pre_filled_data_balanced = balance_json(pre_filled_data_str)
                    if pre_filled_data_balanced is not None:
                        pre_filled_data = json.loads(pre_filled_data_balanced)
                except JSONDecodeError:
                    app.logger.error(f"Failed to parse pre_filled_data. Extraction attempt: {pre_filled_data_str}")
            
            return {"suggestion": suggestion, "pre_filled_data": pre_filled_data}
        
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
            max_tokens=4000,
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

    