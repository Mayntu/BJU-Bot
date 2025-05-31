from aiogram.fsm.state import State, StatesGroup

class FoodAnalyzeState(StatesGroup):
    """
    Состояния для анализа еды
    """
    # Состояние редактирования блюда
    editing : State = State()
