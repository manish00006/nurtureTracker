"""
AI Services for Nurture Coaching App.
Integrates Anthropic Claude (for parent Q&A) and local Ollama (for student doubt solving).
"""

import os
import json
import requests
import logging
from django.conf import settings
from .models import AIConversationLog

logger = logging.getLogger(__name__)


class ClaudeService:
    """Service to interact with Anthropic Claude API for Parent Queries."""
    def __init__(self):
        self.api_key = getattr(settings, 'CLAUDE_API_KEY', '')
        self.model = "claude-3-sonnet-20240229" # Or haiku for speed
        
        try:
            from anthropic import Anthropic
            self.client = Anthropic(api_key=self.api_key) if self.api_key else None
        except ImportError:
            self.client = None
            logger.error("Anthropic library not installed.")

    def get_parent_response(self, user, message, context_data=None):
        """
        Get a response for a parent query.
        context_data is a dict containing child's progress (attendance, scores).
        """
        if not self.client:
            return "[DEV MODE] Claude API key missing or library not installed. Please set CLAUDE_API_KEY."

        # Build system prompt with context
        system_prompt = (
            "You are a helpful, polite assistant for Nurture Coaching Class. "
            "Your job is to answer questions from parents about their child's progress, "
            "coaching policies, or general advice. "
        )
        if context_data:
            system_prompt += f"\nHere is the data for the parent's children: {json.dumps(context_data)}"
            
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=500,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": message}
                ]
            )
            text_response = response.content[0].text
            
            # Log conversation
            AIConversationLog.objects.create(
                user=user,
                message=message,
                response=text_response,
                source='parent_qa',
                tokens_used=response.usage.input_tokens + response.usage.output_tokens
            )
            return text_response
            
        except Exception as e:
            logger.error(f"Claude API Error: {e}")
            return "Sorry, I am currently unable to process your request. Please try again later."


class OllamaService:
    """Service to interact with local Ollama for Student Doubt Solving."""
    def __init__(self):
        self.base_url = getattr(settings, 'OLLAMA_BASE_URL', 'http://localhost:11434')
        self.model = getattr(settings, 'OLLAMA_MODEL', 'qwen2.5-coder')

    def get_student_response(self, user, student, message):
        """
        Get a response for a student doubt.
        """
        url = f"{self.base_url}/api/generate"
        
        system_prompt = (
            "You are a friendly, encouraging tutor for Nurture Coaching Class. "
            "Your job is to help students (from Jr.KG to 9th standard) understand concepts. "
            "Do NOT just give the direct answer to homework problems. "
            "Instead, guide them, give hints, and explain the underlying concepts clearly and simply."
        )
        
        payload = {
            "model": self.model,
            "prompt": f"{system_prompt}\n\nStudent Doubt: {message}\n\nTutor Response:",
            "stream": False
        }
        
        try:
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()
            data = response.json()
            text_response = data.get('response', '')
            
            # Log conversation
            AIConversationLog.objects.create(
                user=user,
                student=student,
                message=message,
                response=text_response,
                source='student_doubt'
            )
            return text_response
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Ollama API Error: {e}")
            return "[DEV MODE] Local Ollama service is not running or accessible. Please ensure Ollama is running."
