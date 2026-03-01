# Tests for Planner Application

## Test Structure

```
backend/tests/
├── __init__.py
├── conftest.py                      # Test fixtures
├── test_repositories.py             # Repository layer tests
├── test_staff_availability.py      # StaffAvailability service tests
├── test_manage_assignments.py      # ManageAssignments service tests
├── test_planner.py                  # Planner service tests
├── test_views.py                    # ViewSet tests (API)
├── test_serializers.py              # Serializer tests
└── test_models.py                   # Model tests
```

## Architecture Overview

The application uses a layered architecture:

```
Views (API endpoints)
    ↓
Services (Business logic)
    ├── ManageAssignments - CRUD operations for assignments
    ├── Planner - Schedule generation algorithm
    └── StaffAvailability - Availability checking
    ↓
Repositories (Data access)
    ├── StaffRepository
    ├── DutyRepository
    ├── DaysOffRepository
    └── DutyAssignmentRepository
    ↓
Models (Django ORM)
```

## Test Coverage

### 1. test_repositories.py (~80 tests)
Tests for all repository classes:

**TestStaffRepository:**
- CRUD operations (get_all, get_by_id, create, update, delete)
- `update_priority()` with value and diff
- `update_priority()` with Greatest() function (never goes below 0)
- `get_minimum_priority()` 
- `set_minimum_priority_for_all()` - priority normalization

**TestDaysOffRepository:**
- CRUD operations
- `exists_for_user_in_date()` - check if user has day off
- `get_list_of_days_off()` - filter by date range

**TestDutyRepository:**
- CRUD operations
- `get_previous_duty()` - get duty before given date
- `get_list_of_duties()` - filter by date range with prefetch
- `get_first_element_by_date()` - get duty by exact date
- `save_duty_days()` - bulk create/update duties

**TestDutyAssignmentRepository:**
- CRUD operations
- `user_has_assignment_for_duty_id()` - check assignment exists
- `get_list_of_duty_assignment()` - filter by date range
- `get_assignment_by_duty_and_user()` - find specific assignment
- `get_count_by_duty_id()` - count assignments for duty
- `get_users_for_duty()` - get all users assigned to duty

### 2. test_staff_availability.py (~15 tests)
Tests for StaffAvailability service:

**TestStaffAvailability:**
- `is_unavailable()` - main availability check
- `has_days_off()` - check for days off
- `has_previous_duty()` - prevent consecutive assignments
- `has_current_duty()` - check if already assigned to this duty
- Integration tests with multiple unavailability reasons

### 3. test_manage_assignments.py (~20 tests)
Tests for ManageAssignments service:

**TestManageAssignments:**
- `get_duties_by_date()` - retrieve duties for date range
- `create_duty_days()` - bulk create duty days
- `get_duty_assignments()` - retrieve assignments
- `get_date_range()` - extract start/end from dates
- `get_days_off()` - retrieve days off with optional filtering
- `get_all_*()` - get all staff/assignments/duties
- `create_assignment()` - create assignment + update priority
- `update_assignment()` - change user + update both priorities
- `delete_assignment()` - remove assignment
- Atomic transaction tests

### 4. test_planner.py (~15 tests)
Tests for Planner service (schedule generation):

**TestPlanner:**
- `create_plan()` - basic plan generation
- Plan respects days off
- Plan handles insufficient staff
- Plan prevents consecutive assignments
- Priority queue logic (assigns lowest priority first)
- `update_priority()` - update user priority
- `set_minimum_priority()` - normalize all priorities
- `save_messages()` - generate warning messages

**TestPlannerEdgeCases:**
- Plan with no staff available
- Single day planning
- Everyone unavailable scenario

### 5. test_views.py (~35 tests)
Tests for ViewSets (API endpoints):

**TestStaffViewSet:**
- List, create, retrieve, update, delete staff
- Duplicate email validation
- Full name generation

**TestDaysOffViewSet:**
- List with date filtering
- Create, delete days off
- Past date validation
- Duplicate validation

**TestDutyAssignmentViewSet:**
- `list_assignments` action - get schedule for date range
- `generate` action - create schedule
- `assign` action - create/update/delete assignments
- Standard CRUD operations
- Validation tests

**TestViewSetIntegration:**
- Full workflow test

### 6. test_serializers.py (~35 tests)
Tests for serializers and validators (unchanged)

### 7. test_models.py (~30 tests)
Tests for Django models (unchanged)

## Running Tests

```bash
# All tests
make check

# With coverage
make test-coverage

# Specific test file
pytest backend/tests/test_repositories.py

# Specific test class
pytest backend/tests/test_repositories.py::TestStaffRepository

# Specific test
pytest backend/tests/test_repositories.py::TestStaffRepository::test_get_all_empty

# Verbose output
pytest -v

# Stop on first failure
pytest -x

# Show print statements
pytest -s
```

## Fixtures (conftest.py)

- `api_client` - DRF test client
- `staff_user`, `staff_users` - Staff instances
- `today`, `tomorrow`, `yesterday`, `future_date` - Date helpers
- `date_range` - 7-day date range
- `duty_day`, `duty_days` - Duty instances
- `day_off`, `days_off_multiple` - DaysOff instances
- `duty_assignment`, `duty_assignments` - DutyAssignment instances
- `duty_with_assignments` - Duty with 2 assignments

## Test Statistics

- **Total tests**: ~230
- **Repositories**: ~80 tests
- **Services**: ~50 tests
- **Views**: ~35 tests
- **Serializers**: ~35 tests
- **Models**: ~30 tests

## Coverage Goals

- **Repositories**: >90% (critical data layer)
- **Services**: >85% (business logic)
- **Views**: >85% (API layer)
- **Overall**: >85%

## Common Test Patterns

### Testing Repositories
```python
@pytest.mark.django_db
def test_repository_method(repository, staff_user):
    result = repository.get_by_id(staff_user.id)
    assert result.id == staff_user.id
```

### Testing Services
```python
@pytest.mark.django_db  
def test_service_method(service, staff_user):
    result = service.create_assignment(duty_date, user_id)
    assert result.id is not None
    # Check side effects
    staff_user.refresh_from_db()
    assert staff_user.priority > 0
```

### Testing Views
```python
@pytest.mark.django_db
def test_api_endpoint(api_client, staff_user):
    response = api_client.post('/api/users/', data, format='json')
    assert response.status_code == 201
    assert response.data['first_name'] == 'Test'
```

## Notes

1. Tests follow AAA pattern (Arrange, Act, Assert)
2. Each test is independent and can run in isolation
3. Fixtures are reusable across all test files
4. Database is reset between tests automatically