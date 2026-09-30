from sqlalchemy.orm import Session
from app.db.session import get_db

def get_current_user(db: Session = Depends(get_db)):
    # Basic dependency for now, can be expanded to full auth
    pass
