from pydantic import BaseModel, Field
from typing import List


class IngredientAnalysis(BaseModel):
    """
    Модель для анализа ингредиента блюда.
    """
    name: str = Field(..., description="Название ингредиента")
    weight: float = Field(..., description="Вес в граммах")
    calories: float = Field(..., description="Калории")
    protein: float = Field(..., description="Белки")
    fat: float = Field(..., description="Жиры")
    carbs: float = Field(..., description="Углеводы")
    fiber: float = Field(..., description="Клетчатка")


class MealAnalysis(BaseModel):
    """
    Модель для анализа блюда.
    """
    title: str = Field(..., description="Название блюда")
    total_weight: float = Field(..., description="Общий вес блюда")
    calories: float = Field(..., description="Общая калорийность")
    proteins: float = Field(..., description="Общее количество белков")
    fats: float = Field(..., description="Общее количество жиров")
    carbs: float = Field(..., description="Общее количество углеводов")
    fiber: float = Field(..., description="Общее количество клетчатки")
    ingredients: List[IngredientAnalysis] = Field(..., description="Список ингредиентов")
