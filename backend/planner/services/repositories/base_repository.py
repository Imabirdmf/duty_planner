from django.db import models


class BaseRepository[T: models.Model]:
    model: type[T]
    default_ordering: str | None = None

    def __init__(self):
        if self.model is None:
            raise NotImplementedError(
                f"{self.__class__.__name__} must set 'model' attribute"
            )

    def get_all(self):
        qs = self.model.objects.all()
        return qs.order_by(self.default_ordering) if self.default_ordering else qs

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
