# Testing Documentation

## Overview

The PM app has comprehensive unit tests covering all core functionality. The test suite includes 84 tests organized across 4 test modules.

## Test Coverage

### Test Modules

1. **test_task.py** (24 tests)
   - Note model tests (creation, parsing, formatting)
   - Task model tests (creation, validation, state management)
   - Task business logic (overdue detection, check scheduling, notifications)
   - Serialization/deserialization (to_dict, from_dict)

2. **test_storage.py** (18 tests)
   - Storage initialization
   - Task persistence (save, load, delete)
   - Multiple task handling
   - Special cases (special characters, corrupted files)
   - Markdown frontmatter formatting

3. **test_manager.py** (27 tests)
   - TaskManager initialization
   - CRUD operations (create, read, update, delete)
   - Filtering and search functionality
   - Task status management
   - Summary statistics
   - Task persistence and reloading

4. **test_config.py** (15 tests)
   - Configuration data classes
   - Config file loading and saving
   - Partial configurations
   - Invalid YAML handling
   - Configuration roundtrips

### Coverage by Component

- **Core Models**: ✓ Fully tested
- **Storage Layer**: ✓ Fully tested
- **Task Manager**: ✓ Fully tested
- **Configuration**: ✓ Fully tested
- **CLI Commands**: Manual testing (integration tests)

## Running Tests

### Run All Tests

```bash
# Activate virtual environment
source venv/bin/activate

# Run all tests
pytest tests/

# Run with verbose output
pytest tests/ -v

# Run quietly
pytest tests/ -q
```

### Run Specific Test Modules

```bash
# Test task model only
pytest tests/test_task.py

# Test storage only
pytest tests/test_storage.py

# Test manager only
pytest tests/test_manager.py

# Test configuration only
pytest tests/test_config.py
```

### Run Specific Test Classes or Methods

```bash
# Run specific test class
pytest tests/test_task.py::TestTask

# Run specific test method
pytest tests/test_manager.py::TestTaskManager::test_create_task
```

### Test Options

```bash
# Show detailed output on failures
pytest tests/ -v --tb=short

# Stop on first failure
pytest tests/ -x

# Run tests in parallel (requires pytest-xdist)
pytest tests/ -n auto

# Show print statements
pytest tests/ -s
```

## Test Fixtures

The test suite uses pytest fixtures defined in `conftest.py`:

- **temp_dir**: Temporary directory for test data (auto-cleanup)
- **test_config**: Test configuration instance
- **storage**: TaskStorage instance with temp directory
- **sample_task**: Pre-configured task for testing
- **multiple_tasks**: List of various task types
- **manager**: TaskManager instance with mocked config

## Test Results

### Latest Test Run

```
84 passed in 0.09s
```

### Test Breakdown

- Configuration tests: 15/15 ✓
- Task Manager tests: 27/27 ✓
- Storage tests: 18/18 ✓
- Task model tests: 24/24 ✓

**Total: 84/84 passing (100%)**

## Continuous Testing

### Watch Mode

You can use pytest-watch to automatically run tests on file changes:

```bash
# Install pytest-watch
pip install pytest-watch

# Run in watch mode
ptw
```

### Pre-commit Hook

Add this to `.git/hooks/pre-commit` to run tests before commits:

```bash
#!/bin/bash
source venv/bin/activate
pytest tests/ -q
if [ $? -ne 0 ]; then
    echo "Tests failed. Commit aborted."
    exit 1
fi
```

## Adding New Tests

### Test Structure

```python
import pytest
from pm.core.task import Task

class TestFeature:
    """Test description."""

    def test_specific_behavior(self, fixture):
        """Test a specific behavior."""
        # Arrange
        task = Task(title="Test")

        # Act
        result = task.some_method()

        # Assert
        assert result == expected_value
```

### Best Practices

1. **One assertion per test** (when possible)
2. **Clear test names** describing what is being tested
3. **Arrange-Act-Assert pattern**
4. **Use fixtures** for common setup
5. **Test edge cases** and error conditions
6. **Keep tests isolated** (no shared state)

## Test Categories

### Unit Tests (Current)

- Test individual components in isolation
- Fast execution (< 1 second)
- No external dependencies
- Mock configuration and file system

### Integration Tests (Future)

- Test CLI commands end-to-end
- Test markdown file editing workflow
- Test configuration loading from real files

### Performance Tests (Future)

- Test with large numbers of tasks
- Test search/filter performance
- Test storage performance

## Known Limitations

1. CLI commands are tested manually (not automated)
2. No integration tests yet
3. No performance benchmarks
4. Background service not yet implemented (no tests)
5. Email notifications not yet implemented (no tests)

## Troubleshooting

### Tests Fail Due to Timezone Issues

Some tests use datetime comparisons. If you see failures related to timestamps, ensure your system timezone is set correctly.

### Tests Fail Due to Permissions

The tests create temporary directories. Ensure you have write permissions in `/tmp` or the directory specified by `tempfile.gettempdir()`.

### Import Errors

Make sure the package is installed in development mode:

```bash
pip install -e .
```

## Future Test Additions

- [ ] CLI command tests (using typer testing utilities)
- [ ] Integration tests for full workflows
- [ ] Performance tests for large task lists
- [ ] Background service tests (when implemented)
- [ ] Email notification tests (when implemented)
- [ ] MCP server tests (when implemented)
- [ ] Web UI tests (when implemented)

## Test Maintenance

Run tests regularly:
- Before committing changes
- After adding new features
- After refactoring
- Before releases

Keep tests updated:
- Add tests for new features
- Update tests when changing behavior
- Remove tests for deprecated features
- Maintain test fixtures

## Contributing

When contributing code:
1. Write tests for new features
2. Ensure all existing tests pass
3. Aim for high code coverage
4. Follow existing test patterns
5. Document complex test scenarios
