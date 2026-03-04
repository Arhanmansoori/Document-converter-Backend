from sqlalchemy.orm import Session
from models import FileConversion


def save_conversion(db: Session, original_filename: str, original_path: str, converted_path: str, conversion_type: str):
    conversion = FileConversion(
        original_filename=original_filename,
        original_path=original_path,
        converted_path=converted_path,
        conversion_type=conversion_type
    )
    db.add(conversion)
    db.commit()
    db.refresh(conversion)
    return conversion

def get_conversion_by_id(db: Session, conversion_id: int):
    from models import FileConversion
    return db.query(FileConversion).filter(FileConversion.id == conversion_id).first()


#-----------------latest--------------------------#



def get_latest_conversion(db: Session):
    return db.query(FileConversion).order_by(FileConversion.id.desc()).first()
