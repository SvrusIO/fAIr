# Release Process and Checklist

**Last Updated:** 2026-01-16  
**Current Version:** 0.5.0

This document outlines the complete release process for the Fairness Pipeline Development Toolkit, including pre-release checks, version management, build procedures, PyPI publication, and post-release tasks.

---

## Overview

The toolkit follows [Semantic Versioning (SemVer)](https://semver.org/spec/v2.0.0.html) and is published to [PyPI](https://pypi.org/project/fairness-pipeline-dev-toolkit/). This guide ensures consistent, reliable releases with proper documentation and testing.

**Release Types:**
- **PATCH** (0.0.X): Bug fixes, security patches, minor improvements
- **MINOR** (0.X.0): New features, enhancements (backward compatible)
- **MAJOR** (X.0.0): Breaking changes (requires user code modifications)

**Current Status:** Beta (0.5.0) - Pre-1.0.0 releases may include breaking changes in MINOR versions with notice.

---

## Pre-Release Checklist

Before starting a release, ensure all items are completed:

### Code Quality and Testing

- [ ] **All tests passing**: Run full test suite
  ```bash
  pytest -q
  ```
- [ ] **Test coverage maintained**: Verify coverage hasn't decreased
  ```bash
  pytest --cov=fairness_pipeline_dev_toolkit --cov-report=html
  ```
- [ ] **Linting and formatting**: Ensure code passes all checks
  ```bash
  ruff check fairness_pipeline_dev_toolkit/
  black --check fairness_pipeline_dev_toolkit/
  isort --check fairness_pipeline_dev_toolkit/
  ```
- [ ] **Type checking** (optional but recommended):
  ```bash
  mypy fairness_pipeline_dev_toolkit/
  ```

### Documentation

- [ ] **README.md updated**: Verify installation instructions, examples, and usage are current
- [ ] **API documentation current**: Ensure `docs/api.md` reflects any API changes
- [ ] **Integration guide updated**: Check `docs/integration_guide.md` for accuracy
- [ ] **CHANGELOG.md prepared**: All changes documented with proper categorization
- [ ] **Versioning strategy reviewed**: Check `docs/VERSIONING.md` if version type is unclear

### Version and Metadata

- [ ] **Version number determined**: Based on changes (PATCH/MINOR/MAJOR)
- [ ] **Dependencies reviewed**: Check `pyproject.toml` for dependency updates
- [ ] **Python version support**: Verify supported Python versions in `pyproject.toml`
- [ ] **Package metadata**: Review description, classifiers, URLs in `pyproject.toml`

### Integration and Compatibility

- [ ] **Backward compatibility verified**: For MINOR/PATCH releases, ensure no breaking changes
- [ ] **Migration notes prepared**: If breaking changes exist, document migration path
- [ ] **Example configs tested**: Verify example configuration files work with new version
- [ ] **CLI commands tested**: Test all CLI commands with example data

### Security and Legal

- [ ] **Security vulnerabilities addressed**: Review and fix any known security issues
- [ ] **License compliance**: Ensure all dependencies are compatible with Apache 2.0
- [ ] **Third-party attributions**: Verify all third-party code is properly attributed

---

## Release Process

### Step 1: Prepare Release Branch

Create a release branch from `main` (or `develop` if using Git Flow):

```bash
# Ensure you're on main and up to date
git checkout main
git pull origin main

# Create release branch
git checkout -b release/v0.5.1  # Replace with your version
```

### Step 2: Update Version Numbers

Update version in all necessary locations:

#### 2.1 Update `pyproject.toml`

```bash
# Edit pyproject.toml
# Update: version = "0.5.1"  # Replace with new version
```

**File:** `pyproject.toml`
```toml
[project]
version = "0.5.1"  # Update this line
```

#### 2.2 Update `__init__.py`

**File:** `fairness_pipeline_dev_toolkit/__init__.py`
```python
__version__ = "0.5.1"  # Update this line
```

#### 2.3 Update README.md (if version is displayed)

**File:** `README.md`
```markdown
**Version:** 0.5.1  # Update if version is shown at top
```

#### 2.4 Update Versioning Documentation (if major version change)

**File:** `docs/VERSIONING.md`
```markdown
**Current Version:** 0.5.1  # Update if major/minor version
```

### Step 3: Update CHANGELOG.md

Add a new release entry to `CHANGELOG.md`:

**File:** `CHANGELOG.md`

```markdown
## [v0.5.1] — 2026-01-XX

### Fixed
- Description of bug fixes

### Changed
- Description of changes

### Added
- Description of new features

### Purpose
Brief summary of the release purpose and key improvements.

**Migration Notes** (if applicable):
- Any breaking changes or migration steps
```

**CHANGELOG Guidelines:**
- Use [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) format
- Categorize changes: Added, Changed, Deprecated, Removed, Fixed, Security
- Include migration notes for breaking changes
- Replace "2026-01-XX" with actual release date
- Be specific and user-focused

### Step 4: Commit Version Updates

Commit all version-related changes:

```bash
git add pyproject.toml
git add fairness_pipeline_dev_toolkit/__init__.py
git add CHANGELOG.md
git add README.md  # if updated
git add docs/VERSIONING.md  # if updated

git commit -m "Bump version to 0.5.1"
```

### Step 5: Run Final Tests

Run comprehensive tests one final time:

```bash
# Full test suite
pytest -q

# System/integration tests
pytest tests/system/ tests/integration/ -q

# CLI tests
pytest tests/cli/ -q
```

### Step 6: Build Distribution Packages

Build source and wheel distributions:

```bash
# Clean previous builds
rm -rf dist/ build/ *.egg-info/

# Run build script
./scripts/build.sh

# Verify distributions
ls -lh dist/
# Should see:
# - fairness-pipeline-dev-toolkit-0.5.1-py3-none-any.whl
# - fairness-pipeline-dev-toolkit-0.5.1.tar.gz
```

**Build Script:** `scripts/build.sh`
- Runs `python -m build`
- Validates distributions with `twine check`

**Verify Build:**
- Check that version in built packages matches intended version
- Ensure no unexpected files are included
- Verify package metadata is correct

### Step 7: Test Installation (Optional but Recommended)

Test installation from local wheel:

```bash
# Create virtual environment
python -m venv test_install
source test_install/bin/activate  # On Windows: test_install\Scripts\activate

# Install from local wheel
pip install dist/fairness-pipeline-dev-toolkit-0.5.1-py3-none-any.whl

# Verify installation
fairpipe version  # Should show 0.5.1

# Run quick smoke test
fairpipe validate --help  # Should work

# Cleanup
deactivate
rm -rf test_install
```

### Step 8: Create Git Tag

Create an annotated git tag for the release:

```bash
# Create annotated tag
git tag -a v0.5.1 -m "Release v0.5.1"

# Verify tag
git tag -l "v*"
git show v0.5.1
```

**Tag Naming Convention:**
- Format: `v0.5.1` (lowercase 'v' prefix)
- Use semantic version number
- Tag message should match CHANGELOG summary

### Step 9: Push Release Branch and Tag

Push the release branch and tag to remote:

```bash
# Push release branch
git push origin release/v0.5.1

# Push tag
git push origin v0.5.1
```

### Step 10: Publish to PyPI

Publish to PyPI using the publish script:

**Prerequisites:**
- PyPI account with maintainer access
- `twine` installed: `pip install twine`
- PyPI credentials configured (see [PyPI API Tokens](https://pypi.org/help/#apitoken))

**Test Publication (TestPyPI):**

```bash
# Upload to TestPyPI first (recommended)
twine upload --repository testpypi dist/*

# Test installation from TestPyPI
pip install --index-url https://test.pypi.org/simple/ fairness-pipeline-dev-toolkit==0.5.1
```

**Production Publication:**

```bash
# Upload to PyPI
./scripts/publish.sh

# Or manually:
twine upload dist/*
```

**Publish Script:** `scripts/publish.sh`
- Runs `twine upload dist/*`
- Requires PyPI credentials (via `~/.pypirc` or environment variables)

**PyPI Credentials:**
- Use API tokens (recommended): Create token at https://pypi.org/manage/account/token/
- Set environment variable: `export TWINE_PASSWORD=<token>`
- Or use `~/.pypirc` configuration file

### Step 11: Merge Release Branch

Merge release branch back to main:

```bash
# Switch to main
git checkout main

# Merge release branch
git merge release/v0.5.1

# Push to main
git push origin main

# Delete release branch (local and remote)
git branch -d release/v0.5.1
git push origin --delete release/v0.5.1
```

---

## Post-Release Tasks

### Immediate (Within 24 hours)

- [ ] **Verify PyPI publication**: Check package appears on PyPI
  ```bash
  pip install fairness-pipeline-dev-toolkit==0.5.1
  fairpipe version  # Should show new version
  ```

- [ ] **Create GitHub Release**: Create release on GitHub
  - Go to: https://github.com/SvrusIO/fAIr/releases/new
  - Tag: Select `v0.5.1`
  - Title: `Release v0.5.1`
  - Description: Copy from CHANGELOG.md release section
  - Attach release notes or link to CHANGELOG

- [ ] **Update documentation site** (if applicable): Update any hosted documentation

- [ ] **Announce release** (if applicable): 
  - Update project status in README if needed
  - Notify stakeholders if internal project

### Short-term (Within 1 week)

- [ ] **Monitor for issues**: Watch for user reports or installation problems
- [ ] **Update demo notebooks**: Ensure demo notebooks work with new version
- [ ] **Review dependency updates**: Check if any dependencies need updating
- [ ] **Documentation review**: Verify all documentation links and examples work

### Long-term (Ongoing)

- [ ] **Collect feedback**: Monitor GitHub issues and user feedback
- [ ] **Plan next release**: Begin planning features for next version
- [ ] **Update roadmap**: Update project roadmap if applicable

---

## Emergency Release Process

For critical bug fixes or security patches:

### Hotfix Release

1. **Create hotfix branch from latest release tag:**
   ```bash
   git checkout -b hotfix/v0.5.1.1 v0.5.1
   ```

2. **Apply fix and test:**
   - Make minimal changes to fix the issue
   - Run tests to verify fix
   - Update CHANGELOG with fix description

3. **Bump PATCH version:**
   - Update version to `0.5.1.1` (or next PATCH)
   - Follow normal version update process

4. **Fast-track release:**
   - Build and test
   - Tag and publish immediately
   - Merge to main after publication

5. **Document urgency:**
   - Clearly mark in CHANGELOG as security fix or critical bug
   - Consider GitHub security advisory if security-related

---

## Release Checklist Summary

### Pre-Release
- [ ] All tests passing
- [ ] Code quality checks pass
- [ ] Documentation updated
- [ ] CHANGELOG.md prepared
- [ ] Version numbers updated
- [ ] Dependencies reviewed

### Release
- [ ] Release branch created
- [ ] Version bumped in all files
- [ ] CHANGELOG.md updated
- [ ] Final tests run
- [ ] Distribution packages built
- [ ] Git tag created
- [ ] Tag pushed to remote
- [ ] Published to PyPI (or TestPyPI first)
- [ ] Release branch merged to main

### Post-Release
- [ ] PyPI publication verified
- [ ] GitHub release created
- [ ] Documentation updated
- [ ] Monitoring for issues

---

## Troubleshooting

### Build Failures

**Issue:** `python -m build` fails
- **Solution:** Ensure `build` and `wheel` are installed: `pip install build wheel`
- Check `pyproject.toml` syntax is valid

**Issue:** `twine check` fails
- **Solution:** Review package metadata in `pyproject.toml`
- Ensure README.md exists and is valid Markdown

### Publication Failures

**Issue:** Authentication error when uploading
- **Solution:** Verify PyPI credentials
- Check API token is valid and has upload permissions
- Ensure `TWINE_USERNAME` and `TWINE_PASSWORD` are set correctly

**Issue:** Package already exists
- **Solution:** Version number must be unique
- Increment version if republishing same version
- Check PyPI for existing version

### Version Mismatches

**Issue:** Installed version doesn't match expected
- **Solution:** Verify version in `pyproject.toml` and `__init__.py` match
- Clear pip cache: `pip cache purge`
- Reinstall: `pip install --no-cache-dir fairness-pipeline-dev-toolkit==0.5.1`

---

## Version Number Guidelines

### When to Bump PATCH (0.0.X)

- Bug fixes that don't change behavior
- Security patches
- Documentation corrections
- Internal refactoring with no external impact
- Performance improvements with no API changes

**Example:** `0.5.0` → `0.5.1`

### When to Bump MINOR (0.X.0)

- New features that are backward compatible
- New optional parameters to existing functions
- New classes or modules
- Enhanced functionality
- New CLI commands or optional arguments

**Example:** `0.5.0` → `0.6.0`

**Note:** Pre-1.0.0, MINOR versions may include breaking changes with notice.

### When to Bump MAJOR (X.0.0)

- Breaking changes to public APIs
- Removal of deprecated features
- Incompatible changes to configuration schema
- Changes requiring user code modifications
- Major architectural changes

**Example:** `0.5.0` → `1.0.0`

---

## Automation Opportunities

Consider automating parts of the release process:

### GitHub Actions

- Automated testing on release branches
- Automated PyPI publication on tag push
- Automated CHANGELOG generation
- Automated version bumping

### Scripts

- Version bump script (updates all version locations)
- Release preparation script (runs all checks)
- Automated CHANGELOG entry generation

### Tools

- `bump2version` or `bumpversion` for version management
- `release-please` for automated releases
- `semantic-release` for semantic versioning automation

---

## Additional Resources

- **Versioning Strategy**: See [docs/VERSIONING.md](docs/VERSIONING.md)
- **Contributing Guide**: See [CONTRIBUTING.md](CONTRIBUTING.md)
- **PyPI Documentation**: https://packaging.python.org/
- **Semantic Versioning**: https://semver.org/
- **Keep a Changelog**: https://keepachangelog.com/

---

## Release History

| Version | Release Date | Type | Notes |
|---------|--------------|------|-------|
| 0.5.1   | TBD          | PATCH | Critical intersectional analysis fix |
| 0.5.0   | 2025-01-XX   | MINOR | Integrated end-to-end workflow |
| 0.4.2   | 2025-01-XX   | PATCH | Monitoring module improvements |
| 0.4.1   | 2025-11-19   | PATCH | Training module fixes |
| 0.4.0   | 2025-11-01   | MINOR | Training module introduction |

---

## Questions or Issues?

If you encounter issues during the release process:

1. **Check this document** for troubleshooting steps
2. **Review recent releases** for examples
3. **Consult team members** if unclear on version type
4. **Document issues** for future reference

For questions about the release process, open an issue on GitHub or contact the maintainers.

---

**Last Release:** v0.5.1 (if applicable)  
**Next Planned Release:** TBD  
**Maintainer:** Svrus LLC
