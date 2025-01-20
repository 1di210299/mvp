# debug_logger.py
import logging
import os
from datetime import datetime
import streamlit as st

class DebugLogger:
    def __init__(self, enabled=False, log_to_file=True):
        self.enabled = enabled
        self.log_to_file = log_to_file
        self.logs = []
        
        if enabled:
            # Configure logging
            logging.basicConfig(
                level=logging.DEBUG,
                format='%(asctime)s - %(levelname)s - %(message)s'
            )
            self.logger = logging.getLogger('FileProcessor')
            
            if log_to_file:
                # Create logs directory if it doesn't exist
                if not os.path.exists('logs'):
                    os.makedirs('logs')
                    
                # Create log file with timestamp
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                log_file = f'logs/debug_{timestamp}.log'
                file_handler = logging.FileHandler(log_file)
                file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
                self.logger.addHandler(file_handler)

    def log(self, message, level='info'):
        """Logs a message with the specified level"""
        if not self.enabled:
            return

        # Add to internal list
        self.logs.append({
            'timestamp': datetime.now().isoformat(),
            'level': level,
            'message': message
        })

        # Logging by level
        if level == 'debug':
            self.logger.debug(message)
        elif level == 'info':
            self.logger.info(message)
        elif level == 'warning':
            self.logger.warning(message)
        elif level == 'error':
            self.logger.error(message)

    def get_logs(self):
        """Returns all stored logs"""
        return self.logs

    def clear_logs(self):
        """Clear stored logs"""
        self.logs = []