from typing import Dict, List, Set
from flask import Flask, jsonify, request
from flask_cors import CORS
from json_models import RequestCheckStatus, RequestGenerateVacancy
from pydantic import ValidationError
from model import Model
from model_config import ModelConfig
import json
import threading
import time
import dotenv
import os

# environment variables load
dotenv.load_dotenv()
# port for flask server
port = os.getenv('FLASK_PORT')
# client domain (need to CORS policy)
client_domain = os.getenv('CLIENT_DOMAIN')

# app instance
app = Flask(__name__)
# set CORS policy
CORS(app, origins=[client_domain if client_domain else "/", "http://localhost:3000"])

# config instance
config = ModelConfig(
        model_folder="generation_model",
        model_file="model-Q5_K_M.gguf",
        gpu_layers=10,
        threads=8,
        context_length=2800,
        max_new_tokens=2048,
)

# model instance
model = Model(config)

# queue for waiting tasks
task_queue: List[RequestGenerateVacancy] = []
# tasks which is currently processing by model
processing_tasks: Set[str] = set()
# result pool
result_pool: Dict[str, Dict[str, str | float]] = {}
# mutex for tasks queue
queue_lock = threading.Lock()
# mutex for processing tasks
processing_lock = threading.Lock()
# mutex for result pool
result_lock = threading.Lock()

# time, before the task is removed from the result pool if it is not requested to receive 
MAX_CACHE_TIME = 60


def process_task():
    """Main function to manage tasks
    """
    while True:
        with result_lock:
            del_tokens=[]
            for token in result_pool:
                if time.time() - result_pool[token]['timestamp'] > MAX_CACHE_TIME: # type: ignore
                    del_tokens.append(token)
            for token in del_tokens:
                del result_pool[token]
        
        with queue_lock:
            task = task_queue.pop(0) if task_queue else None
        
        if task:
            try:
                result = process_task_logic(task)
                with result_lock:
                    result_pool[task.token] = {'content': result, 'timestamp': time.time()}
            except(RuntimeError):
                print(f"{'%Y-%m-%d %H:%M:%S', time.localtime()} Task by token={task.token} cannot be completed, unexpected error occured")
            with processing_lock:
                processing_tasks.remove(task.token)
        else:
            time.sleep(1)
            

def process_task_logic(task: RequestGenerateVacancy) -> str:
    """This function send request to the model and return model request output

    Args:
        task (RequestGenerateVacancy): Request from user

    Raises:
        RuntimeError: raise RuntimeError if RuntimeError from model occured

    Returns:
        str: generated vacancy text
    """
    with processing_lock:
        processing_tasks.add(task.token)
        
    try:
        answer: str = model.generate(
        vacancy_name=task.vacancy_name,
        company_name=task.company_name,
        company_place=task.company_place,
        schedule=task.schedule,
        experience=task.experience,
        key_skills=task.key_skills,
    )
    except(RuntimeError):
        raise RuntimeError("Model generation error occured")
    return answer

@app.route("/api/check-answer", methods=['POST'])
def check_answer_status():
    """Flask route function. Using for check task status and return position or position/vacancy_text to client

    Returns:
        json: json which contains message and content fields
    """
    try:
        data = request.json
        
        if (type(data)) == dict:
            data = json.dumps(data)
        
        check_request = RequestCheckStatus.model_validate_json(data) # type: ignore
        
        token = check_request.token
        
        with result_lock:
            if token in result_pool:
                answer = result_pool[token]['content']
                response = {'message': 'GOOD', 'content': answer}
                del result_pool[token]
                return jsonify(response), 200
        
        with processing_lock:
            if token in processing_tasks:
                response = {'message': 'OK', 'content': 0}
                return jsonify(response), 200
        
        with queue_lock:
            for i, task in enumerate(task_queue):
                if token == task.token:
                    response = {'message': 'OK', 'content': i + 1}
                    return jsonify(response), 200
        
        return jsonify({
            'message': 'OK',
            'content': -1
        })
        
    except ValidationError as e:
        error_response = {'message': 'BAD', 'content': 'Invalid JSON format: ' + str(e)}
        return jsonify(error_response), 400


@app.route("/api/generate", methods=['POST'])
def create_task():
    """Flask route function. Using for create new task based on user form request

    Returns:
        json: return json, which contains user request status
    """
    try:
        data = request.json

        if type(data) == dict:
            data = json.dumps(data)

        generate_request = RequestGenerateVacancy.model_validate_json(data) # type: ignore
        
        with queue_lock:
            task_queue.append(generate_request)
        
        response_message = {'message': 'OK'}
        return jsonify(response_message), 200
    
    except ValidationError as e:
        error_response = {'message': 'BAD', 'content': 'Invalid JSON format: ' + str(e)}
        return jsonify(error_response), 400
    

def start_task_processing():
    """Function to start new thread for tasks manage
    """
    global thread
    thread = threading.Thread(target=process_task)
    thread.daemon = True
    thread.start()

if __name__ == "__main__":
    """Start flask server
    """
    start_task_processing()
    app.run(port=int(port)) if port else app.run(port=80)
