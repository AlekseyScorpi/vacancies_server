# This is the server for the vacancies generation system
## About this server
This server works in pair with front-end part https://github.com/AlekseyScorpi/vacancies_site
It allows you to generate job texts at the request of users based on the form they submitted.
To generate text, the server uses a large language model. Model is finetuned Saiga3 - https://huggingface.co/AlekseyScorpi/saiga_llama3_vacancies_lora
## Installation
* You need to download any saiga_llama3_vacanices GGUF model from https://huggingface.co/AlekseyScorpi/saiga_llama3_vacancies_GGUF
* Next you have to set model_config.json for your purpose or you can use my default config
* You need set several environments variables in .env file (create it):
  * NGROK_AUTH_TOKEN
  * NGROK_SERVER_DOMAIN
  * FLASK_PORT
  * CLIENT_DOMAIN
### Docker way
* You should be sure that you have the nvidia container toolkit installed to work with cuda inside containers
* Just build docker container with ```docker build -t {YOUR_IMAGE_NAME} . ```
* Run it 😉 , example run script ```docker run --gpus all -p 80:80 vacancies-server-saiga3```

### Default python way
* First, create new virtual environment and activate it
* Second, set new environment variable ```ENV CMAKE_ARGS="-DLLAMA_CUDA=on"``` to build llama_cpp_python with CUDA (be sure, that you have CUDA Toolkit on your device)
* Then ```run pip install -r requirements.txt```
* Now you can run your server with ```python start.py```
