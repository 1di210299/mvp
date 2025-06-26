import openai
import os
from dotenv import load_dotenv
from typing import Dict, List
import json

load_dotenv()

# Configuración de OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

class OpenAIService:
    def __init__(self):
        self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
    async def improve_cv(self, original_cv: str) -> Dict[str, str]:
        """Mejorar CV usando GPT-4"""
        prompt = f"""
        Eres un coach de empleo especializado en el mercado laboral peruano. 
        Mejora el siguiente CV considerando:
        
        1. Formato profesional adaptado al mercado peruano
        2. Terminología laboral común en Perú
        3. Estructura clara y atractiva para reclutadores peruanos
        4. Optimización para ATS (Applicant Tracking Systems)
        5. Uso de verbos de acción en español
        6. Adaptación cultural apropiada
        
        CV Original:
        {original_cv}
        
        Devuelve una respuesta en formato JSON con:
        - "improved_cv": El CV mejorado
        - "feedback": Comentarios específicos sobre las mejoras realizadas
        - "suggestions": 3 sugerencias adicionales para el candidato
        
        Responde solo en español y enfócate en el mercado laboral peruano.
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "Eres un experto coach de empleo especializado en el mercado laboral peruano."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2000,
                temperature=0.7
            )
            
            result = json.loads(response.choices[0].message.content)
            return result
            
        except Exception as e:
            return {
                "improved_cv": "Error al procesar el CV. Intenta nuevamente.",
                "feedback": f"Error: {str(e)}",
                "suggestions": ["Verifica tu conexión a internet", "Intenta con un CV más corto", "Contacta al soporte técnico"]
            }
    
    async def generate_cover_letter(self, job_title: str, company_name: str, 
                                  job_description: str = None, user_experience: str = None) -> Dict[str, str]:
        """Generar carta de presentación"""
        prompt = f"""
        Eres un coach de empleo especializado en el mercado laboral peruano.
        Genera una carta de presentación profesional para:
        
        Puesto: {job_title}
        Empresa: {company_name}
        Descripción del puesto: {job_description or "No proporcionada"}
        Experiencia del usuario: {user_experience or "No proporcionada"}
        
        La carta debe:
        1. Usar un tono profesional pero cálido, apropiado para Perú
        2. Mencionar empresas peruanas relevantes si es apropiado
        3. Usar terminología laboral común en Perú
        4. Ser concisa pero impactante (máximo 300 palabras)
        5. Incluir estructura: saludo, introducción, cuerpo, cierre
        6. Adaptarse al tipo de industria y puesto
        
        Devuelve una respuesta en formato JSON con:
        - "cover_letter": La carta de presentación completa
        - "tips": 3 consejos para personalizar aún más la carta
        
        Responde solo en español.
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "Eres un experto en redacción de cartas de presentación para el mercado laboral peruano."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1500,
                temperature=0.7
            )
            
            result = json.loads(response.choices[0].message.content)
            return result
            
        except Exception as e:
            return {
                "cover_letter": "Error al generar la carta. Intenta nuevamente.",
                "tips": ["Verifica tu conexión", "Intenta con menos texto", "Contacta soporte"]
            }
    
    async def conduct_interview(self, job_title: str, conversation_history: List[Dict] = None, 
                              user_response: str = None) -> Dict[str, str]:
        """Conducir entrevista de trabajo"""
        
        if not conversation_history:
            conversation_history = []
            
        # Primera pregunta si no hay historial
        if not conversation_history and not user_response:
            prompt = f"""
            Eres un reclutador peruano experimentado que está entrevistando a un candidato para el puesto de: {job_title}
            
            Inicia la entrevista con una pregunta apropiada para el mercado laboral peruano.
            Usa un tono profesional pero amigable, como es común en Perú.
            
            Devuelve una respuesta en formato JSON con:
            - "question": La primera pregunta de la entrevista
            - "context": Breve explicación de por qué esta pregunta es importante
            
            Responde solo en español.
            """
        else:
            # Continuar entrevista
            history_text = "\n".join([f"P: {item['question']}\nR: {item['response']}" for item in conversation_history])
            prompt = f"""
            Eres un reclutador peruano experimentado entrevistando para el puesto de: {job_title}
            
            Historial de la entrevista:
            {history_text}
            
            Última respuesta del candidato: {user_response}
            
            Evalúa la respuesta y:
            1. Proporciona feedback constructivo
            2. Haz la siguiente pregunta apropiada
            3. Mantén el tono profesional peruano
            4. Considera el contexto cultural peruano
            
            Devuelve una respuesta en formato JSON con:
            - "feedback": Evaluación de la última respuesta (2-3 oraciones)
            - "question": La siguiente pregunta de la entrevista
            - "score": Puntuación de 1-10 para la última respuesta
            - "tips": Un consejo específico para mejorar
            
            Responde solo en español.
            """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "Eres un reclutador experto especializado en entrevistas laborales en Perú."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.8
            )
            
            result = json.loads(response.choices[0].message.content)
            return result
            
        except Exception as e:
            return {
                "question": "Error en la entrevista. ¿Podrías repetir tu respuesta?",
                "feedback": "Error técnico en el procesamiento",
                "score": 0,
                "tips": "Intenta nuevamente"
            }

# Instancia global del servicio
openai_service = OpenAIService()