# Work with SAFE-EVAL on GitHub

The working repository is [Apple32452/safe-eval](https://github.com/Apple32452/safe-eval).

## Clone it onto your Mac

Run these lines one at a time in the VS Code terminal:

```bash
cd ~/Downloads
git clone https://github.com/Apple32452/safe-eval.git
cd safe-eval
python -m pip install -r requirements.txt
python scripts/check_release.py
python -m unittest discover -s experiments/stage7 -p 'test_*.py' -v
```

Use your existing activated Python environment. If you already cloned this
repository, open that folder and use `git pull` rather than cloning it again.

## Run the fixed experiment

From the repository root:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python experiments/stage7/run_stage7.py --repeats 100 --workers 2 --output results/stage7_local
python experiments/stage7/analyze_stage7.py --input results/stage7_local
```

Wait for the experiment to finish before starting the analyzer. Research runs
execute in your terminal. GitHub tracks the source and documentation; Actions
runs the configured automated checks.

## Continue development

For a new experiment, create a branch, preserve the released Stage 7 directory,
add the new stage and its protocol, run the checks, and commit the changes:

```bash
git switch -c research/new-stage
```

After making and checking your changes:

```bash
git add .
git commit -m "Describe the research change"
git push -u origin research/new-stage
```

Open a pull request on GitHub to review the code and evidence before merging.
Use your own existing Git authentication and commit identity.

The Python environment and generated local runs are excluded from commits.
The compact released reference tables, figures and public data remain included.
