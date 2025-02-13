from pydantic import BaseModel
from datetime import date

class AthleteBase(BaseModel):
    last_name: str
    first_name: str
    gender: str
    birth_date: date
    coach_id: int

class AthleteCreate(AthleteBase):
    pass

class AthleteResponse(AthleteBase):
    id: int

    class Config:
        from_attributes = True

class CoachBase(BaseModel):
    last_name: str
    first_name: str
    credentials: str

class CoachCreate(CoachBase):
    pass

class CoachResponse(CoachBase):
    id: int

    class Config:
        from_attributes = True

class CategoryBase(BaseModel):
    name: str
    age_group: str
    gender: str

class CategoryCreate(CategoryBase):
    pass

class CategoryResponse(CategoryBase):
    id: int

    class Config:
        from_attributes = True

class TournamentBase(BaseModel):
    name: str
    location: str
    start_date: date
    end_date: date
    registration_start_date: date
    registration_end_date: date

class TournamentCreate(TournamentBase):
    pass

class TournamentResponse(TournamentBase):
    id: int

    class Config:
        from_attributes = True
