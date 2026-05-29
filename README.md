# Agent Utils
A collection of skills for the Aria/Backline AI agents to use. These are installed as globally executable CLI scripts in the given server running the AI agent. 

## Installation

```bash
mkdir agent-utils
cd agent-utils
git clone THISREPO .
```

Copy/modify the .env into each folder
Run a script to test it.

```bash
cd agent-utils/kanboard
python3 kanboard.py overdue
```

Make script global
This is needed per script. AI can do it quickly for you. 
```bash
# 1. Make sure it's executable
chmod +x ~/agent-utils/kanboard/kanboard.py

# 2. Create ~/bin and symlink
mkdir -p ~/bin
ln -s ~/agent-utils/kanboard/kanboard.py ~/bin/kanboard

# 3. Add ~/bin to PATH in ~/.bashrc
echo 'export PATH="$PATH:$HOME/bin"' >> ~/.bashrc

# 4. Reload your shell
source ~/.bashrc
```