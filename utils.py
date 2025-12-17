"""
Funciones utilitarias para el scraper
"""
import os
import json
import pandas as pd
import logging
from datetime import datetime
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


def save_to_json(data: List[Dict[str, Any]], filename: str = None):
    """
    Guarda datos en formato JSON
    
    Args:
        data: Lista de diccionarios con los datos
        filename: Nombre del archivo (puede incluir ruta completa)
    """
    try:
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"scraped_data_{timestamp}.json"
            os.makedirs("data", exist_ok=True)
            filepath = os.path.join("data", filename)
        else:
            # Si filename incluye ruta, crear directorio
            filepath = filename
            directory = os.path.dirname(filepath)
            if directory:
                os.makedirs(directory, exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Datos guardados en: {filepath}")
        return filepath
        
    except Exception as e:
        logger.error(f"Error al guardar JSON: {e}")
        return None


def save_to_csv(data: List[Dict[str, Any]], filename: str = None):
    """
    Guarda datos en formato CSV
    
    Args:
        data: Lista de diccionarios con los datos
        filename: Nombre del archivo (puede incluir ruta completa)
    """
    try:
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"scraped_data_{timestamp}.csv"
            os.makedirs("data", exist_ok=True)
            filepath = os.path.join("data", filename)
        else:
            # Si filename incluye ruta, crear directorio
            filepath = filename
            directory = os.path.dirname(filepath)
            if directory:
                os.makedirs(directory, exist_ok=True)
        
        df = pd.DataFrame(data)
        df.to_csv(filepath, index=False, encoding='utf-8-sig')
        
        logger.info(f"Datos guardados en: {filepath}")
        return filepath
        
    except Exception as e:
        logger.error(f"Error al guardar CSV: {e}")
        return None


def save_to_excel(data: List[Dict[str, Any]], filename: str = None):
    """
    Guarda datos en formato Excel
    
    Args:
        data: Lista de diccionarios con los datos
        filename: Nombre del archivo (genera uno automático si es None)
    """
    try:
        os.makedirs("data", exist_ok=True)
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"scraped_data_{timestamp}.xlsx"
        
        filepath = os.path.join("data", filename)
        
        df = pd.DataFrame(data)
        df.to_excel(filepath, index=False, engine='openpyxl')
        
        logger.info(f"Datos guardados en: {filepath}")
        return filepath
        
    except Exception as e:
        logger.error(f"Error al guardar Excel: {e}")
        return None


def clean_text(text: str) -> str:
    """
    Limpia texto eliminando espacios extra y caracteres especiales
    
    Args:
        text: Texto a limpiar
        
    Returns:
        Texto limpio
    """
    if not text:
        return ""
    
    # Eliminar espacios extra
    text = " ".join(text.split())
    
    # Eliminar caracteres especiales si es necesario
    # text = re.sub(r'[^\w\s-]', '', text)
    
    return text.strip()


def create_output_dir(dirname: str = "data"):
    """
    Crea el directorio de salida si no existe
    
    Args:
        dirname: Nombre del directorio
    """
    try:
        os.makedirs(dirname, exist_ok=True)
        logger.info(f"Directorio creado/verificado: {dirname}")
    except Exception as e:
        logger.error(f"Error al crear directorio: {e}")


def get_timestamp() -> str:
    """
    Retorna un timestamp formateado
    
    Returns:
        String con formato YYYYMMDD_HHMMSS
    """
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def log_scraping_stats(total_items: int, success: int, failed: int, duration: float):
    """
    Registra estadísticas del scraping
    
    Args:
        total_items: Total de items procesados
        success: Items exitosos
        failed: Items fallidos
        duration: Duración en segundos
    """
    logger.info("=" * 50)
    logger.info("ESTADÍSTICAS DE SCRAPING")
    logger.info(f"Total de items: {total_items}")
    logger.info(f"Exitosos: {success}")
    logger.info(f"Fallidos: {failed}")
    logger.info(f"Duración: {duration:.2f} segundos")
    logger.info(f"Items por segundo: {total_items/duration:.2f}")
    logger.info("=" * 50)
