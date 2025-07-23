# file: /api/main.py

from flask import Flask, jsonify

from api.config import logger, HOST, PORT
from api.routes import whatsapp_webhook, pubsub_chatbot

# Crear la aplicación Flask
app = Flask(__name__)

# Registrar blueprints
app.register_blueprint(whatsapp_webhook, url_prefix='/chatbot/whatsapp')
app.register_blueprint(pubsub_chatbot, url_prefix='/chatbot/pubsub')

# Ruta raíz
@app.route('/', methods=['GET'])
def home():
    """Verificar que la API está funcionando"""
    logger.info("API is working!")
    return jsonify({
        "status": "success",
        "message": "API is working!",
        "version": "1.0.0"
    }), 200

# Manejador de errores 404
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "error": "Recurso no encontrado",
        "status_code": 404
    }), 404

# Manejador de errores 500
@app.errorhandler(500)
def server_error(error):
    logger.error(f"Error interno del servidor: {str(error)}")
    return jsonify({
        "error": "Error interno del servidor",
        "status_code": 500
    }), 500

if __name__ == '__main__':
    logger.info(f"Iniciando servidor en {HOST}:{PORT}")
    app.run(host=HOST, port=PORT, debug=False)


