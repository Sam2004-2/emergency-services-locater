# GitHub Setup Guide

This repository has been initialized with Git. Follow these steps to push it to GitHub.

## Quick Setup

### Option 1: Create a New Repository on GitHub

1. **Go to GitHub** and create a new repository:
   - Visit https://github.com/new
   - Repository name: `emergency-services-locator` (or your preferred name)
   - Description: "Interactive web mapping application for locating emergency services using Django, PostGIS, and Leaflet"
   - **DO NOT** initialize with README, .gitignore, or license (we already have these)
   - Click "Create repository"

2. **Connect your local repository to GitHub**:

```bash
# Add GitHub as remote origin (replace YOUR_USERNAME with your GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/emergency-services-locator.git

# Push to GitHub
git push -u origin main
```

### Option 2: Using GitHub CLI (if installed)

```bash
# Login to GitHub (if not already logged in)
gh auth login

# Create repository and push
gh repo create emergency-services-locator --public --source=. --remote=origin --push

# Or for private repository
gh repo create emergency-services-locator --private --source=. --remote=origin --push
```

### Option 3: Using SSH (if you have SSH keys configured)

```bash
# Add GitHub as remote origin (replace YOUR_USERNAME with your GitHub username)
git remote add origin git@github.com:YOUR_USERNAME/emergency-services-locator.git

# Push to GitHub
git push -u origin main
```

## After Pushing to GitHub

### 1. Update README.md

Replace placeholder links in README.md with your actual repository:
- Change `yourusername` to your GitHub username
- Update email addresses
- Add actual screenshots to `docs/screenshots/`

### 2. Enable GitHub Pages (Optional)

If you want to host documentation:
1. Go to repository Settings → Pages
2. Select source: `main` branch, `/docs` folder
3. Save

### 3. Add Repository Topics

Add relevant topics to your repository:
- `django`
- `postgis`
- `leaflet`
- `geospatial`
- `webmapping`
- `gis`
- `emergency-services`
- `docker`
- `rest-api`

### 4. Set Up Branch Protection (Optional)

For production:
1. Go to Settings → Branches
2. Add rule for `main` branch
3. Enable "Require pull request reviews before merging"

## Repository Structure

```
emergency-services-locator/
├── .git/                      # Git repository data
├── .gitignore                 # Files to ignore
├── LICENSE                    # MIT License
├── README.md                  # Main documentation
├── requirements.txt           # Python dependencies
├── docker-compose.yml         # Docker orchestration
├── manage.py                  # Django management
├── boundaries/                # County boundaries app
├── services/                  # Emergency services app
├── frontend/                  # Map interface app
├── es_locator/               # Django project settings
├── docker/                    # Docker configuration
├── docs/                      # Documentation
└── spatial_data/             # Spatial data storage
```

## Useful Git Commands

### Daily Workflow

```bash
# Check status
git status

# Stage changes
git add .

# Commit changes
git commit -m "Your descriptive message"

# Push to GitHub
git push

# Pull latest changes
git pull
```

### Create a New Feature

```bash
# Create and switch to new branch
git checkout -b feature/your-feature-name

# Make changes and commit
git add .
git commit -m "Add new feature"

# Push branch to GitHub
git push -u origin feature/your-feature-name

# Create pull request on GitHub
```

### View History

```bash
# View commit history
git log --oneline --graph --all

# View changes
git diff
```

## Common Issues

### Large Files

If you have large spatial data files, consider using Git LFS:

```bash
# Install Git LFS
brew install git-lfs  # macOS
# or: sudo apt-get install git-lfs  # Linux

# Initialize Git LFS
git lfs install

# Track large files
git lfs track "*.geojson"
git lfs track "*.shp"

# Add .gitattributes
git add .gitattributes
git commit -m "Add Git LFS tracking"
```

### Sensitive Data

**IMPORTANT**: Never commit:
- `.env` files with real credentials
- Database dumps with sensitive data
- API keys or tokens
- Private keys

These are already in `.gitignore`, but double-check before pushing.

### Reset Last Commit (if needed)

```bash
# Undo last commit but keep changes
git reset --soft HEAD~1

# Undo last commit and discard changes
git reset --hard HEAD~1
```

## Next Steps

1. ✅ Repository initialized
2. ⬜ Push to GitHub
3. ⬜ Update README with actual links
4. ⬜ Add screenshots to `docs/screenshots/`
5. ⬜ Add repository topics
6. ⬜ Set up GitHub Actions (optional)
7. ⬜ Configure branch protection (optional)

## Resources

- [GitHub Docs](https://docs.github.com/)
- [Git Documentation](https://git-scm.com/doc)
- [GitHub CLI](https://cli.github.com/)
- [Git LFS](https://git-lfs.github.com/)

---

**Current Status**: 
- ✅ Git repository initialized
- ✅ Initial commit created (79 files)
- ✅ Branch renamed to `main`
- ⏳ Ready to push to GitHub

**Commit Hash**: `ac4badb`
**Files Committed**: 79 files, 7,351 lines
