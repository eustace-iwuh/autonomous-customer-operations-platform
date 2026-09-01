from typing import Any

from sqlalchemy.orm import Session

from backend.database.models import Case
from backend.domain.states import CasePriority, CaseStatus, validate_transition
from backend.services.event_service import EventService


class CaseService:
    def __init__(self, db: Session):
        self.db = db
        self.event_service = EventService(db)

    def create_case(
        self,
        *,
        case_number: str,
        customer_id: int,
        title: str,
        description: str,
        priority: CasePriority = CasePriority.MEDIUM,
    ) -> Case:
        case = Case(
            case_number=case_number,
            customer_id=customer_id,
            title=title,
            description=description,
            priority=priority.value,
            status=CaseStatus.RECEIVED.value,
        )

        self.db.add(case)
        self.db.flush()

        self.event_service.record(
            case_id=case.id,
            event_type="CASE_CREATED",
            actor_type="SYSTEM",
            description="Case created by the operations platform.",
            payload={
                "case_number": case.case_number,
                "priority": case.priority,
            },
        )

        return case

    def get_case(self, case_id: int) -> Case | None:
        return self.db.query(Case).filter(Case.id == case_id).first()

    def list_cases(self) -> list[Case]:
        return self.db.query(Case).order_by(Case.created_at.desc()).all()

    def transition_case(
        self,
        *,
        case_id: int,
        target_status: CaseStatus,
        actor_type: str = "SYSTEM",
        description: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> Case:
        case = self.get_case(case_id)

        if case is None:
            raise ValueError(f"Case not found: {case_id}")

        current_status = CaseStatus(case.status)

        validate_transition(
            current=current_status,
            target=target_status,
        )

        previous_status = case.status
        case.status = target_status.value

        self.db.flush()

        self.event_service.record(
            case_id=case.id,
            event_type="CASE_STATUS_CHANGED",
            actor_type=actor_type,
            description=(
                description
                or f"Case status changed from "
                f"{previous_status} to {target_status.value}."
            ),
            payload={
                "previous_status": previous_status,
                "new_status": target_status.value,
                **(payload or {}),
            },
        )

        return case
