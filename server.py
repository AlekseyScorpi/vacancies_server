from typing import Dict, List, Set
from flask import Flask, jsonify, request
from json_models import RequestCheckStatus, RequestGenerateVacancy
from pydantic import ValidationError
from model import Model
from model_config import ModelConfig
import json
import threading
import time

# app instance
app = Flask(__name__)

# json schemas
with open('schemas.json') as f:
    schemas = json.load(f)

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

task_queue: List[RequestGenerateVacancy] = []
processing_tasks: Set[str] = set()
result_pool: Dict[str, str] = {}
queue_lock = threading.Lock()
processing_lock = threading.Lock()
result_lock = threading.Lock()



def process_task():
    while True:
        with queue_lock:
            task = task_queue.pop(0) if task_queue else None
        
        if task:
            result = process_task_logic(task)
            with result_lock:
                result_pool[task.token] = result
            with processing_lock:
                processing_tasks.remove(task.token)
        else:
            time.sleep(1)
            

def process_task_logic(task: RequestGenerateVacancy) -> str:
    with processing_lock:
        processing_tasks.add(task.token)
        
    answer: str = model.generate(
        vacancy_name=task.vacancy_name,
        company_name=task.company_name,
        company_place=task.company_place,
        schedule=task.schedule,
        experience=task.experience,
        key_skills=task.key_skills,
    )
    return answer

@app.route("/api/check-answer", methods=['POST'])
def check_answer_status():
    try:
        data = request.json
        
        if (type(data)) == dict:
            data = json.dumps(data)
        
        check_request = RequestCheckStatus.model_validate_json(data)
        
        token = check_request.token
        
        with result_lock:
            if token in result_pool:
                answer = result_pool[token]
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
    try:
        data = request.json

        if type(data) == dict:
            data = json.dumps(data)

        generate_request = RequestGenerateVacancy.model_validate_json(data)
        
        with queue_lock:
            task_queue.append(generate_request)
        
        response_message = {'message': 'OK'}
        return jsonify(response_message), 200
    
    except ValidationError as e:
        error_response = {'message': 'BAD', 'content': 'Invalid JSON format: ' + str(e)}
        return jsonify(error_response), 400


@app.route("/api/home", methods=['GET'])
def return_home():
    return jsonify({
        'description': str(model._model)
    })

def start_task_processing():
    global thread
    thread = threading.Thread(target=process_task)
    thread.daemon = True
    thread.start()

if __name__ == "__main__":
    
    start_task_processing()
    
    app.run(port=80)
