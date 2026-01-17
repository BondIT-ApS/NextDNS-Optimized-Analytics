# 🧱 VSCode Configuration - NextDNS Optimized Analytics

This folder contains team-shared VSCode configuration for the NextDNS Optimized Analytics project.

## 🚀 Quick Setup

### For New Team Members:

1. **Copy templates to create your local settings:**
   ```bash
   cd .vscode
   cp settings.json.template settings.json
   cp launch.json.template launch.json
   ```

2. **Install recommended extensions:**
   - VSCode will automatically prompt you to install recommended extensions
   - Or manually: `Cmd+Shift+P` → "Extensions: Show Recommended Extensions"

3. **Verify Python interpreter:**
   - `Cmd+Shift+P` → "Python: Select Interpreter"
   - Choose: `backend/venv/bin/python`

## 📁 File Structure

### Shared Files (committed to git):
- **`extensions.json`** - Recommended extensions for the project
- **`tasks.json`** - Build, test, and development tasks
- **`*.json.template`** - Templates for local configuration
- **`README.md`** - This setup guide

### Local Files (ignored by git):
- **`settings.json`** - Your personal VSCode settings (created from template)
- **`launch.json`** - Your debug configurations (created from template)

## 🔧 Key Features

### Backend Development:
- ✅ Python virtual environment auto-detection
- ✅ Black formatting (88 char line length)
- ✅ Pylint linting with project-specific rules
- ✅ pytest test discovery and debugging

### Frontend Development:
- ✅ TypeScript + React 19 support
- ✅ ESLint + Prettier formatting
- ✅ Vitest test integration
- ✅ Tailwind CSS intellisense

### Full Stack:
- ✅ Docker integration
- ✅ Database client (PostgreSQL, MySQL, SQLite, Redis, MongoDB, and more)
- ✅ GitHub Actions workflow validation
- ✅ Git workflow enhancements

## 🧪 Testing & Debugging

### Available Debug Configurations:
- **🧪 Debug Current Test File** - Debug the currently open test file
- **🧪 Debug All Backend Tests** - Run all backend tests with debugger
- **🧪 Debug Unit Tests Only** - Focus on unit tests
- **🧪 Debug Integration Tests Only** - Focus on API integration tests
- **🚀 Debug FastAPI Server** - Debug the backend server

### Available Tasks (Cmd+Shift+P → "Tasks: Run Task"):
- **Frontend**: Lint, format, test, type-check
- **Backend**: Test (all), unit tests only, integration tests only, lint, format, security scan
- **Docker**: Build, run, health check
- **Quality**: Full quality checks for both frontend and backend

### Test Organization:
**Frontend (Vitest)**: Tests are automatically organized by Vitest Explorer with real-time watching

**Backend (pytest)**: Tests appear in VSCode's Test Explorer organized by file structure:
- 📁 `tests/unit/` - Unit tests (37 tests) with `@pytest.mark.unit`
- 📁 `tests/integration/` - Integration tests (18 tests) with `@pytest.mark.integration`

**Run by test type:**
- Unit tests only: `🧪 Backend: Run Unit Tests Only` task
- Integration tests only: `🧪 Backend: Run Integration Tests Only` task
- Or use terminal: `pytest -m unit` or `pytest -m integration`

## 🔄 Updating Configuration

### For Template Changes:
1. Update the `.template` files
2. Commit and push changes
3. Team members can merge changes into their local files as needed

### For Personal Settings:
- Modify your local `settings.json` and `launch.json`
- These changes stay local and won't be committed

## 🆘 Troubleshooting

### Tests Not Showing Up:
1. Reload window: `Cmd+Shift+P` → "Developer: Reload Window"
2. Refresh tests: `Cmd+Shift+P` → "Python: Test: Refresh Tests"
3. Check Python interpreter is set to `backend/venv/bin/python`

### Python Import Issues:
1. Ensure virtual environment is activated in VSCode
2. Check that `python.analysis.extraPaths` includes the backend folder
3. Restart Python language server: `Cmd+Shift+P` → "Python: Restart Language Server"

---
*Following the LEGO principle - every piece should fit together perfectly! 🧱*