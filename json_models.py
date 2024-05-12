from typing import List
from pydantic import BaseModel, Field

class RequestGenerateVacancy(BaseModel):
    """Class for form request validation to create new generation task

    Args:
        BaseModel (_type_): default pydantic basemodel
    """
    vacancy_name: str = Field(alias='vacancyName')
    company_name: str = Field(alias='companyName', default="")
    company_place: str = Field(alias='companyPlace', default="")
    schedule: str = ""
    experience: str = ""
    key_skills: List[str] = Field(alias='keySkills', default=[])
    token: str
    
class RequestCheckStatus(BaseModel):
    """Class for check-answer request validation to check current task status

    Args:
        BaseModel (_type_): default pydantic basemodel
    """
    token: str
