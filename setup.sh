#!/bin/bash
# Initial setup for the automated assessment environment with virtual environment

echo "🚀 Setting up the assessment environment..."

# Create directory structure
mkdir -p {submissions,output,logs,config}

# Function to check dependencies
check_dependency() {
    if ! command -v $1 &> /dev/null; then
        echo "❌ $1 not found. Installing..."
        return 1
    else
        echo "✅ $1 found"
        return 0
    fi
}

# Check and install system dependencies
check_dependency "jq" || sudo apt-get install -y jq
check_dependency "curl" || sudo apt-get install -y curl
check_dependency "python3" || sudo apt-get install -y python3
check_dependency "pip3" || sudo apt-get install -y python3-pip

# Create Python virtual environment
echo "🐍 Creating Python virtual environment (.venv)..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    echo "✅ Virtual environment created"
else
    echo "⚠️  Virtual environment already exists"
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source .venv/bin/activate

# Verify activation
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo "✅ Virtual environment activated: $VIRTUAL_ENV"
else
    echo "❌ Failed to activate virtual environment"
    exit 1
fi

# Upgrade pip in virtual environment
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Create the requirements.txt file with the frozen dependencies
echo "📄 Creating requirements.txt file..."
cat > requirements.txt << EOF
aiohappyeyeballs==2.6.1
aiohttp==3.12.15
aiosignal==1.4.0
async-timeout==5.0.1
attrs==25.3.0
et_xmlfile==2.0.0
frozenlist==1.7.0
idna==3.10
multidict==6.6.4
numpy==2.0.2
openpyxl==3.1.5
pandas==2.3.2
propcache==0.3.2
python-dateutil==2.9.0.post0
python-dotenv==1.1.1
pytz==2025.2
PyYAML==6.0.2
scipy==1.13.1
six==1.17.0
typing_extensions==4.15.0
tzdata==2025.2
yarl==1.20.1
EOF

# Install Python dependencies from the requirements file
echo "📦 Installing Python dependencies from requirements.txt..."
pip install -r requirements.txt

# Verify installation
echo "🔍 Verifying key packages installation..."
python3 -c "import aiohttp, pandas, numpy, yaml, dotenv; print('✅ All key packages imported successfully')" || echo "❌ Package import failed"

# Create template configuration file
echo "⚙️ Creating template configuration file..."
cat > config/config.env << EOF
# API configuration
API_PROVIDER=groq
API_KEY=your_api_key_here
API_URL=https://api.groq.com/openai/v1/chat/completions

# Email configuration
EMAIL_SERVER=smtp.example.com
EMAIL_PORT=587
EMAIL_USER=your_email@example.com
EMAIL_PASS=your_email_password

# General settings
MAX_RETRIES=3
TIMEOUT_SECONDS=30
PARALLEL_JOBS=5
LOG_LEVEL=INFO
EOF

# Create .gitignore if it doesn't exist
if [ ! -f ".gitignore" ]; then
    echo "📝 Creating .gitignore file..."
    cat > .gitignore << EOF
# Virtual environment
.venv/
venv/

# Output files
output/
logs/

# Configuration with sensitive data
config/config.env

# Python
__pycache__/
*.pyc
*.pyo
*.egg-info/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db
EOF
fi

echo ""
echo "✅ Setup completed successfully!"
echo ""
echo "📋 Next steps:"
echo "   1. Edit config/config.env and add your API_KEY"
echo "   2. (Optional) Edit other configs in:"
echo "      - config/config.yaml"
echo "   3. To activate the environment manually: source .venv/bin/activate"
echo "      To deactivate: deactivate"
echo "   4. To test the setup:"
echo "      - ./run.sh eval submissions"
echo "   5. For your classes:"
echo "      - Download the submissions from Moodle as a zip file"
echo "      - ./run.sh prepare your.zip"
echo "      - ./run.sh eval submissions"
echo ""
echo "🔍 Environment info:"
echo "   📁 Virtual environment: .venv/"
echo "   📦 Packages installed: $(pip list --format=freeze | wc -l) packages"
echo "   🐍 Python path: $(which python)"
echo ""
