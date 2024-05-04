from typing import List
from pydantic import BaseModel, Field

class RequestGenerateVacancy(BaseModel):
    vacancy_name: str = Field(alias='vacancyName')
    company_name: str = Field(alias='cityFullName', default="")
    company_place: str = Field(alias='companyPlace', default="")
    schedule: str = ""
    experience: str = ""
    key_skills: List[str] = Field(alias='keySkills', default=[])
    token: str
    
class RequestCheckStatus(BaseModel):
    token: str
