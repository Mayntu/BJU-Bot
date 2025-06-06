from aiogram.fsm.state import State, StatesGroup

class GoalState(StatesGroup):
    """
    Состояния для установки цели
    """
    waiting_for_goal : State = State()