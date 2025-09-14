#!/bin/bash
# Initial setup for the automated assessment environment

echo "🚀 Setting up the assessment environment..."

# Create directory structure (CORRECTED LINE)
mkdir -p {submissions,rubrics,output,logs,config}

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

# Check and install dependencies
check_dependency "jq" || sudo apt-get install -y jq
check_dependency "curl" || sudo apt-get install -y curl
check_dependency "python3" || sudo apt-get install -y python3
check_dependency "pip3" || sudo apt-get install -y python3-pip

# Install Python dependencies
pip3 install python-dotenv pandas openpyxl

# Create template configuration file
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

echo "✅ Setup completed successfully!"