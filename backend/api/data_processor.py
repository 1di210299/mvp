import pandas  as pd 
from .column_mapper import map_column

def process_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    new_columns = {}
    for col in df.columns:
        new_columns[col]=map_column(col)
    df.rename(columns=new_columns, inplace=True)

    df.drop_duplicates(inplace=True)
    df.fillna(value=None, inplace=True)

def process_file(file_obj) -> dict:
    try:
        if file_obj.name.endswith('.csv'):
            df = pd.read_csv(file_obj)
        elif file_obj.name.endswith(('.xls','.xlsx')):
            df = pd.read_excel(file_obj)
        else:
            return {'error':'formato de archivo no encontrado'}

    except Exception as e:
        print(f'error:{e}')

    processed_df = process_dataframe(df)
    result = processed_df.to_dict(orient='records')
    return {'data':result}