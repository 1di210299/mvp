"""
Forecasting Tasks Module - Organized by categories
=================================================

This module provides task functionality organized by categories:
- base_tasks: Core prediction and analysis tasks
- ml_tasks: Machine learning and model training tasks
- utils_tasks: Utility and maintenance tasks
- training_tasks: Model training and validation tasks
- forecast_tasks: Forecasting generation tasks
- training_algorithms: Specific training algorithms
- forecast_generation: Forecast generation utilities
- utils: Legacy utility functions
"""

# Import all tasks from organized modules
from .base_tasks import *
from .ml_tasks import *
from .utils_tasks import *
from .training_tasks import *
from .forecast_tasks import *

# Legacy imports for backward compatibility
from .training_algorithms import *
from .forecast_generation import *
from .utils import *
