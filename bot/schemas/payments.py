from pydantic import BaseModel

class CreatePaymentTicketResponse(BaseModel):
    """
    Ответ API для создания платежного тикета.
    
    :param confirmation_url: URL для подтверждения платежа
    :param payment_id: ID платежа
    """
    confirmation_url: str
    payment_id : str