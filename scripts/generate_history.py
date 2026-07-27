import os
import sys
import subprocess
import datetime
import random
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
# Put the history repository in a scratch folder
REPO_DIR = os.path.join(HERE, "..", "..", "contribution-history")
REPO_DIR = os.path.abspath(REPO_DIR)

# Clear existing repo dir if it exists to start fresh
if os.path.exists(REPO_DIR):
    shutil.rmtree(REPO_DIR)

os.makedirs(REPO_DIR, exist_ok=True)

# Run git commands in the repo directory with backdated env variables
def run_git(args, env=None):
    current_env = os.environ.copy()
    if env:
        current_env.update(env)
    res = subprocess.run(["git"] + args, cwd=REPO_DIR, env=current_env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        print(f"Git command failed: git {' '.join(args)}", file=sys.stderr)
        print(f"Stderr: {res.stderr}", file=sys.stderr)
        sys.exit(1)
    return res.stdout

# Initialize repo
print("Initializing local history repository...")
run_git(["init"])
run_git(["checkout", "-b", "main"])
run_git(["config", "user.name", "RaghavParasher"])
run_git(["config", "user.email", "raghavparashar905@gmail.com"])

# Generate dates for the last 365 days
end_date = datetime.date.today()
start_date = end_date - datetime.timedelta(days=365)

current_date = start_date
total_commits = 0

print("Generating backdated commit history...")
while current_date <= end_date:
    is_weekend = current_date.weekday() in (5, 6)
    
    # Weekdays: 78% active with 1-6 commits
    # Weekends: 22% active with 1-3 commits
    roll = random.random()
    if is_weekend:
        num_commits = random.randint(1, 3) if roll < 0.22 else 0
    else:
        num_commits = random.randint(1, 6) if roll < 0.78 else 0
        
    for i in range(num_commits):
        # Generate random time during the day (9am to 9pm)
        hour = random.randint(9, 21)
        minute = random.randint(0, 59)
        second = random.randint(0, 59)
        
        # Git expects ISO 8601 or similar formats for date env variables
        commit_time = f"{current_date.isoformat()}T{hour:02d}:{minute:02d}:{second:02d}"
        
        # Append change to a dummy file to create unique commit content
        file_path = os.path.join(REPO_DIR, "art.txt")
        with open(file_path, "a") as f:
            f.write(f"Contribution on {commit_time}\n")
            
        run_git(["add", "art.txt"])
        
        env = {
            "GIT_AUTHOR_DATE": commit_time,
            "GIT_COMMITTER_DATE": commit_time
        }
        run_git(["commit", "-m", f"update on {current_date.isoformat()}"], env=env)
        total_commits += 1
        
    current_date += datetime.timedelta(days=1)

print(f"Generated {total_commits} commits in total.")

# Add remote and push to the private contribution-art repository
REMOTE_URL = "https://github.com/RaghavParasher/contribution-art.git"
print(f"Setting remote to {REMOTE_URL}...")
run_git(["remote", "add", "origin", REMOTE_URL])
print("Force-pushing history to main branch...")
run_git(["push", "-u", "origin", "main", "-f"])
print("Successfully pushed to GitHub! Please wait 5-10 minutes for the contribution grid to update.")
