#!/bin/bash
set -euo pipefail

SESSION_NAME="champion"

if [[ ! -f .env ]]; then
  echo ".env file not found."
  exit 1
fi

if tmux has-session -t $SESSION_NAME 2>/dev/null; then
  echo "Session '$SESSION_NAME' already exists. Attaching..."
  tmux attach-session -t $SESSION_NAME
  exit 0
fi

tmux new-session -d -s $SESSION_NAME
tmux rename-window -t $SESSION_NAME:0 "Database"
tmux send-keys -t $SESSION_NAME:0 "make db" C-m
tmux new-window -t $SESSION_NAME -n "Backend"
tmux send-keys -t $SESSION_NAME:1 "make dev-back" C-m
tmux new-window -t $SESSION_NAME -n "Frontend"
tmux send-keys -t $SESSION_NAME:2 "make dev-front" C-m

tmux attach-session -t $SESSION_NAME
