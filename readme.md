# AI Decision Maker

An AI-powered web application to assist in decision-making processes using the Anthropic Claude API.

## Features

- Utilizes Anthropic's Claude AI for decision-making assistance
- Supports multiple decision-making frameworks (Personal, Business, Ethical)
- Simple and intuitive web interface

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/ai-decision-maker.git
   cd ai-decision-maker
   ```

2. Set up a virtual environment:
   ```
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

4. Set up your environment variables:
   - Create a `.env` file in the project root
   - Add your Anthropic API key: `ANTHROPIC_API_KEY=your_api_key_here`

5. Run the application:
   ```
   python app.py
   ```

6. Open a web browser and navigate to `http://localhost:5000`

## Usage

1. Enter your decision question in the input field
2. Select the type of decision (Personal, Business, or Ethical)
3. Click "Get AI Suggestion" to receive advice

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License.