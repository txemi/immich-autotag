# Issue 0014: Jenkins Pipeline Containerization

**Status:** 🟡 Proposed  
**Priority:** High  
**Created:** 2026-01-14  
**Tech Stack:** Jenkins, Docker, Python, Bash

---

## 📋 Problem Statement

The current Jenkins pipeline setup has recurring issues with:
- **Dependency hell:** Different Python versions, library conflicts, and environment inconsistencies
- **Reproducibility:** Local development environment differs from Jenkins CI environment
- **Debugging difficulty:** Hard to reproduce CI failures locally
- **Maintenance overhead:** Manual setup of Python virtual environments and dependencies

### Current Workflow Issues
- Setup scripts (`setup_venv.sh`, `run_app.sh`) work locally but may fail in Jenkins
- No guarantee that Jenkins environment matches production/development environments
- Library version conflicts cause unpredictable failures

---

## 🎯 Objective

**Encapsulate the Jenkins pipeline in a containerized environment** to ensure:
1. ✅ **Reproducibility:** Same environment everywhere (local, CI, production)
2. ✅ **Isolation:** No conflicts with host system dependencies
3. ✅ **Ease of debugging:** Run the same Docker image locally to reproduce CI issues
4. ✅ **Faster setup:** Pre-built images with cached dependencies

---

## 🔍 Proposed Solutions

### **Option A: Jenkins Docker Agent (Dockerfile-based)** ⭐ **RECOMMENDED**

**Description:** Use Jenkins' native Docker support with a custom Dockerfile.

**Implementation:**
```groovy
pipeline {
    agent {
        dockerfile {
            filename 'Dockerfile'
            args '-v $HOME/.cache:/root/.cache'
        }
    }
    stages {
        stage('Run Application') {
            steps {
                sh 'bash run_app.sh'
            }
        }
    }
}
```

**Pros:**
- ✅ Jenkins manages container lifecycle automatically
- ✅ Full control over base image and dependencies
- ✅ Docker layer caching speeds up builds
- ✅ Can pre-install heavy dependencies (OpenCV, ML libs, etc.)
- ✅ Works seamlessly with existing Dockerfile

**Cons:**
- ⚠️ Requires Docker configured in Jenkins
- ⚠️ Need to maintain Dockerfile (but we already have one)

**Requirements:**
- Jenkins with Docker plugin enabled
- Docker daemon accessible to Jenkins agent

---

### **Option B: Docker Compose for Local + CI**

**Description:** Use Docker Compose to define services, making it easy to run locally and in Jenkins.

**Implementation:**
```yaml
# docker-compose.jenkins.yml
version: '3.8'
services:
  immich-autotag:
    build: .
    volumes:
      - .:/app
    environment:
      - IMMICH_API_KEY=${IMMICH_API_KEY}
      - IMMICH_API_URL=${IMMICH_API_URL}
    command: bash run_app.sh
```

```groovy
// Jenkinsfile
pipeline {
    agent any
    stages {
        stage('Run in Container') {
            steps {
                sh 'docker-compose -f docker-compose.jenkins.yml run --rm immich-autotag'
            }
        }
    }
}
```

**Pros:**
- ✅ Identical environment for local development and CI
- ✅ Easy to add services (databases, mock APIs, etc.)
- ✅ Simple debugging: `docker-compose up` locally
- ✅ Environment variables managed cleanly

**Cons:**
- ⚠️ Requires docker-compose installed in Jenkins
- ⚠️ Slightly more complex setup

---

### **Option C: Pre-built Docker Image (Registry-based)**

**Description:** Build and push Docker image to a registry (Docker Hub, GitHub Container Registry), then Jenkins pulls it.

**Implementation:**
```groovy
pipeline {
    agent {
        docker {
            image 'ghcr.io/txemi/immich-autotag:latest'
            args '-v $HOME/.cache:/root/.cache'
        }
    }
    stages {
        stage('Run Application') {
            steps {
                sh 'bash run_app.sh'
            }
        }
    }
}
```

**Pros:**
- ✅ Fastest CI builds (no build step, just pull)
- ✅ Image versioning via tags
- ✅ Reduces Jenkins resource usage

**Cons:**
- ⚠️ Requires image registry setup
- ⚠️ Need separate CI job to build and push images
- ⚠️ Potential lag between code changes and image updates

---

## 📊 Comparison Matrix

| Criteria | Option A (Dockerfile) | Option B (Compose) | Option C (Registry) |
|----------|----------------------|-------------------|---------------------|
| **Setup Complexity** | Low | Medium | High |
| **Build Speed** | Medium (cached) | Medium | Fast (pre-built) |
| **Local Development** | Good | Excellent | Good |
| **Debugging Ease** | Good | Excellent | Medium |
| **Maintenance** | Low | Medium | High |
| **Recommended For** | CI pipelines | Dev + CI | Large teams |

---

## ✅ Acceptance Criteria

- [ ] Jenkins pipeline runs in isolated Docker container
- [ ] Local reproduction of Jenkins environment is possible
- [ ] No dependency conflicts with host system
- [ ] Pipeline execution time is acceptable (<5min for basic run)
- [ ] Dockerfile or docker-compose.yml is documented
- [ ] CI failures are reproducible locally using same Docker setup

---

## 🚀 Implementation Plan

### Phase 1: Dockerfile Optimization
1. Review existing `Dockerfile` and `Dockerfile.cron`
2. Optimize for CI (layer caching, minimal image size)
3. Pre-install dependencies in image

### Phase 2: Update Jenkinsfile
1. Modify `Jenkinsfile` to use Docker agent
2. Test pipeline with containerized setup
3. Validate that `setup_venv.sh` and `run_app.sh` work in container

### Phase 3: Documentation
1. Document Docker setup in `docs/docker.md`
2. Add troubleshooting guide for common issues
3. Update `CONTRIBUTING.md` with container-based development workflow

---

## 📚 References

- [Jenkins Docker Pipeline Plugin](https://plugins.jenkins.io/docker-workflow/)
- [Best Practices for Dockerfile](https://docs.docker.com/develop/dev-best-practices/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)

---

## 🔗 Related Issues

- **Issue 0012:** Cleanup and Redeploy (infrastructure context)
- **Future:** Quality Gate Policy (will benefit from containerized testing)

---

**Next Steps:** Choose preferred option and begin Dockerfile optimization.
