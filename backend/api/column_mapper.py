import difflib

COLUMN_MAPPING = {
    'fechaingreso': 'date_of_entry',
    'fecha_ingreso': 'date_of_entry',
    'fechaIngreso': 'date_of_entry',
    # Agrega más mapeos según necesites.
}

def normalize_columns_name(col_name:str)->str:
    return ''.join(e for e in col_name if  e.isalnum()).lower()

def map_column(col_name:str)->str:
    normalized = normalize_columns_name(col_name)
    if normalize_columns_name in COLUMN_MAPPING:
        return COLUMN_MAPPING(normalized)

    posibles = list(COLUMN_MAPPING.keys())
    match =difflib.get_close_matches(normalized,posibles,n=1,cutoff=0.8)
    if match:
        return COLUMN_MAPPING(match[0])
    return normalized


