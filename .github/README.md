# GitHub Actions Configuration

This directory contains GitHub Actions workflows for the m2m project.

## Docker Build and Push Workflow

The `docker-build.yml` workflow automatically builds and publishes Docker images to Docker Hub.

### Required Secrets

To enable Docker Hub publishing, configure these repository secrets in GitHub:

1. Go to your repository Settings → Secrets and variables → Actions
2. Add the following secrets:

- `DOCKERHUB_USERNAME`: Your Docker Hub username
- `DOCKERHUB_TOKEN`: Your Docker Hub access token (not password!)

### Creating a Docker Hub Access Token

1. Log in to [Docker Hub](https://hub.docker.com/)
2. Go to Account Settings → Security → Access Tokens
3. Click "New Access Token"
4. Give it a description (e.g., "GitHub Actions - m2m")
5. Set permissions to "Read & Write"
6. Generate and copy the token
7. Add it to GitHub repository secrets as `DOCKERHUB_TOKEN`

### Workflow Triggers

The workflow automatically runs on:

- **Push to main branch**: Builds and tags as `latest`
- **Push to dev branch**: Builds and tags as `dev`
- **Version tags** (e.g., `v1.0.0`): Builds and tags as `1.0.0`, `1.0`, `1`, and `latest`
- **Pull requests**: Builds but doesn't push (for testing)
- **Manual trigger**: Via GitHub Actions UI

### Image Tags

Images are published to: `linumuqam/m2m`

Tag strategy:
- `latest`: Latest stable release from main branch
- `dev`: Development builds from dev branch
- `1.0.0`, `1.0`, `1`: Semantic version tags from releases
- `main`, `dev`: Branch-based tags
- `pr-123`: Pull request builds (not pushed)

### Platform Support

The workflow currently builds images for the following platform:
- `linux/amd64` (Intel/AMD 64-bit)
