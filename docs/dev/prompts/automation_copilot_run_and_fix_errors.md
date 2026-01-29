# Prompt for GitHub Copilot: Run and Fix Execution Errors

## Instructions for the Copilot Agent

1. Use the Visual Studio Code task configured to run the main application of the project.
2. Execute the application using this task.
3. Observe the output and detect any runtime errors or exceptions.
4. If any errors or exceptions occur, automatically fix them in the source code.
5. Rerun the application using the same VS Code task.
6. Repeat this process in a loop until the application runs without any execution errors or exceptions.
7. When the process is complete, notify that the application runs successfully with no execution errors.

## Notes
- Do not stop until the application runs completely error-free.
- Apply best practices for code quality and refactoring in each correction.
- Optionally, document the changes made in each iteration.

---

This prompt is designed for a LLM/Copilot agent to automate the process of running the application and fixing all execution errors using the configured Visual Studio Code task.