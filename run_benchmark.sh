#!/usr/bin/env bash
set -euo pipefail

TASK_TEMPLATE='Use the marimo-pair skill here. Discover running sessions. Edit the notebook "NOTEBOOK_NAME". Read data/ired-novartis/cs1c02786_si_002.csv, identify the single point mutations, and plot me a heatmap of x-axis position, y-axis mutant letter, and heatmap value taken from the '\''mean'\'' column. When done, rank order the positions by average value of the '\''mean'\'' column, then rank order the positions by top value of the '\''mean'\'' column, and plot me an UpSet plot of the top 20 for each to visualize the set overlaps. Finally, write in for me a recommendation for what positions we should be mutating.'

MODELS="glm-analysis.py:openrouter/z-ai/glm-5.1
opus-analysis.py:openrouter/anthropic/claude-opus-4.6
sonnet-analysis.py:openrouter/anthropic/claude-sonnet-4.6
minimax-analysis.py:openrouter/minimax/minimax-m2.7
kimi-analysis.py:openrouter/moonshotai/kimi-k2.5
gemma-analysis.py:openrouter/google/gemma-4-31b-it
qwen-coder-analysis.py:openrouter/qwen/qwen3-coder"

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
LOGDIR="$REPO_DIR/logs"
TRANSCRIPTDIR="$REPO_DIR/transcripts"
mkdir -p "$LOGDIR" "$TRANSCRIPTDIR"

run_and_export() {
  local notebook="$1"
  local model="$2"
  local task="${TASK_TEMPLATE//NOTEBOOK_NAME/$notebook}"
  local name="$(basename "$notebook" .py)"
  local logfile="$LOGDIR/${name}.log"
  local jsonfile="$TRANSCRIPTDIR/${name}.json"
  local mdfile="$TRANSCRIPTDIR/${name}.md"

  echo "=== Starting $model on $notebook ==="
  opencode run -m "$model" --format json --dir "$REPO_DIR" --title "Benchmark: $model" -- "$task" > "$logfile" 2>&1
  local exit_code=$?

  local session_id
  session_id=$(grep -m1 -o '"sessionID":"[^"]*"' "$logfile" | head -1 | cut -d'"' -f4)

  if [ -n "$session_id" ]; then
    opencode export "$session_id" > "$jsonfile" 2>/dev/null || true
    if [ -f "$jsonfile" ] && command -v python3 &>/dev/null; then
      python3 "$REPO_DIR/export_to_md.py" "$jsonfile" > "$mdfile" 2>/dev/null || true
    fi
    echo "=== Finished $model (session: $session_id, exit: $exit_code) ==="
  else
    echo "=== Finished $model (no session ID found, exit: $exit_code) ==="
  fi

  return $exit_code
}

pids=()
names=()

while IFS=: read -r notebook model; do
  run_and_export "$notebook" "$model" &
  pids+=($!)
  names+=("$model")
done <<< "$MODELS"

echo "=== All ${#pids[@]} models launched in parallel ==="
echo "=== Waiting for completion... ==="

fail=0
for i in "${!pids[@]}"; do
  if ! wait "${pids[$i]}"; then
    echo "FAILED: ${names[$i]} (pid ${pids[$i]})"
    fail=$((fail + 1))
  fi
done

echo
echo "=== All benchmarks complete ($fail failures) ==="
echo "Logs: $LOGDIR/"
echo "Transcripts: $TRANSCRIPTDIR/"
