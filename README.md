# TestCode.ai – Automated Assessment System with LLMs

Welcome to **TestCode.ai**, a free and open-source platform designed to support automated exam grading with the assistance of **Large Language Models (LLMs)**.

Its main feature is its high flexibility through a central configuration file (config.yaml). This allows the user to define detailed evaluation rubrics and customize the prompts sent to a Large Language Model (LLM). Additionally, the system integrates the anonymization of submissions, automatic AI-based evaluation, and feedback delivery by email.

---

## 🚀 Features
- **Setup** of a complete evaluation environment.
- **Preparation of submissions** from Moodle `.zip` files (unzip + anonymization).
- **Automated evaluation** of programming tasks using LLMs.
- **Automatic feedback delivery** via email.
- **Mapping file** generation for anonymized student folders.

---

## 📦 Installation
Clone the repository and make the wrapper script executable:

```bash
git clone https://github.com/fzampirolli/TestCode.ai.git
cd TestCode.ai
chmod +x run.sh
````

---

## ⚡ Usage

Run the wrapper script with one of the available commands:

```bash
./run.sh [COMMAND] [OPTIONS]
```

### Main Commands

* `setup`
  Sets up the initial environment (run once).

  ```bash
  ./run.sh setup
  ```

* `prepare <zip_file>`
  Unzips and anonymizes submissions from Moodle.
  The mapping file is saved in `output/mapping.txt`.

* `eval <folder>`
  Runs the AI evaluation on the submissions folder.
  Example:

  ```bash
  ./run.sh eval submissions
  ```

* `email`
  Sends the generated feedback to students via email.

* `check`
  Verifies whether all required scripts are available
  (`setup.sh`, `eval.py`, `send_email.py`, `rename_folders.sh`).

* `-h, --help`
  Displays the help message.

---

## 🔄 Example Workflow

```bash
./run.sh setup
./run.sh prepare submissions.zip
./run.sh eval submissions
./run.sh email
```

---

## 📂 Project Structure

```
TestCode.ai/
├── run.sh               # Main wrapper script
├── setup.sh             # Environment setup script
├── eval.py              # AI evaluation logic
├── send_email.py        # Email feedback sender
├── config/              # Folder with .env and .yaml
├── submissions/         # Student submissions (after prepare)
├── output/              # Generated feedback and mapping
└── logs/                # Execution logs
```

---

## 📜 License

This project is licensed under the **MIT License**.
You are free to use, modify, and distribute this software, provided that the original copyright
and license notice are included in all copies or substantial portions of the software.

See the [LICENSE](LICENSE.txt) file for more details.
