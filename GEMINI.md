# General rules

## Allowed extra files
- You can read .agent/ folder even when it is .gitignored. That is where you make changes before user approves them in project.

## Ignored files
- .env
- .databricks
- .venv
- dist
- *.egg-info

## Safety
- Never modify project files directly without approval.
- Don't read .env files under any circumstances
- Never commit or stage files. The user will handle that.

## Code style
- Simple code over clever code. Follow the KISS principle, keep it simple, stupid.  
- If changes are required in existing code, make absolute minimal changes possible to accomplish the task  
- Follow the pylint rules that are not excluded in .pylintrc
- Prefer early return in functions

## Workflow
1. When user asks to make changes, propose changes in `.agent/proposals/`. Use filenames that the project uses, the imports related and only the funtions that are effected in that proposal, so that the user can read changes faster.
2. Wait for approval and after user has approved, you can move changes to their right places in the project  
3. After user approves new features or changes, and you add the changes to project remove the proposal from .agent/proposals folder to keep it clean.
