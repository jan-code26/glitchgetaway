"""
AI provider abstraction layer for puzzle generation.

Supports multiple AI providers (Anthropic, OpenAI, Google Gemini) with a
common interface. Provider selection is controlled via AI_PROVIDER environment
variable, or falls back to the first available provider with an API key.
"""

import json
import os
from abc import ABC, abstractmethod
from typing import List, Dict, Optional


class BasePuzzleGenerator(ABC):
    """Base class for AI puzzle generators."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
    
    @abstractmethod
    def generate_puzzles(
        self,
        topic: Optional[str] = None,
        count: int = 5,
        custom_prompt: Optional[str] = None
    ) -> List[Dict]:
        """
        Generate puzzle data.
        
        Args:
            topic: Optional topic/theme for the puzzles
            count: Number of puzzles to generate
            custom_prompt: Optional custom prompt to override default
        
        Returns:
            List of dictionaries with keys:
                - title
                - description
                - puzzle_question
                - puzzle_answer
                - alternate_answers (comma-separated string)
                - hint
        """
        pass
    
    def _build_prompt(
        self,
        topic: Optional[str] = None,
        count: int = 5,
        custom_prompt: Optional[str] = None
    ) -> str:
        """Build the prompt for the AI."""
        if custom_prompt:
            return custom_prompt
        
        topic_text = f" about {topic}" if topic else " about web development, programming, or technology"
        
        return f"""Generate {count} escape room puzzle{'' if count == 1 else 's'}{topic_text}.

Each puzzle should:
- Be solvable with programming/tech knowledge
- Have a clear, specific answer (ideally short - max 100 characters)
- Include 1-3 alternate acceptable answers if applicable
- Have a helpful hint that guides without giving away the answer
- Be engaging and educational

Return your response as a JSON array with this exact structure:
[
  {{
    "title": "Puzzle Title (max 100 chars)",
    "description": "Engaging narrative description of the scenario",
    "puzzle_question": "The actual question or challenge",
    "puzzle_answer": "The primary correct answer",
    "alternate_answers": "comma,separated,alternates or empty string",
    "hint": "A helpful hint"
  }}
]

Return ONLY the JSON array, no other text."""
    
    def _parse_response(self, response_text: str) -> List[Dict]:
        """Parse the AI response into puzzle dictionaries."""
        # Try to extract JSON from the response
        response_text = response_text.strip()
        
        # Look for JSON array markers
        start = response_text.find('[')
        end = response_text.rfind(']')
        
        if start != -1 and end != -1:
            json_text = response_text[start:end + 1]
            try:
                puzzles = json.loads(json_text)
                
                # Validate structure
                required_keys = {
                    'title', 'description', 'puzzle_question',
                    'puzzle_answer', 'alternate_answers', 'hint'
                }
                
                validated_puzzles = []
                for puzzle in puzzles:
                    if all(key in puzzle for key in required_keys):
                        # Ensure alternate_answers is a string
                        if not isinstance(puzzle['alternate_answers'], str):
                            puzzle['alternate_answers'] = ','.join(
                                str(a) for a in puzzle['alternate_answers']
                            )
                        validated_puzzles.append(puzzle)
                
                return validated_puzzles
            except json.JSONDecodeError as e:
                raise ValueError(f"Failed to parse AI response as JSON: {e}")
        
        raise ValueError("No JSON array found in AI response")


class AnthropicProvider(BasePuzzleGenerator):
    """Anthropic Claude puzzle generator."""
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key or os.getenv('ANTHROPIC_API_KEY'))
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not set")
    
    def generate_puzzles(
        self,
        topic: Optional[str] = None,
        count: int = 5,
        custom_prompt: Optional[str] = None
    ) -> List[Dict]:
        try:
            import anthropic
        except ImportError:
            raise ImportError("anthropic package not installed. Run: pip install anthropic")
        
        client = anthropic.Anthropic(api_key=self.api_key)
        prompt = self._build_prompt(topic, count, custom_prompt)
        
        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}]
        )
        
        response_text = message.content[0].text
        return self._parse_response(response_text)


class OpenAIProvider(BasePuzzleGenerator):
    """OpenAI GPT puzzle generator."""
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key or os.getenv('OPENAI_API_KEY'))
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not set")
    
    def generate_puzzles(
        self,
        topic: Optional[str] = None,
        count: int = 5,
        custom_prompt: Optional[str] = None
    ) -> List[Dict]:
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("openai package not installed. Run: pip install openai")
        
        client = OpenAI(api_key=self.api_key)
        prompt = self._build_prompt(topic, count, custom_prompt)
        
        response = client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )
        
        response_text = response.choices[0].message.content
        return self._parse_response(response_text)


class GeminiProvider(BasePuzzleGenerator):
    """Google Gemini puzzle generator."""
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key or os.getenv('GOOGLE_API_KEY'))
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY not set")
    
    def generate_puzzles(
        self,
        topic: Optional[str] = None,
        count: int = 5,
        custom_prompt: Optional[str] = None
    ) -> List[Dict]:
        try:
            import google.generativeai as genai
        except ImportError:
            raise ImportError(
                "google-generativeai package not installed. "
                "Run: pip install google-generativeai"
            )
        
        genai.configure(api_key=self.api_key)
        model = genai.GenerativeModel('gemini-pro')
        
        prompt = self._build_prompt(topic, count, custom_prompt)
        response = model.generate_content(prompt)
        
        return self._parse_response(response.text)


# Provider registry
PROVIDERS = {
    'anthropic': AnthropicProvider,
    'openai': OpenAIProvider,
    'gemini': GeminiProvider,
}


def get_provider(provider_name: Optional[str] = None) -> BasePuzzleGenerator:
    """
    Get an AI provider instance.
    
    Args:
        provider_name: Name of provider ('anthropic', 'openai', 'gemini').
                      If None, uses AI_PROVIDER env var or auto-detects.
    
    Returns:
        Configured provider instance
    
    Raises:
        ValueError: If no provider is available or configured
    """
    # Use specified provider or environment variable
    if not provider_name:
        provider_name = os.getenv('AI_PROVIDER', '').lower()
    
    # If a specific provider is requested, try to use it
    if provider_name:
        if provider_name not in PROVIDERS:
            raise ValueError(
                f"Unknown provider: {provider_name}. "
                f"Valid options: {', '.join(PROVIDERS.keys())}"
            )
        try:
            return PROVIDERS[provider_name]()
        except ValueError as e:
            raise ValueError(f"Cannot use {provider_name} provider: {e}")
    
    # Auto-detect: try each provider in order
    for name, provider_class in PROVIDERS.items():
        try:
            return provider_class()
        except (ValueError, ImportError):
            continue
    
    # No provider available
    raise ValueError(
        "No AI provider configured. Set one of: "
        "ANTHROPIC_API_KEY, OPENAI_API_KEY, or GOOGLE_API_KEY"
    )
