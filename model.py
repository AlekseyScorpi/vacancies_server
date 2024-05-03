import os
from typing import List
from model_config import ModelConfig
from ctransformers import AutoModelForCausalLM

class Model:
    
    def __init__(self, model_config: ModelConfig):
        model_path = os.path.join(model_config.model_folder, model_config.model_file)
        
        self._model = AutoModelForCausalLM.from_pretrained(
            model_path,
            gpu_layers=model_config.gpu_layers,
            context_length=model_config.context_length,
            max_new_tokens=model_config.max_new_tokens,
            threads=model_config.threads
        )
        self._system_prompt = model_config.system_prompt
        
    def _create_prompt(self, request):
        prompt = f'''<|im_start|>system
{self._system_prompt}<|im_end|>
<|im_start|>user
{request}<|im_end|>
<|im_start|>assistant'''

        return prompt

    def generate(
        self,
        vacancy_name,
        company_name="",
        company_place="",
        schedule="",
        experience="",
        key_skills: List[str]=[],
    ):
        
        capitalize_skills = [f"'{skill.capitalize()}'" for skill in key_skills]
        
        request = (f'Напиши текст вакансии для должности "{vacancy_name}". Название компании: "{company_name}". ',
                   f'Расположение: {company_place}. График работы: {schedule}. Опыт работы: {experience}. ',
                   f'Ключевые навыки: {", ".join(capitalize_skills)}')
        
        prompt = self._create_prompt(request=request)
        
        outputs = self._model(prompt)

        while '<|im_end|>' in outputs:
            outputs = outputs.replace('<|im_end|>', '')
        while '<|im_start|>' in outputs:
            outputs = outputs.replace('<|im_start|>', '')
        while ';' in outputs:
            outputs = outputs.replace(';', '\n')
        
        return outputs