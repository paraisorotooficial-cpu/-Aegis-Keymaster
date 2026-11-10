"""
Educational Tips System
Provides contextual "Did you know?" tips for Python concepts
"""
import random
from typing import Dict, List


class TipsSystem:
    """Manages educational tips and 'Did you know?' information"""
    
    def __init__(self):
        self.tips = self._init_tips()
    
    def _init_tips(self) -> Dict[str, List[str]]:
        """Initialize all educational tips organized by topic"""
        return {
            "variables": [
                "💡 Sabías que... En Python, las variables no necesitan declaración de tipo. Python infiere el tipo automáticamente.",
                "💡 Sabías que... Puedes asignar múltiples variables en una línea: x, y, z = 1, 2, 3",
                "💡 Sabías que... Los nombres de variables son case-sensitive: 'nombre' y 'Nombre' son diferentes.",
                "💡 Sabías que... Por convención, usa snake_case para nombres de variables: mi_variable_nombre",
            ],
            
            "strings": [
                "💡 Sabías que... Los f-strings (f'texto {variable}') son más rápidos que .format() o %",
                "💡 Sabías que... Puedes usar comillas triples ('''texto''') para strings multilínea",
                "💡 Sabías que... Los strings en Python son inmutables. Cada modificación crea un nuevo string.",
                "💡 Sabías que... Usa str.join() en lugar de concatenación (+) para mejor rendimiento con muchos strings",
            ],
            
            "lists": [
                "💡 Sabías que... Las listas en Python son dinámicas y pueden contener diferentes tipos de datos",
                "💡 Sabías que... list.append() es O(1) pero list.insert(0, x) es O(n) - usa collections.deque para inserciones rápidas al inicio",
                "💡 Sabías que... Los índices negativos acceden desde el final: mi_lista[-1] es el último elemento",
                "💡 Sabías que... Puedes usar list comprehensions para crear listas de forma más eficiente",
            ],
            
            "dicts": [
                "💡 Sabías que... Desde Python 3.7+, los diccionarios mantienen el orden de inserción",
                "💡 Sabías que... Usa dict.get(key, default) para evitar KeyError si la clave no existe",
                "💡 Sabías que... Los diccionarios usan hash tables internamente, haciendo búsquedas O(1)",
                "💡 Sabías que... Puedes fusionar diccionarios con: {**dict1, **dict2}",
            ],
            
            "functions": [
                "💡 Sabías que... Las funciones en Python son objetos de primera clase - pueden ser asignadas a variables",
                "💡 Sabías que... Usa *args para argumentos posicionales variables y **kwargs para argumentos con nombre",
                "💡 Sabías que... Las funciones pueden tener docstrings para documentación: '''Descripción de la función'''",
                "💡 Sabías que... Python soporta funciones anidadas (funciones dentro de funciones)",
            ],
            
            "loops": [
                "💡 Sabías que... enumerate() te da tanto el índice como el valor: for i, val in enumerate(lista)",
                "💡 Sabías que... Usa zip() para iterar sobre múltiples listas simultáneamente",
                "💡 Sabías que... El bucle for-else ejecuta el else solo si el bucle NO fue interrumpido con break",
                "💡 Sabías que... Las list comprehensions son generalmente más rápidas que bucles for equivalentes",
            ],
            
            "conditionals": [
                "💡 Sabías que... Puedes usar operadores ternarios: resultado = 'sí' if condición else 'no'",
                "💡 Sabías que... El operador 'in' funciona con strings, listas, tuplas, sets y diccionarios",
                "💡 Sabías que... Python evalúa 'and' y 'or' con short-circuit: no evalúa el segundo operando si no es necesario",
                "💡 Sabías que... Puedes encadenar comparaciones: if 0 < x < 10:",
            ],
            
            "classes": [
                "💡 Sabías que... __init__ es el constructor de la clase, pero __new__ crea la instancia",
                "💡 Sabías que... Usa @property para crear getters y setters de forma pythónica",
                "💡 Sabías que... __str__ define la representación en string para usuarios, __repr__ para desarrolladores",
                "💡 Sabías que... Python soporta herencia múltiple usando MRO (Method Resolution Order)",
            ],
            
            "exceptions": [
                "💡 Sabías que... Es mejor pedir perdón que permiso: usa try-except en lugar de chequeos previos (EAFP)",
                "💡 Sabías que... El bloque 'finally' siempre se ejecuta, incluso si hay un return en try o except",
                "💡 Sabías que... Puedes crear excepciones personalizadas heredando de Exception",
                "💡 Sabías que... Usa 'raise' sin argumentos dentro de except para re-lanzar la excepción original",
            ],
            
            "file_io": [
                "💡 Sabías que... El context manager 'with' cierra automáticamente el archivo, incluso si hay errores",
                "💡 Sabías que... Usa 'r' para lectura, 'w' para escritura (sobrescribe), 'a' para append",
                "💡 Sabías que... pathlib.Path es más moderno y portable que os.path para manejar rutas",
                "💡 Sabías que... Puedes leer archivos grandes línea por línea con: for line in file:",
            ],
            
            "imports": [
                "💡 Sabías que... Los imports absolutos son preferibles a los relativos para mejor legibilidad",
                "💡 Sabías que... __all__ define qué se exporta cuando usas 'from module import *'",
                "💡 Sabías que... Los módulos se importan solo una vez, luego se cachean en sys.modules",
                "💡 Sabías que... Usa if __name__ == '__main__': para código que solo se ejecuta directamente",
            ],
            
            "comprehensions": [
                "💡 Sabías que... Las list comprehensions son más rápidas que map() + lambda en Python",
                "💡 Sabías que... Existen también dict comprehensions: {k: v for k, v in items}",
                "💡 Sabías que... Set comprehensions crean sets únicos: {x for x in lista}",
                "💡 Sabías que... Las generator expressions usan () en lugar de [] y son más eficientes en memoria",
            ],
            
            "decorators": [
                "💡 Sabías que... Los decoradores son funciones que modifican el comportamiento de otras funciones",
                "💡 Sabías que... @staticmethod no recibe self, @classmethod recibe cls",
                "💡 Sabías que... Puedes apilar múltiples decoradores: se aplican de abajo hacia arriba",
                "💡 Sabías que... functools.wraps preserva metadata de la función original en decoradores",
            ],
            
            "async": [
                "💡 Sabías que... async/await permite programación asíncrona sin callbacks (async/await sobre asyncio)",
                "💡 Sabías que... 'await' solo funciona dentro de funciones 'async def'",
                "💡 Sabías que... asyncio es single-threaded pero puede manejar miles de operaciones I/O concurrentes",
                "💡 Sabías que... Usa asyncio.gather() para ejecutar múltiples coroutines en paralelo",
            ],
            
            "generators": [
                "💡 Sabías que... 'yield' convierte una función en un generador que produce valores bajo demanda",
                "💡 Sabías que... Los generadores son iteradores perezosos - solo calculan valores cuando se necesitan",
                "💡 Sabías que... Puedes enviar valores a un generador con .send() y controlar su ejecución",
                "💡 Sabías que... Los generadores son ideales para trabajar con grandes datasets sin cargar todo en memoria",
            ],
            
            "context_managers": [
                "💡 Sabías que... Los context managers garantizan que recursos se liberen correctamente",
                "💡 Sabías que... Usa @contextmanager de contextlib para crear context managers simples",
                "💡 Sabías que... __enter__ se ejecuta al inicio del bloque 'with', __exit__ al final",
                "💡 Sabías que... Puedes usar múltiples context managers: with open(f1) as file1, open(f2) as file2:",
            ],
            
            "type_hints": [
                "💡 Sabías que... Los type hints mejoran la legibilidad pero no se verifican en runtime",
                "💡 Sabías que... Usa typing.Optional[T] para valores que pueden ser None",
                "💡 Sabías que... typing.Union[A, B] permite múltiples tipos posibles",
                "💡 Sabías que... mypy es una herramienta popular para verificación estática de tipos",
            ],
            
            "best_practices": [
                "💡 Sabías que... PEP 8 es la guía de estilo oficial de Python - úsala para código consistente",
                "💡 Sabías que... 'Explicit is better than implicit' - uno de los principios del Zen de Python",
                "💡 Sabías que... Usa virtualenv o venv para aislar dependencias de proyectos",
                "💡 Sabías que... Los docstrings deben describir QUÉ hace la función, no CÓMO lo hace",
            ],
            
            "performance": [
                "💡 Sabías que... Las operaciones en sets son mucho más rápidas que en listas para búsquedas",
                "💡 Sabías que... Usa generators en lugar de listas cuando proceses datos grandes",
                "💡 Sabías que... __slots__ puede reducir el uso de memoria en clases con muchas instancias",
                "💡 Sabías que... El módulo 'timeit' es perfecto para medir el rendimiento de pequeños snippets",
            ],
        }
    
    def get_tip(self, topic: str = None) -> str:
        """Get a random tip, optionally filtered by topic"""
        if topic and topic in self.tips:
            return random.choice(self.tips[topic])
        
        # Get random tip from any topic
        all_tips = []
        for tips_list in self.tips.values():
            all_tips.extend(tips_list)
        
        return random.choice(all_tips) if all_tips else "💡 ¡Sigue practicando para mejorar!"
    
    def get_tip_for_concept(self, concept: str) -> str:
        """Get a tip based on the concept being practiced"""
        # Map concepts to tip topics
        concept_mapping = {
            "variables": "variables",
            "strings": "strings",
            "lists": "lists",
            "dicts": "dicts",
            "basic": "functions",
            "params": "functions",
            "lambda": "functions",
            "loops": "loops",
            "conditionals": "conditionals",
            "classes": "classes",
            "inheritance": "classes",
            "decorators": "decorators",
            "handling": "exceptions",
            "raising": "exceptions",
            "reading": "file_io",
            "writing": "file_io",
            "imports": "imports",
            "comprehensions": "comprehensions",
            "async": "async",
            "context": "context_managers",
        }
        
        topic = concept_mapping.get(concept, None)
        return self.get_tip(topic)
    
    def get_all_topics(self) -> List[str]:
        """Get list of all available tip topics"""
        return list(self.tips.keys())