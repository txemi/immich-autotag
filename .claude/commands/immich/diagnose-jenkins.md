Fetch and diagnose the latest Jenkins build for a branch of the immich-autotag pipeline.

## Credentials

Use the environment variables set in `.claude/settings.local.json`:
- `JENKINS_URL`, `JENKINS_USER`, `JENKINS_TOKEN`, `JENKINS_JOB`

## Steps

1. Determine the target branch:
   - If the user passed a branch name as argument, use it (URL-encode `/` as `%2F`).
   - Otherwise use the current git branch: `git branch --show-current`

2. Fetch the last build result and number:
   ```bash
   curl -s -u "$JENKINS_USER:$JENKINS_TOKEN" \
     "$JENKINS_URL/job/$JENKINS_JOB/job/<branch-encoded>/lastBuild/api/json" \
     | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['number'], d['result'], d['url'])"
   ```

3. Fetch the console log:
   ```bash
   curl -s -u "$JENKINS_USER:$JENKINS_TOKEN" \
     "$JENKINS_URL/job/$JENKINS_JOB/job/<branch-encoded>/lastBuild/consoleText"
   ```

4. Diagnose and report:
   - If **FAILURE**: identify the root cause (first ERROR line or exception), ignore stack traces unless the cause is unclear. Give a one-paragraph diagnosis and a suggested fix.
   - If **SUCCESS**: confirm it passed and list the stages that ran.
   - If the build is still **running**: say so and offer to check again.

5. Include the direct Jenkins URL to the build for the user to open if needed.
