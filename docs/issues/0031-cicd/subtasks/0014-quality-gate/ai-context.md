# AI Context: Jenkins Pipeline Containerization Discussion

**Date:** 2026-01-14  
**AI Assistant:** GitHub Copilot (Claude Sonnet 4.5)  
**Context:** Feature branch `feature/jenkins-pipeline` created for Jenkins CI/CD setup

---

## 🧠 Problem Analysis

### User's Pain Points
- **"A ton of mess with libraries":** Dependency management is a recurring issue
- **"This Python thing and its endless trouble":** Version conflicts are frustrating
- **"Always start from the same point":** Need deterministic, reproducible environment
- **"Not go crazy with strange errors":** Want predictable CI behavior

### Root Cause
Current setup relies on:
- Host Python installation (version varies)
- Virtual environment created by `setup_venv.sh` (can differ based on host)
- No isolation from system-level libraries

---

## 💡 AI Recommendations

### Why Containerization is Critical
1. **Immutability:** Same base image every time
2. **Dependency isolation:** No conflicts with host system
3. **Version locking:** Exact Python version, library versions
4. **Reproducibility:** `docker run` locally = Jenkins run
5. **Debuggability:** Reproduce CI failures by running same container

### Recommended Approach: **Option A (Dockerfile + Jenkins Docker Agent)**

**Reasoning:**
- Project already has `Dockerfile` and `Dockerfile.cron`
- Minimal changes to existing workflow
- Jenkins Docker plugin is mature and well-supported
- Caching makes builds fast after first run
- No need for external registry initially

---

## 🔧 Technical Implementation Notes

### Dockerfile Optimization Strategy
```dockerfile
# Use specific Python version (not 'latest')
FROM python:3.11-slim

# Install system dependencies in one layer
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy and install requirements FIRST (cacheable layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code LAST (changes frequently)
COPY . .

# Pre-run setup script
RUN bash setup_venv.sh || true

CMD ["python", "main.py"]
```

**Key optimizations:**
1. **Layer ordering:** Stable layers first (OS, requirements), volatile last (code)
2. **Cache efficiency:** Requirements rarely change, code changes often
3. **Minimal image:** Use `-slim` variant, clean up apt cache
4. **No cache for pip:** Reduces image size

### Jenkinsfile Pattern
```groovy
pipeline {
    agent {
        dockerfile {
            filename 'Dockerfile'
            // Mount cache for faster builds
            args '-v $HOME/.cache:/root/.cache'
        }
    }
    
    environment {
        // Inject secrets from Jenkins credentials
        IMMICH_API_KEY = credentials('immich-api-key')
    }
    
    stages {
        stage('Validate Setup') {
            steps {
                sh 'python --version'
                sh 'pip list'
            }
        }
        
        stage('Run Application') {
            steps {
                sh 'bash run_app.sh --help'
            }
        }
    }
}
```

---

## 🚨 Potential Gotchas

### 1. **Jenkins Docker Socket Access**
- Jenkins needs access to Docker daemon
- Solution: Mount `/var/run/docker.sock` or use Docker-in-Docker

### 2. **File Permissions**
- Container runs as root by default, host files may have different UID
- Solution: Add `USER` directive in Dockerfile or fix permissions in Jenkinsfile

### 3. **Secrets Management**
- API keys must not be in Dockerfile
- Solution: Use Jenkins credentials and inject as environment variables

### 4. **Build Time**
- First build will be slow (pulling base image, installing deps)
- Solution: Use layer caching, consider pre-built image for frequently-used base

---

## 🎯 Migration Path

### Short-term (Immediate)
1. Create optimized `Dockerfile` for CI
2. Update `Jenkinsfile` to use Docker agent
3. Test basic pipeline run

### Mid-term (Next sprint)
1. Add proper test stages to Jenkins pipeline
2. Integrate with quality gates (when ready)
3. Document local Docker development workflow

### Long-term (Future)
1. Consider GitHub Actions as alternative to Jenkins
2. Publish Docker images to registry for faster pulls
3. Multi-stage builds for smaller production images

---

## 📝 Open Questions for User

1. **Current Jenkins setup:** Is Docker already available in Jenkins environment?
2. **Secrets:** How are Immich API credentials currently managed?
3. **Test data:** Do we need to mount test photo directories into container?
4. **Performance:** What's acceptable build time for CI pipeline?

---

## 🔗 Related Decisions

- **Branch strategy:** Develop → Main workflow established (Issue: Branch Policy)
- **Quality gates:** Future requirement, will benefit from containerized testing
- **Deployment:** Docker is already used (Dockerfile.cron for scheduled runs)

---

**Conclusion:** Containerization via Dockerfile + Jenkins Docker agent is the pragmatic choice. Minimal disruption, maximum benefit.
