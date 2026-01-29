# Prompt for GitHub Copilot: Automated Execution and Quality Loop

## Instructions for the Copilot Agent

1. Run the main application of the project (choose the appropriate task or command to launch the app).
2. Observe the output and detect any errors or exceptions.
3. If there are errors, automatically fix them in the source code.
4. Repeat the process of execution and correction in a loop until the application runs without errors.
5. Once the app runs correctly, execute the Quality Gate in STANDARD mode.
6. If the Quality Gate STANDARD detects errors, automatically fix them and rerun the Quality Gate STANDARD.
7. Repeat the cycle until the Quality Gate STANDARD passes without errors.
8. Next, execute the Quality Gate in TARGET mode.
9. If the Quality Gate TARGET detects errors, automatically fix them and rerun the Quality Gate TARGET.
10. Repeat the cycle until the Quality Gate TARGET passes without errors.
11. Finish the process and notify that the project is free of execution and quality errors.

## Notes
- Do not stop the process until all steps are completely error-free.
- Apply best practices for refactoring and code quality in each correction.
- Briefly document the changes made in each iteration if possible.

---

This prompt is designed for a LLM/Copilot agent to automate the continuous correction and improvement of the project following an execution and quality validation loop.