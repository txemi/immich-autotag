// ==================== CONFIG FLAGS ====================
def ENABLE_JENKINS_TAGGING = true // Set to true to enable GitHub tagging
// Auto-chain: on success the build re-triggers itself, so the batch keeps walking the library
// without anyone pressing a button. It belongs ONLY to the operational branch: on any other
// branch it would spin a second infinite loop competing for the SAME single agent
// (the one carrying the `immich-batch` label), where each run can take hours. main is
// for validating, not for processing the library.
def ENABLE_AUTO_CHAIN = (env.BRANCH_NAME == 'ops/batch-processing')
                                  // (keeps the batch-processing chain self-perpetuating
                                  // without external dispatch). Failure stops the chain
                                  // by design — re-enable manually after investigating.

// Helper for tagging (debe estar fuera del pipeline)
def tagBuild(String type) {
    def tagName = "jenkins-${type}-${env.BUILD_NUMBER ?: 'manual'}-${env.GIT_COMMIT ?: 'manual'}"
    echo "🏷️ Creando tag GitHub (${type}): ${tagName}"
    try {
        sh "git config user.name 'jenkins'"
        sh "git config user.email 'jenkins@localhost'"
        sh "git tag ${tagName}"
        withCredentials([usernamePassword(
            credentialsId: 'app_github_para_ubuntu20jenkins.ad3.lab',
            usernameVariable: 'GH_USER',
            passwordVariable: 'GH_TOKEN'
        )]) {
            sh "git remote set-url origin https://\${GH_USER}:\${GH_TOKEN}@github.com/txemi/immich-autotag.git"
            sh "git push origin ${tagName}"
        }
    } catch (e) {
        echo "⚠️ GitHub tagging failed (non-fatal): ${e.message}"
    }
}
pipeline {
    options {
        // Keep last 30 builds or 30 days, whichever is smaller. The previous
        // value of 4 was effectively bypassed because every SUCCESS build was
        // pinned via `currentBuild.keepLog = true` (now removed in the
        // success post-action below), so old builds never rotated and ate
        // tens of GB on the master.
        buildDiscarder(logRotator(numToKeepStr: '30', daysToKeepStr: '30'))
    }
    agent {
        docker {
            image 'python:3.11-slim'
            // Pin to the batch agent: the checkpoint chain (logs_local/) lives in that
            // node's workspace, and sequential single-node execution is required
            // (see issue 004-active-run-monitoring). Without a label the build can land
            // on the Windows agent (no docker) or the controller.
            //
            // The label is a PURPOSE, not a hostname. It used to say
            // 'ub20jenkins4ub20', which happens to work because Jenkins exposes every
            // node's own name as an implicit label -- but that is not a label anyone
            // declared: this controller only defines two, `linux` and `windows`. Binding
            // the pipeline to a machine name means renaming or replacing that machine
            // requires a code change and a PR to a protected branch, and it silently
            // bypasses the label scheme.
            //
            // `immich-batch` is declared on the node in Jenkins (2026-08-10). Moving the
            // batch to another machine is now a checkbox there, not a commit here. NOTE:
            // it is deliberately assigned to ONE node -- until the checkpoint stops
            // living in a node's workspace, a second node would reprocess from zero.
            label 'immich-batch'
            // Mounts ~/.ssh from host into the container as read-only for private key and known_hosts access
            // Ensure $HOME/.ssh exists and contains the required key and known_hosts files
            //
            // ⚠️ Do NOT mount the AGENT's `$HOME/.cache` into `/root/.cache`.
            //
            // This container runs with `--user root` (it needs to: the mounts below land under
            // `/root/...`, which is mode 700, so a non-root uid could not even traverse it).
            // Inside the container `HOME=/root`, so `-v $HOME/.cache:/root/.cache` was really the
            // AGENT's `~/.cache`, mounted read-write and written as uid 0. Hundreds of root-owned
            // files ended up in the agent's `uv` cache, which from then on it could READ but not
            // UPDATE.
            //
            // The damage lands on OTHER jobs of the same node, and hours later, which is what
            // makes it expensive to diagnose:
            //   · they stay green for as long as `uv` can serve the cache as-is;
            //   · for a TAG, `uv` resolves tag -> SHA through GitHub's API fast path, and that
            //     anonymous bucket is 60/h per public IP, shared by every machine behind the same
            //     NAT. When it runs out, `uv` does a real `git fetch`, needs to WRITE, and fails
            //     with `Git operation failed`;
            //   · the darnlink recipe surfaces that as "bad ref / no network" -- pointing at two
            //     things that are perfectly fine.
            // Measured 2026-08-11: 327 root-owned files, and a link gate on a sibling job of the
            // same node going red 11 minutes later.
            //
            // ⚠️ The writer was the `ops/batch-processing` branch, which carries its OWN copy of
            // this file and re-triggers itself every few hours. Merging this to `main` does NOT
            // stop it: the change has to reach that branch too.
            //
            // The cache now belongs to the CONTAINER: it dies with it and touches nobody's home.
            //
            // The trade, measured, is not the same for both tools:
            //   · pip lost NOTHING -- with the old mount it disabled its cache outright
            //     (`check_path_owner`: as euid 0 it refuses a dir owned by another uid; "The cache
            //     has been disabled" appears 6 times in the older build logs). Same 163 downloads
            //     before and after.
            //   · uv DID lose cross-build reuse: it has no such guard, so as root it happily wrote
            //     into the agent's `~/.cache/uv` -- which is where 323 of those 327 root-owned
            //     files came from. Each build now reclones and rebuilds its pinned tools.
            // That cost is small and it is the price of the fix, not a free lunch.
            //
            // NOT changed on purpose: `--user root`. Dropping it has its own risk (the mounts
            // above) and would still leave root-owned files in the WORKSPACE, which is a separate
            // decision. A root cron currently sweeps workspaces of DEAD branches only -- it does
            // not clean live ones, so that half is still open.
            args '-v $HOME/.config/immich_autotag:/root/.config/immich_autotag:ro -v $HOME/.ssh:/root/.ssh:ro --user root -e XDG_CACHE_HOME=/tmp/cache -e UV_CACHE_DIR=/tmp/cache/uv'
        }
    }
    
    environment {
        PYTHONUNBUFFERED = '1'
    }
    
    stages {
        stage('Clean Python Caches') {
            steps {
                script {
                    echo "Cleaning Python cache directories to prevent permission issues..."
                    sh '''
                        # Remove cache directories that can cause permission issues in Jenkins
                        rm -rf .mypy_cache .pytest_cache __pycache__ *.pyc
                        find . -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true
                        find . -type f -name '*.pyc' -delete 2>/dev/null || true
                        echo "✓ Cache directories cleaned"
                    '''
                }
            }
        }
        
        stage('Install System Dependencies') {
            steps {
                script {
                    echo "[JENKINS] Installing all system and dev tools via setup_venv.sh --dev..."
                    sh '''
                        chmod +x setup_venv.sh
                        # use clean in case immich server updated version and we need to refresh client
                        bash setup_venv.sh --clean --dev 
                    '''
                }
            }
        }
        
        stage('Validate Installation') {
            steps {
                script {
                    echo "Validating installation..."
                    sh '''
                        . .venv/bin/activate
                        python -c "from immich_autotag import __version__; print(f'✓ immich_autotag {__version__}')"
                        python -c "import immich_client; print('✓ immich_client installed')"
                        echo "✓ All imports successful"
                    '''
                }
            }
        }
        stage('Quality Gate (Python OO)') {
            steps {
                script {
                    echo "================ PYTHON QUALITY GATE (MODULAR OO VERSION) ================"
                    echo "[PYTHON QUALITY GATE] Ejecutando Quality Gate Python (modular OO, attrs, enum, subprocess, type-safe)"
                    sh '''
                        # Configure git safe.directory to avoid ownership errors
                        git config --global --add safe.directory "$PWD"
                        chmod +x scripts/devtools/quality_gate_py/venv_launcher.sh
                        # TODO: Temporary workaround - skipping `check_mypy` in CI until
                        # type/model discrepancies are resolved. Remove this flag and
                        # revert to full Quality Gate once fixes are applied.
                        # FIXME: ensure we don't forget to remove this.
                        #bash scripts/devtools/quality_gate_py/venv_launcher.sh --level=STANDARD --mode=CHECK --skip-checks=check_mypy
                        bash scripts/devtools/quality_gate_py/venv_launcher.sh --level=STANDARD --mode=CHECK 
                    '''
                }
            }
        }
        stage('Quality Gate (Docs Links)') {
            steps {
                script {
                    echo "================ DOCS LINK GATE (darnlink) ================"
                    echo "[DOCS LINK GATE] Checking uuid-anchored Markdown links (read-only, no --write)"
                    sh '''
                        git config --global --add safe.directory "$PWD"
                        # darnlink runs via uvx; ensure uv is available in a
                        # predictable location (user site, not a global pip).
                        export PATH="$HOME/.local/bin:$PATH"
                        command -v uvx >/dev/null 2>&1 || python3 -m pip install --quiet --user uv
                        bash scripts/devtools/darnlink_docs_gate.sh .
                    '''
                }
            }
        }
        // ── The surfaces no file gate can see, on the wall that does not bill ─────────────────
        //
        // `check_no_spanish_chars` already runs above, inside the Python quality gate, and it is
        // better than darnlang on FILES: every tracked file, file names too, a curated wordlist.
        // Nothing here touches it.
        //
        // What no file gate can see is what is written straight into GitHub. The same check runs in
        // Actions, and it is duplicated here on purpose: Actions is the surface that stops when a
        // payment fails -- three-second red runs with no steps, on this account, this month --
        // while this controller is self-hosted and does not bill. The published surfaces are also
        // the least retractable ones there are, so they are the last place to accept a wall that
        // can be switched off by an invoice.
        //
        // A multibranch build exposes CHANGE_TITLE / CHANGE_BODY / CHANGE_TARGET on a PR, so the
        // same three surfaces are reachable from here.
        stage('Quality Gate (Language, published surfaces)') {
            steps {
                sh '''
                    set -eu
                    export PATH="$HOME/.local/bin:$PATH"
                    command -v uvx >/dev/null 2>&1 || python3 -m pip install --quiet --user uv
                    . tools/darnlang_ref.sh
                    # Resolve first, judge second: uvx exits 1 when it cannot reach the ref, the same
                    # code a finding uses, and conflating them reads a network hiccup as Spanish.
                    uvx --from "$DARNLANG_REF" darnlang --help >/dev/null

                    # ONE MESSAGE AT A TIME: concatenating a range and judging it as a single text
                    # lets one English line hide a Spanish one.
                    if [ -n "${CHANGE_TARGET:-}" ]; then
                      git fetch --no-tags origin "$CHANGE_TARGET"
                      RANGE="FETCH_HEAD..HEAD"
                    else
                      RANGE="HEAD -1"
                    fi
                    fail=0
                    for sha in $(git log --format=%H $RANGE); do
                      git log -1 --format=%B "$sha" > .darnlang-msg
                      uvx --from "$DARNLANG_REF" darnlang prose .darnlang-msg \
                        --label "commit message $sha" || fail=1
                    done
                    rm -f .darnlang-msg

                    if [ -n "${CHANGE_TITLE:-}" ]; then
                      printf '%s\n\n%s\n' "$CHANGE_TITLE" "${CHANGE_BODY:-}" > .darnlang-pr
                      uvx --from "$DARNLANG_REF" darnlang prose .darnlang-pr \
                        --label "PR title/description" || fail=1
                      rm -f .darnlang-pr
                    fi
                    exit "$fail"
                '''
            }
        }
        stage('Quality Gate (Shell Script)') {
            when {
                expression { false } // Disabled: deprecated shell quality gate. Keep stage for history, skip execution.
            }
            steps {
                script {
                    echo '🚨🚨 DEPRECATED: QUALITY GATE (SHELL SCRIPT) - USE PYTHON VERSION INSTEAD 🚨🚨'
                    echo "Running Quality Gate (relaxed mode)..."
                    sh '''
                        chmod +x scripts/devtools/quality_gate.sh
                        bash scripts/devtools/quality_gate.sh --level=STANDARD --mode=CHECK
                    '''
                }
            }
        }



        stage('Run Application') {
            steps {
                script {
                    echo "Running immich-autotag application..."
                    sh '''
                        chmod +x run_app.sh
                        bash run_app.sh
                    '''
                }
            }
        }
    }
    
    post {
        always {
            // Archive run-dir outputs only. Two changes vs the previous pattern:
            //   * `*_PID*` matches the run dir naming scheme and skips `_archive/`,
            //     which the wrap-around fills with snapshots of completed cycles
            //     and grows unbounded over time.
            //   * `fingerprint: false` — SHA1ing all run files dominated build wall
            //     time (5-47h per build for the post-actions phase). We don't
            //     consume these artifacts across pipelines, so the fingerprints
            //     have no consumer.
            archiveArtifacts artifacts: 'logs_local/*_PID*/**', excludes: 'logs_local/*/api_cache/**', fingerprint: false, allowEmptyArchive: true
            echo "Pipeline execution completed at ${new Date()}"
        }

        success {
            echo "✅ Pipeline succeeded - All stages passed"
            script {
                // Do NOT pin successful builds with keepLog=true. Pinning bypasses
                // buildDiscarder and historical builds accumulate forever, filling
                // the master disk (we hit 99% in May 2026). If a specific build
                // needs to be retained, mark it manually from the UI instead.
                if (ENABLE_JENKINS_TAGGING) {
                    tagBuild('success')
                } else {
                    echo "[INFO] Jenkins tagging and push is disabled by ENABLE_JENKINS_TAGGING flag."
                }
                if (ENABLE_AUTO_CHAIN) {
                    echo "🔁 Auto-chain enabled: triggering next build on this branch"
                    build job: env.JOB_NAME, wait: false, propagate: false
                } else {
                    echo "[INFO] Auto-chain disabled by ENABLE_AUTO_CHAIN flag."
                }
            }
        }
        failure {
            echo "❌ Pipeline FAILED - Check logs above"
            script {
                if (ENABLE_JENKINS_TAGGING) {
                    tagBuild('fail')
                } else {
                    echo "[INFO] Jenkins tagging and push is disabled by ENABLE_JENKINS_TAGGING flag."
                }
            }
        }
        aborted {
            echo "⚠️ Pipeline ABORTED - Build was cancelled"
            script {
                if (ENABLE_JENKINS_TAGGING) {
                    tagBuild('abort')
                } else {
                    echo "[INFO] Jenkins tagging and push is disabled by ENABLE_JENKINS_TAGGING flag."
                }
            }
        }
    }
}
