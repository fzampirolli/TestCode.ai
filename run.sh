#!/bin/bash
# Simplified wrapper script for the assessment system

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Displays the help message with the simplified commands
show_help() {
    echo -e "${BLUE}Automated Assessment System with LLMs${NC}"
    echo ""
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Main Commands:"
    echo "  setup                - Sets up the initial environment (run once)"
    echo "  prepare <zip_file>   - Unzips and renames submissions"
    echo "  eval <folder>        - Runs the AI evaluation on the submissions folder"
    echo "  email                - Sends the feedback via email"
    echo "  check                - Checks if the required scripts exist"
    echo "  clean                - Removes submissions, output and logs folders"
    echo ""
    echo "Options:"
    echo "  -h, --help     Shows this help message"
    echo ""
    echo "Example workflow:"
    echo "  1. $0 setup"
    echo "  2. $0 prepare submissions.zip"
    echo "  3. $0 eval submissions"
    echo "  4. $0 email"
}

# Checks for essential scripts
check_scripts() {
    local missing_scripts=()
    local required_scripts=("setup.sh" "eval.py" "send_email.py")

    for script in "${required_scripts[@]}"; do
        if [ ! -f "./$script" ]; then
            missing_scripts+=("$script")
        fi
    done
    
    if [ ${#missing_scripts[@]} -gt 0 ]; then
        echo -e "${RED}❌ Missing essential scripts:${NC}"
        for script in "${missing_scripts[@]}"; do
            echo -e "   - $script"
        done
        return 1
    fi
    return 0
}

# --- MAIN COMMAND LOGIC ---
case "$1" in
    "setup")
        echo -e "${BLUE}🚀 Setting up the environment...${NC}"
        [ -f "./setup.sh" ] && chmod +x ./setup.sh && ./setup.sh || echo -e "${RED}❌ setup.sh not found.${NC}"
        ;;

    "prepare")
        if [ -z "$2" ]; then
            echo -e "${RED}❌ Please specify the .zip file${NC}" && exit 1
        fi
        if [ ! -f "$2" ]; then
            echo -e "${RED}❌ File '$2' not found.${NC}" && exit 1
        fi

        echo -e "${BLUE}🚀 Preparing submissions...${NC}"
        SUBMISSIONS_DIR="submissions"

        # Limpa pasta para evitar duplicação ao rodar mais de uma vez
        rm -rf "$SUBMISSIONS_DIR"
        mkdir -p "$SUBMISSIONS_DIR"

        echo -e "${YELLOW}📦 Unpacking '$2'...${NC}"
        if ! unzip -q "$2" -d "$SUBMISSIONS_DIR/"; then
            echo -e "${RED}❌ Failed to unpack the file.${NC}" && exit 1
        fi
        
        # Caso Moodle crie subpasta com o nome do zip
        BASENAME=$(basename "$2" .zip)
        SOURCE_DIR="$SUBMISSIONS_DIR/$BASENAME"
        if [ -d "$SOURCE_DIR" ]; then
            echo -e "${YELLOW}📂 Moving files from subfolder '$BASENAME'...${NC}"
            mv "$SOURCE_DIR"/* "$SUBMISSIONS_DIR/" && rmdir "$SOURCE_DIR"
        fi

        echo -e "${YELLOW}🏷️  Renaming folders...${NC}"
        MAP_FILE="output/mapping.txt"
        mkdir -p output
        > "$MAP_FILE"

        index=0
        find "$SUBMISSIONS_DIR" -mindepth 1 -maxdepth 1 -type d | while read -r dir_path; do
            original_name=$(basename "$dir_path")

            # Se já estiver no formato "Nome Sobrenome - user", pula
            if [[ "$original_name" == *" - "* ]]; then
                echo "Skipping already renamed: $original_name"
                continue
            fi

            IFS=' ' read -ra partes <<< "$original_name"
            num_partes=${#partes[@]}
            if (( num_partes < 4 )); then
                echo "Skipping invalid folder: $original_name"
                continue
            fi

            usuario="${partes[$((num_partes-1))]}"
            ra="${partes[$((num_partes-2))]}"
            primeiro_nome="${partes[$((num_partes-3))]}"

            restante_nome=""
            for ((i=0; i<num_partes-3; i++)); do
                restante_nome+="${partes[$i]} "
            done
            restante_nome=$(echo "$restante_nome" | sed 's/ *$//')

            novo_nome="${primeiro_nome} ${restante_nome} - ${usuario}"

            mv "$dir_path" "$SUBMISSIONS_DIR/$novo_nome"
            echo "'$original_name' -> '$novo_nome'" >> "$MAP_FILE"
            ((index++))
        done
        echo -e "${GREEN}✅ Folders renamed. See '$MAP_FILE' for reference.${NC}"
        ;;

    "eval")
        if [ -z "$2" ]; then
            echo -e "${RED}❌ Please specify the submissions folder${NC}" && exit 1
        fi
        echo -e "${BLUE}🤖 Running AI evaluation...${NC}"
        [ -f "./eval.py" ] && python3 eval.py "$2" "${@:3}" || echo -e "${RED}❌ eval.py not found.${NC}"
        ;;

    "email")
        echo -e "${BLUE}📧 Sending feedback emails...${NC}"
        [ -f "./send_email.py" ] && python3 send_email.py "${@:2}" || echo -e "${RED}❌ send_email.py not found.${NC}"
        ;;

    "check")
        echo -e "${BLUE}🔍 Checking scripts...${NC}"
        check_scripts
        ;;

    "clean")
        echo -e "${BLUE}🧹 Cleaning environment...${NC}"
        rm -rf submissions output logs
        echo -e "${GREEN}✅ Environment cleaned (submissions, output, logs).${NC}"
        ;;

    "-h"|"--help"|"help"|"")
        show_help
        ;;

    *)
        echo -e "${RED}❌ Invalid command: $1${NC}"
        show_help
        exit 1
        ;;
esac

echo -e "${GREEN}✅ Command '$1' completed!${NC}"
