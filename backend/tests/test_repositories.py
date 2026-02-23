"""
Тесты для репозиториев (слой доступа к данным)
"""

import pytest
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError
from planner.models import Staff

# Предполагаем, что StaffRepository находится в planner/repositories.py
# Если путь другой, измените импорт соответственно


from planner.services.repositories.staff_repository import StaffRepository


@pytest.mark.django_db
class TestStaffRepository:
    """Тесты для StaffRepository"""

    @pytest.fixture
    def repository(self):
        """Создает экземпляр репозитория"""
        return StaffRepository()

    def test_get_all_empty(self, repository):
        """Тест получения всех сотрудников когда БД пуста"""
        result = repository.get_all()

        assert result.count() == 0
        assert list(result) == []

    def test_get_all_with_data(self, repository, staff_users):
        """Тест получения всех сотрудников"""
        result = repository.get_all()

        assert result.count() == len(staff_users)
        assert set(result) == set(staff_users)

    def test_get_by_id_success(self, repository, staff_user):
        """Тест получения сотрудника по ID"""
        result = repository.get_by_id(staff_user.id)

        assert result == staff_user
        assert result.id == staff_user.id
        assert result.email == staff_user.email

    def test_get_by_id_not_found(self, repository):
        """Тест получения несуществующего сотрудника"""
        with pytest.raises(Staff.DoesNotExist):
            repository.get_by_id(99999)

    def test_create_staff(self, repository):
        """Тест создания нового сотрудника"""
        data = {
            "first_name": "Тест",
            "last_name": "Тестов",
            "email": "test@example.com",
            "priority": 0,
        }

        result = repository.create(**data)

        assert result.id is not None
        assert result.first_name == "Тест"
        assert result.last_name == "Тестов"
        assert result.email == "test@example.com"
        assert result.priority == 0
        assert Staff.objects.count() == 1

    def test_create_staff_minimal_fields(self, repository):
        """Тест создания сотрудника с минимальными полями"""
        data = {
            "first_name": "Тест",
            "last_name": "Тестов",
            "email": "test@example.com",
        }

        result = repository.create(**data)

        assert result.id is not None
        assert result.priority == 0  # default value

    def test_create_staff_duplicate_email(self, repository, staff_user):
        """Тест создания сотрудника с дублирующимся email"""
        data = {
            "first_name": "Другой",
            "last_name": "Человек",
            "email": staff_user.email,  # дублирующийся email
        }

        with pytest.raises(IntegrityError):
            repository.create(**data)

    def test_update_staff(self, repository, staff_user):
        """Тест обновления сотрудника"""
        updates = {
            "first_name": "Обновленный",
            "last_name": "Пользователь",
            "priority": 5,
        }

        result = repository.update(staff_user.id, **updates)

        assert result.id == staff_user.id
        assert result.first_name == "Обновленный"
        assert result.last_name == "Пользователь"
        assert result.priority == 5

        # Проверяем что изменения сохранены в БД
        staff_user.refresh_from_db()
        assert staff_user.first_name == "Обновленный"
        assert staff_user.last_name == "Пользователь"
        assert staff_user.priority == 5

    def test_update_staff_partial(self, repository, staff_user):
        """Тест частичного обновления сотрудника"""
        original_last_name = staff_user.last_name

        updates = {"first_name": "Новое"}

        result = repository.update(staff_user.id, **updates)

        assert result.first_name == "Новое"
        assert result.last_name == original_last_name  # Не изменилось

    def test_update_nonexistent_staff(self, repository):
        """Тест обновления несуществующего сотрудника"""
        with pytest.raises(Staff.DoesNotExist):
            repository.update(99999, first_name="Test")

    def test_delete_staff(self, repository, staff_user):
        """Тест удаления сотрудника"""
        staff_id = staff_user.id

        repository.delete(staff_id)

        assert Staff.objects.count() == 0
        assert not Staff.objects.filter(id=staff_id).exists()

    def test_delete_nonexistent_staff(self, repository):
        """Тест удаления несуществующего сотрудника"""
        with pytest.raises(Staff.DoesNotExist):
            repository.delete(99999)

    def test_delete_cascades_to_related_objects(
        self, repository, staff_user, day_off, duty_assignment
    ):
        """Тест что удаление сотрудника каскадно удаляет связанные объекты"""
        from planner.models import DaysOff, DutyAssignment

        staff_id = staff_user.id

        # Проверяем что связанные объекты существуют
        assert DaysOff.objects.filter(user=staff_user).exists()
        assert DutyAssignment.objects.filter(user=staff_user).exists()

        repository.delete(staff_id)

        # Проверяем что связанные объекты удалены
        assert not DaysOff.objects.filter(user_id=staff_id).exists()
        assert not DutyAssignment.objects.filter(user_id=staff_id).exists()


@pytest.mark.django_db
class TestStaffRepositoryEdgeCases:
    """Тесты граничных случаев для StaffRepository"""

    @pytest.fixture
    def repository(self):
        return StaffRepository()

    def test_update_with_empty_dict(self, repository, staff_user):
        """Тест обновления с пустым словарем изменений"""
        original_first_name = staff_user.first_name

        result = repository.update(staff_user.id, **{})

        # Ничего не должно измениться
        assert result.first_name == original_first_name

    def test_get_all_returns_queryset(self, repository, staff_users):
        """Тест что get_all возвращает QuerySet"""
        result = repository.get_all()

        # Проверяем что это QuerySet
        assert hasattr(result, "filter")
        assert hasattr(result, "count")
        assert hasattr(result, "order_by")

    def test_update_email_to_duplicate(self, repository, staff_users):
        """Тест обновления email на дублирующийся"""
        staff1 = staff_users[0]
        staff2_email = staff_users[1].email

        with pytest.raises(IntegrityError):
            repository.update(staff1.id, email=staff2_email)

    def test_create_update_delete_flow(self, repository):
        """Тест полного жизненного цикла: создание -> обновление -> удаление"""
        # Создание
        staff = repository.create(
            first_name="Тест", last_name="Тестов", email="test@example.com"
        )
        assert Staff.objects.count() == 1

        # Обновление
        updated = repository.update(staff.id, first_name="Обновленный")
        assert updated.first_name == "Обновленный"
        assert Staff.objects.count() == 1

        # Удаление
        repository.delete(staff.id)
        assert Staff.objects.count() == 0

    def test_update_all_fields(self, repository, staff_user):
        """Тест обновления всех полей сразу"""
        updates = {
            "first_name": "Новое",
            "last_name": "Имя",
            "email": "new@example.com",
            "priority": 10,
        }

        result = repository.update(staff_user.id, **updates)

        assert result.first_name == "Новое"
        assert result.last_name == "Имя"
        assert result.email == "new@example.com"
        assert result.priority == 10


@pytest.mark.django_db
class TestStaffRepositoryIntegration:
    """Интеграционные тесты для StaffRepository"""

    @pytest.fixture
    def repository(self):
        return StaffRepository()

    def test_repository_works_with_api(self, repository, api_client):
        """Тест что репозиторий корректно работает с API"""
        # Создаем через репозиторий
        staff = repository.create(
            first_name="Тест", last_name="Тестов", email="test@example.com"
        )

        # Получаем через API
        response = api_client.get(f"/api/users/{staff.id}/")

        assert response.status_code == 200
        assert response.data["first_name"] == "Тест"
        assert response.data["email"] == "test@example.com"

    def test_multiple_repositories_same_data(self):
        """Тест что несколько экземпляров репозитория работают с одними данными"""
        repo1 = StaffRepository()
        repo2 = StaffRepository()

        staff = repo1.create(
            first_name="Тест", last_name="Тестов", email="test@example.com"
        )

        # Второй репозиторий должен видеть данные первого
        result = repo2.get_by_id(staff.id)
        assert result.first_name == "Тест"

        # Обновление через второй репозиторий
        repo2.update(staff.id, first_name="Обновленный")

        # Первый репозиторий должен видеть изменения
        updated = repo1.get_by_id(staff.id)
        assert updated.first_name == "Обновленный"

    def test_repository_with_transactions(self, repository):
        """Тест работы репозитория с транзакциями"""
        from django.db import transaction

        try:
            with transaction.atomic():
                staff = repository.create(
                    first_name="Тест", last_name="Тестов", email="test@example.com"
                )

                # Искусственно вызываем ошибку
                raise Exception("Rollback test")
        except Exception:
            pass

        # Проверяем что данные откатились
        assert Staff.objects.count() == 0

    def test_repository_bulk_operations(self, repository):
        """Тест массовых операций через репозиторий"""
        # Создаем несколько сотрудников
        staff_list = []
        for i in range(5):
            staff = repository.create(
                first_name=f"Тест{i}",
                last_name=f"Тестов{i}",
                email=f"test{i}@example.com",
            )
            staff_list.append(staff)

        # Получаем всех
        all_staff = repository.get_all()
        assert all_staff.count() == 5

        # Обновляем всех
        for staff in staff_list:
            repository.update(staff.id, priority=10)

        # Проверяем обновления
        all_staff = repository.get_all()
        for staff in all_staff:
            assert staff.priority == 10

        # Удаляем всех
        for staff in staff_list:
            repository.delete(staff.id)

        assert Staff.objects.count() == 0


@pytest.mark.django_db
class TestStaffRepositoryWithRelatedObjects:
    """Тесты репозитория с учетом связанных объектов"""

    @pytest.fixture
    def repository(self):
        return StaffRepository()

    def test_get_staff_with_days_off(self, repository, staff_user, day_off):
        """Тест получения сотрудника у которого есть выходные"""
        staff = repository.get_by_id(staff_user.id)

        # Проверяем что можем получить связанные выходные
        days_off = staff.daysoff_set.all()
        assert days_off.count() == 1
        assert days_off.first() == day_off

    def test_get_staff_with_duty_assignments(
        self, repository, staff_user, duty_assignment
    ):
        """Тест получения сотрудника у которого есть назначения"""
        staff = repository.get_by_id(staff_user.id)

        # Проверяем что можем получить связанные назначения
        assignments = staff.dutyassignment_set.all()
        assert assignments.count() == 1
        assert assignments.first() == duty_assignment

    def test_update_staff_preserves_related_objects(
        self, repository, staff_user, day_off, duty_assignment
    ):
        """Тест что обновление сотрудника сохраняет связанные объекты"""
        staff_id = staff_user.id

        # Обновляем сотрудника
        repository.update(staff_id, first_name="Обновленный")

        # Проверяем что связанные объекты сохранились
        from planner.models import DaysOff, DutyAssignment

        assert DaysOff.objects.filter(user_id=staff_id).exists()
        assert DutyAssignment.objects.filter(user_id=staff_id).exists()
