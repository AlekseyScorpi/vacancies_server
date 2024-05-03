class ModelConfig:
    def __init__(
        self,
        model_folder,
        model_file,
        gpu_layers=0,
        threads=-1,
        context_length=-1,
        max_new_tokens=1024,
        system_prompt="Пожалуйста, отвечайте на русском языке. Ты полезный ассистент, твоя задача помогать компаниям с созданием интересного и необычного текста вакансий. Если какой-то пункт пустой, то не добавляй его в свой ответ. Если что-то не указано или ты в чём то не уверен, то не придумывай ничего лишнего, лучше промолчи, однако, если ты считаешь, что некоторые требования необходимы для данной должности, добавь их."
    ) -> None:
        self.model_folder = model_folder
        self.model_file = model_file
        self.gpu_layers = gpu_layers
        self.threads = threads
        self.context_length = context_length
        self.max_new_tokens = max_new_tokens
        self.system_prompt = system_prompt