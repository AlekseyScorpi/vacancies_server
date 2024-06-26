from typing import Dict, List, Set, Union
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO, disconnect
from schemas import RequestUserConnect, RequestGenerateVacancy, ModelConfig
from pydantic import ValidationError
from model import Model
import json
import threading
import time
import dotenv
import os
import logging

# environment variables load
dotenv.load_dotenv()
# port for flask server
port = int(os.getenv('FLASK_PORT', default=8080))
# client domain (need to CORS policy)
client_domain = os.getenv('CLIENT_DOMAIN', default="/")

# app instance
app = Flask(__name__)
# set socketIO
socketio = SocketIO(app, cors_allowed_origins=[client_domain, "http://localhost:3000"])
# set CORS policy
CORS(app, origins=[client_domain, "http://localhost:3000"])

# queue for waiting tasks
task_queue: List[RequestGenerateVacancy] = []
# tasks which is currently processing by model
processing_tasks: Set[str] = set()
# result pool
result_pool: Dict[str, Dict[str, Union[str, float]]] = {}
# users pool
user_pool: Dict[str, str] = {}
# mutex for tasks queue
queue_lock = threading.Lock()
# mutex for processing tasks
processing_lock = threading.Lock()
# mutex for result pool
result_lock = threading.Lock()
# mutex for user pool
user_lock = threading.Lock()

# condition for update info about current positions
condition = threading.Condition()

# time, before the task is removed from the result pool if it is not requested to receive 
MAX_CACHE_TIME = 10
# event name for update, this name also should be using on client to correctly read socket
UPDATE_EVENT_NAME = 'queue_update'


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
                logging.warning(f"Task by token {token} was deleted due to the expiration cache time")
                del result_pool[token]
        
        with queue_lock:
            task = task_queue.pop(0) if task_queue else None
        
        if task:
            try:
                result = process_task_logic(task)
                with result_lock:
                    result_pool[task.token] = {'content': result, 'timestamp': time.time()}
            except(RuntimeError):
                logging.error(f"Task by token={task.token} cannot be completed, unexpected error occured")
            with processing_lock:
                processing_tasks.remove(task.token)
            send_position_info()
        else:
            time.sleep(1)
            

def send_position_info():
    """Function to send update info about new positions to all users (*connected users)
    """
    with user_lock:
        for sid in user_pool:
            update_queue_position(sid, user_pool[sid])

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
    
    send_position_info()
        
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

        
@socketio.on('user_connect')
def handle_user_connect(data):
    """Function for create a new user for its task by his SID and token

    Args:
        data (dict): dictionary which can be validate as RequestUserConnect with task token
    """
    user_sid = request.sid # type: ignore
    try:
        data = RequestUserConnect.model_validate(data)
        token = data.token
        with user_lock:
            user_pool[user_sid] = token # type: ignore
            logging.info(f"User connect by user sid {user_sid} with token {token}")
            time.sleep(0.3)
            update_queue_position(user_sid, token)
    except ValidationError as e:
        logging.warning(f"Validation error in handle_user_connect: {e}")
        disconnect(user_sid)
        
@socketio.on('disconnect')
def handle_disconnect():
    """This function handle socket disconnect

    Returns:
        str: Message about invalid sid in user_pool
    """
    user_sid = request.sid # type: ignore
    try:
        token = user_pool[user_sid]
    except KeyError:
        logging.warning(f"Cannot find token by user sid {user_sid}")
        return "Invalid token"
    
    with user_lock:
        del user_pool[user_sid]
    
    with queue_lock:
        task_queue[:] = [task for task in task_queue if task.token != token]
    
    with result_lock:
        result_pool.pop(token, None)
            

def update_queue_position(sid: str, token: str):
    """Function to send update info about new position to the user by sid and token

    Args:
        sid (str): user socket sid
        token (str): user token for task
    """
    logging.info(f"Send info by sid {sid} and token {token}")
    if token in result_pool:
        answer = result_pool[token]['content']
        socketio.emit(UPDATE_EVENT_NAME, {'message': 'GOOD', 'content': answer}, room=sid) # type: ignore
        return
    if token in processing_tasks:
        socketio.emit(UPDATE_EVENT_NAME, {'message': 'OK', 'content': 0}, room=sid) # type: ignore
        return
    for i, task in enumerate(task_queue):
        if token == task.token:
            socketio.emit(UPDATE_EVENT_NAME, {'message': 'OK', 'content': i + 1}, room=sid) # type: ignore
            return
    socketio.emit(UPDATE_EVENT_NAME, {'message': 'BAD', 'content': -1}, room=sid) # type: ignore
                    

@app.route("/api/generate", methods=['POST'])
def create_task():
    """Flask route function. Using for create new task based on user POST form request

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
    logging.basicConfig(level=logging.INFO, filename="py_log.log",filemode="w",
                    format="%(asctime)s %(levelname)s %(message)s")
    
    # config instance
    with open('model_config.json') as f:
        try:
            json_config = json.load(f)
        except:
            logging.error('Failed to load model_config.json as json')
            exit()
    try:
        config = ModelConfig.model_validate(json_config)
    except ValidationError as e:
        logging.error(f"Failed to load config: {e}")
        exit()
    
    # model instance
    try:
        model = Model(config)
    except Exception as e:
        logging.error(f"Failed to load model: {e}")
        exit()
    
    start_task_processing()
    app.run(debug=False, port=port)
