# file: /api/services/ai_services.py

from typing import List
from api.config import logger
from google.cloud import vision

class AIServices:
    @staticmethod
    def extract_image_ocr(image_bytes: bytes) -> str:
        """
        Procesa una imagen utilizando la API de OCR de Google Cloud Vision.
        
        Args:
            image_bytes: Datos de la imagen en formato bytes
            
        Returns:
            str: Texto extraído de la imagen
        """
        try:
            client: vision.ImageAnnotatorClient = vision.ImageAnnotatorClient()
            image: vision.Image = vision.Image(content=image_bytes)
            
            # Realizar petición de detección de texto
            response = client.text_detection(image=image)
            texts: List = response.text_annotations
            
            # Verificar si hay errores
            if response.error.message:
                logger.error(f"Error en el procesamiento OCR: {response.error.message}")
                return ""
            
            # Extraer el texto completo (el primer elemento contiene todo el texto)
            full_text: str = texts[0].description if texts else ""
            
            # Registrar éxito
            if full_text:
                logger.info(f"OCR completado exitosamente. Se extrajeron {len(full_text)} caracteres.")
            else:
                logger.info("OCR completado, pero no se encontró texto en la imagen.")
                
            return full_text
        except Exception as e:
            logger.error(f"Error en el procesamiento OCR: {str(e)}")
            return ""

    @staticmethod
    def speech_to_text(audio_bytes: bytes) -> str:
        """
        Convierte audio a texto utilizando la API de reconocimiento de voz.
        
        Args:
            audio_bytes: Datos del audio en formato bytes
            
        Returns:
            str: Texto transcrito del audio
        """
        # Esta funcionalidad se implementará en el futuro
        logger.info("La funcionalidad de transcripción de audio aún no está implementada")
        return "Transcripción de audio en desarrollo"
    
    @staticmethod
    def analyze_image(image_bytes: bytes) -> str:
        """
        Analiza el contenido de una imagen para generar una descripción.
        
        Args:
            image_bytes: Datos de la imagen en formato bytes
            
        Returns:
            str: Descripción generada de la imagen
        """
        try:
            client: vision.ImageAnnotatorClient = vision.ImageAnnotatorClient()
            image: vision.Image = vision.Image(content=image_bytes)
            
            # Realizar análisis de etiquetas
            response = client.label_detection(image=image)
            labels = response.label_annotations
            
            if response.error.message:
                logger.error(f"Error en el análisis de imagen: {response.error.message}")
                return ""
            
            # Generar descripción basada en las etiquetas encontradas
            if labels:
                top_labels: List[str] = [label.description for label in labels[:5]]
                description: str = f"La imagen contiene: {', '.join(top_labels)}"
                logger.info(f"Análisis de imagen completado exitosamente.")
                return description
            else:
                logger.info("Análisis de imagen completado, pero no se encontraron etiquetas.")
                return "No se pudieron identificar elementos en la imagen"
        except Exception as e:
            logger.error(f"Error en el análisis de imagen: {str(e)}")
            return ""