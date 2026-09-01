from typing import Any

from sqlalchemy.orm import Session

from backend.database.models import CaseEvent


class EventService:
    def __init__(self, db: Session):
        self.db = db

    def record(
        self,
        *,
        case_id: int,
        event_type: str,
        actor_type: str,
        description: str,
        payload: dict[str, Any] | None = None,
    ) -> CaseEvent:
        event = CaseEvent(
            case_id=case_id,
            event_type=event_type,
            actor_type=actor_type,
            description=description,
            payload=payload or {},
        )

        self.db.add(event)
        self.db.flush()

        return event