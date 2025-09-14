#!/bin/bash
# Wrapper script to simplify usage

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

show_help() {
    echo -e "${BLUE}Automated Assessment System with LLMs${NC}"
    echo ""
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  setup                    Configure initial environment"
    echo "  prepare <zip_file>       Unzip and rename files"
    echo "  eval <folder>            Evaluate submissions using the LLM"
    echo "  monitor                  Monitor progress in real time"
    echo "  email                    Send feedback via email"
    echo "  rename <folder>          Only rename folders (skip extraction)"
    echo ""
    echo "Options:"
    echo "  -h, --help     Show this help message"
    echo "  -c, --config   Use custom configuration file"
    echo "  -v, --verbose  Enable verbose mode"
    echo ""
    echo "Examples:"
    echo "  $0 setup"
    echo "  $0 prepare submissions.zip"
    echo "  $0 rename submissions/"
    echo "  $0 eval submissions/"
    echo "  $0 monitor"
    echo ""
    echo "Note: The prepare command will automatically create a 'submissions' folder"
}

# Function to check if required scripts exist
check_scripts() {
    local missing_scripts=()
    
    if [ ! -f "./setup.sh" ]; then
        missing_scripts+=("setup.sh")
    fi
    
    if [ ! -f "./rename_folders.sh" ]; then
        missing_scripts+=("rename_folders.sh")
    fi
    
    if [ ! -f "./eval.py" ]; then
        missing_scripts+=("eval.py")
    fi
    
    if [ ! -f "./monitor.py" ]; then
        missing_scripts+=("monitor.py")
    fi
    
    if [ ! -f "./send_email.py" ]; then
        missing_scripts+=("send_email.py")
    fi
    
    if [ ${#missing_scripts[@]} -gt 0 ]; then
        echo -e "${RED}❌ Missing required scripts:${NC}"
        for script in "${missing_scripts[@]}"; do
            echo -e "   - $script"
        done
        echo -e "${YELLOW}Please ensure all required scripts are in the current directory${NC}"
        return 1
    fi
    
    return 0
}

case "$1" in
    "setup")
        echo -e "${BLUE}🚀 Setting up environment...${NC}"
        if [ -f "./setup.sh" ]; then
            chmod +x setup.sh
            ./setup.sh
        else
            echo -e "${RED}❌ setup.sh not found${NC}"
            exit 1
        fi
        ;;
    "prepare")
        if [ -z "$2" ]; then
            echo -e "${RED}❌ Please specify the zip file to extract${NC}"
            echo "Usage: $0 prepare <zip_file>"
            exit 1
        fi
        
        if [ ! -f "$2" ]; then
            echo -e "${RED}❌ File '$2' not found${NC}"
            exit 1
        fi
        
        echo -e "${BLUE}🚀 Extracting and renaming files...${NC}"
        
        # Create submissions directory if it doesn't exist
        if [ ! -d "submissions" ]; then
            mkdir -p submissions
            echo -e "${GREEN}✅ Created submissions directory${NC}"
        fi
        
        # Extract files
        echo -e "${YELLOW}📦 Extracting '$2'...${NC}"
        if unzip -q "$2" -d submissions/; then
            echo -e "${GREEN}✅ Files extracted successfully${NC}"

            # --- NEW CODE BLOCK STARTS HERE ---
            # Get the zip file name without the .zip extension
            BASENAME=$(basename "$2" .zip)
            SOURCE_DIR="submissions/$BASENAME"

            # Check if extraction created a subfolder (default behavior)
            if [ -d "$SOURCE_DIR" ]; then
                echo -e "${YELLOW}📂 Subfolder '$BASENAME' found. Moving contents...${NC}"
                # Move all contents from the subfolder to the 'submissions' directory
                mv "$SOURCE_DIR"/* submissions/
                # Remove the now empty subfolder
                rmdir "$SOURCE_DIR"
                echo -e "${GREEN}✅ Contents moved and empty folder removed.${NC}"
            fi
            # --- END OF NEW CODE BLOCK ---
        else
            echo -e "${RED}❌ Failed to extract '$2'${NC}"
            exit 1
        fi
        
        # Rename folders
        if [ -f "./rename_folders.sh" ]; then
            chmod +x rename_folders.sh
            echo -e "${YELLOW}🏷️  Renaming folders...${NC}"
            ./rename_folders.sh submissions/
        else
            echo -e "${RED}❌ rename_folders.sh not found${NC}"
            exit 1
        fi
        ;;
    "rename")
        if [ -z "$2" ]; then
            echo -e "${RED}❌ Please specify the submissions folder${NC}"
            echo "Usage: $0 rename <folder>"
            exit 1
        fi
        
        if [ ! -d "$2" ]; then
            echo -e "${RED}❌ Directory '$2' not found${NC}"
            exit 1
        fi
        
        echo -e "${BLUE}🏷️  Renaming folders only...${NC}"
        if [ -f "./rename_folders.sh" ]; then
            chmod +x rename_folders.sh
            ./rename_folders.sh "$2"
        else
            echo -e "${RED}❌ rename_folders.sh not found${NC}"
            exit 1
        fi
        ;;
    "eval")
        if [ -z "$2" ]; then
            echo -e "${RED}❌ Please specify the submissions folder${NC}"
            echo "Usage: $0 eval <folder>"
            exit 1
        fi
        
        if [ ! -d "$2" ]; then
            echo -e "${RED}❌ Directory '$2' not found${NC}"
            exit 1
        fi
        
        echo -e "${BLUE}🤖 Evaluating submissions...${NC}"
        if [ -f "./eval.py" ]; then
            python3 eval.py "$2" "${@:3}"
        else
            echo -e "${RED}❌ eval.py not found${NC}"
            exit 1
        fi
        ;;
    "monitor")
        echo -e "${BLUE}📊 Starting monitor...${NC}"
        if [ -f "./monitor.py" ]; then
            python3 monitor.py
        else
            echo -e "${RED}❌ monitor.py not found${NC}"
            exit 1
        fi
        ;;
    "email")
        echo -e "${BLUE}📧 Sending emails...${NC}"
        if [ -f "./send_email.py" ]; then
            python3 send_email.py "${@:2}"
        else
            echo -e "${RED}❌ send_email.py not found${NC}"
            exit 1
        fi
        ;;
    "check")
        echo -e "${BLUE}🔍 Checking required scripts...${NC}"
        if check_scripts; then
            echo -e "${GREEN}✅ All required scripts are present${NC}"
        else
            exit 1
        fi
        ;;
    "-h"|"--help"|"help"|"")
        show_help
        ;;
    *)
        echo -e "${RED}❌ Invalid command: $1${NC}"
        echo ""
        show_help
        exit 1
        ;;
esac

echo -e "${GREEN}✅ Command completed!${NC}"
