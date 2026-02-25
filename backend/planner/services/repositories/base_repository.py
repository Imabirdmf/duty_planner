from typing import Generic, Type, TypeVar

from django.db import models

T = TypeVar("T", bound=models.Model)


class BaseRepository(Generic[T]):
    model: Type[T]

    def get_all(self):
        return self.model.objects.all()

    def get_by_id(self, obj_id: int) -> T:
        return self.model.objects.get(id=obj_id)

    def create(self, **kwargs) -> T:
        return self.model.objects.create(**kwargs)

    def update(self, obj_id: int, **kwargs) -> T:
        obj = self.get_by_id(obj_id)
        for k, v in kwargs.items():
            setattr(obj, k, v)
        obj.save()
        return obj

    def delete(self, obj_id: int) -> None:
        obj = self.get_by_id(obj_id)
        obj.delete()
