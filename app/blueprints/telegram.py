from flask import Blueprint, request, jsonify, current_app
from app.services.telegram_service import TelegramBotService

telegram_bp = Blueprint('telegram', __name__, url_prefix='/telegram')

def _get_bot_service() -> TelegramBotService:
    bot_service = TelegramBotService()
    bot_service.bot_token = (current_app.config.get('TELEGRAM_BOT_TOKEN') or '').strip()
    return bot_service

@telegram_bp.route('/webhook', methods=['POST'])
def telegram_webhook():
    """Handle Telegram webhook requests"""
    try:
        bot_service = _get_bot_service()
        if not bot_service.bot_token:
            return jsonify({'status': 'error', 'message': 'TELEGRAM_BOT_TOKEN is not configured'}), 500

        update = request.get_json()
        if update:
            result = bot_service.process_update(update)
            if result:
                return jsonify({'status': 'success', 'message': 'Update processed'}), 200
            else:
                return jsonify({'status': 'error', 'message': 'Failed to process update'}), 400
        
        return jsonify({'status': 'no update', 'message': 'No update received'}), 200
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@telegram_bp.route('/status', methods=['GET'])
def telegram_status():
    """Get Telegram bot status"""
    try:
        bot_service = _get_bot_service()
        if not bot_service.bot_token:
            return jsonify({'status': 'inactive', 'message': 'TELEGRAM_BOT_TOKEN is not configured'}), 400

        bot_info = bot_service.get_bot_info()
        if bot_info:
            return jsonify({
                'status': 'active',
                'bot_info': bot_info,
                'webhook': 'configured'
            }), 200
        else:
            return jsonify({
                'status': 'inactive',
                'message': 'Bot not accessible'
            }), 400
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@telegram_bp.route('/test', methods=['POST'])
def test_telegram():
    """Test Telegram bot functionality"""
    try:
        bot_service = _get_bot_service()
        if not bot_service.bot_token:
            return jsonify({'status': 'error', 'message': 'TELEGRAM_BOT_TOKEN is not configured'}), 500

        data = request.get_json()
        chat_id = data.get('chat_id')
        message = data.get('message', 'Test message from College Virtual Assistant')
        
        if not chat_id:
            return jsonify({'status': 'error', 'message': 'chat_id is required'}), 400
        
        result = bot_service.send_message(chat_id, message)
        
        if result:
            return jsonify({
                'status': 'success',
                'message': 'Message sent successfully'
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to send message'
            }), 400
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
