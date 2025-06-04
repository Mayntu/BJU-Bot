from tortoise.fields import (
    CharField,
    BigIntField,
    FloatField,
    DecimalField,
    DatetimeField,
    DateField,
    UUIDField,
    IntField,

    ForeignKeyField,
)
from tortoise.models import Model
from uuid import uuid4

from bot.config import YOOKASSA_PAYMENT_STATUS


class User(Model):
    id = BigIntField(pk=True)
    username = CharField(max_length=255, unique=True)
    timezone = CharField(max_length=64, default="UTC")
    meal_count = IntField(default=0)
    # subscription = CharField(max_length=32, default="free")

    created_at = DatetimeField(auto_now_add=True)

    def __str__(self):
        return f"telegram id: {self.id}"

    class Meta:
        table = "users"


class Meal(Model):
    id = UUIDField(pk=True, default=uuid4)
    user = ForeignKeyField("models.User", related_name="meals")
    name = CharField(max_length=255)
    total_weight = FloatField()
    total_calories = FloatField()
    total_protein = FloatField()
    total_fat = FloatField()
    total_carbs = FloatField()
    total_fiber = FloatField()

    created_at = DatetimeField(auto_now_add=True)

    def __str__(self):
        return self.name        
    
    class Meta:
        table = "meals"


class Ingredient(Model):
    id = UUIDField(pk=True, default=uuid4)
    meal = ForeignKeyField("models.Meal", related_name="ingredients")
    name = CharField(max_length=255)
    weight = FloatField()
    calories = FloatField()
    protein = FloatField()
    fat = FloatField()
    carbs = FloatField()
    fiber = FloatField()

    created_at = DatetimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    
    class Meta:
        table = "ingredients"


class UserDailyReport(Model):
    id = UUIDField(pk=True, default=uuid4)
    user = ForeignKeyField("models.User", related_name="daily_reports")
    date = DateField()

    meal_name = CharField(max_length=255, null=True)
    
    total_weight = FloatField()
    total_calories = FloatField()
    total_protein = FloatField()
    total_fat = FloatField()
    total_carbs = FloatField()
    total_fiber = FloatField()

    created_at = DatetimeField(auto_now_add=True)
    updated_at = DatetimeField(auto_now=True)

    class Meta:
        table = "user_daily_reports"
        unique_together = ("user", "date")


class UserDailyMeal(Model):
    id = UUIDField(pk=True, default=uuid4)
    user = ForeignKeyField("models.User", related_name="daily_meals")
    date = DateField()
    
    name = CharField(max_length=255)
    calories = FloatField()
    order = IntField()

    created_at = DatetimeField(auto_now_add=True)

    class Meta:
        table = "user_daily_meals"
        indexes = [("user", "date")]


class UserSubscription(Model):
    id = UUIDField(pk=True, default=uuid4)
    user = ForeignKeyField("models.User", related_name="subscriptions")
    plan = CharField(max_length=32)
    price = DecimalField(max_digits=10, decimal_places=2)
    currency = CharField(max_length=32, default="RUB")
    start_date = DateField()
    end_date = DateField(null=True)

    created_at = DatetimeField(auto_now_add=True)

    class Meta:
        table = "user_subscriptions"
        indexes = [("user", "plan")]


class Payment(Model):
    id = UUIDField(pk=True, default=uuid4)
    user = ForeignKeyField("models.User", related_name="payments")
    user_subscription = ForeignKeyField("models.UserSubscription", related_name="payments")
    status = CharField(max_length=32, default=YOOKASSA_PAYMENT_STATUS.PENDING.value)  # pending, succeeded, canceled
    yookassa_payment_id = CharField(max_length=64, null=True, unique=True)

    created_at = DatetimeField(auto_now_add=True)

    class Meta:
        table = "payments"
        unique_together = ("user", "created_at")
