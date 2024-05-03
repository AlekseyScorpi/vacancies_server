from flask import Flask, jsonify, request
from jsonschema import validate, ValidationError
from model import Model
from model_config import ModelConfig
import json

# app instance
app = Flask(__name__)

with open('schemas.json') as f:
    schema = json.load(f)

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

@app.route("/api/data", methods=['POST'])
def get_data():
    try:
        data = request.json
        
        validate(instance=data, schema=schema['requestGenerateVacancy'])
        
        answer = model.generate(
        vacancy_name=data['vacancy_name'],
        company_name=data['company_name'],
        company_place=data['company_place'],
        schedule=data['schedule'],
        experience=data['experience'],
        key_skills=data['key_skills'],
    )
        
        response_data = {'answer': answer}
        return jsonify(response_data)
    
    except ValidationError as e:
        error_response = {'error': 'Invalid JSON format: ' + str(e)}
        return jsonify(error_response), 400

@app.route("/api/home", methods=['GET'])
def return_home():
    return jsonify({
        'description': str(model._model)
    })

if __name__ == "__main__":
    app.run(debug=True)
