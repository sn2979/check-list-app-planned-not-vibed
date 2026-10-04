from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import Session

from checklist import dao
from checklist.model import Checklist
from checklist.schema import ChecklistCreate, ChecklistDetail, ChecklistRead, ChecklistUpdate
from database import SessionDep

router = APIRouter(prefix="/checklists", tags=["checklists"])


def _get_checklist_or_404(session: Session, checklist_id: int) -> Checklist:
    checklist = dao.get_checklist(session, checklist_id)
    if checklist is None:
        raise HTTPException(404, "Checklist not found")
    return checklist


@router.get("", response_model=list[ChecklistRead])
def list_checklists(session: SessionDep):
    return dao.list_checklists(session)


@router.post("", response_model=ChecklistRead, status_code=201)
def create_checklist(body: ChecklistCreate, session: SessionDep):
    checklist = dao.create_checklist(session, body.name)
    session.commit()
    return checklist


@router.get("/{checklist_id}", response_model=ChecklistDetail)
def get_checklist(checklist_id: int, session: SessionDep):
    checklist = dao.get_checklist_contents(session, checklist_id)
    if checklist is None:
        raise HTTPException(404, "Checklist not found")
    return checklist


@router.patch("/{checklist_id}", response_model=ChecklistRead)
def update_checklist(checklist_id: int, body: ChecklistUpdate, session: SessionDep):
    checklist = _get_checklist_or_404(session, checklist_id)
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(checklist, field, value)
    session.commit()
    return checklist


@router.delete("/{checklist_id}", status_code=204)
def delete_checklist(checklist_id: int, session: SessionDep):
    checklist = _get_checklist_or_404(session, checklist_id)
    dao.delete_checklist(session, checklist)
    session.commit()


@router.post("/{checklist_id}/copy", response_model=ChecklistDetail, status_code=201)
def copy_checklist(checklist_id: int, session: SessionDep):
    original = dao.get_checklist_contents(session, checklist_id, include_file_content=True)
    if original is None:
        raise HTTPException(404, "Checklist not found")
    new = original.copy()
    session.add(new)
    session.commit()
    return new
