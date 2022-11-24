import os
import pandas as pd
from google.cloud import bigquery
from google.oauth2 import service_account


class BigQueryClient():
    def __init__(self, credential_json, project_id):
        self.project_id = project_id
        self.credentials = service_account.Credentials.from_service_account_file(
            credential_json)
        self.client = bigquery.Client(
            credentials=self.credentials, project=project_id)

    def query(self, query_str):
        return pd.read_gbq(query_str, credentials=self.credentials)

    def get_schemas(self):
        data = dict()
        schemas = list(self.query(
            'SELECT DISTINCT schema_name FROM INFORMATION_SCHEMA.SCHEMATA')['schema_name'])

        for schema in schemas:
            tables = list(pd.read_gbq(f'SELECT table_name FROM {self.project_id}.{schema}.INFORMATION_SCHEMA.TABLES')['table_name'])
            data[schema] = dict()
            for table in tables:
                data[schema][table] = dict()
                table_ref = self.client.get_table(f'{self.project_id}.{schema}.{table}')
                      
                data[schema][table] = dict(zip([schema.name for schema in table_ref.schema], [schema.field_type for schema in table_ref.schema]))

        return data
    
    def download_csv(self, project, schema, table):
        path = f'data/{project}.{schema}.{table}.csv'
        if not os.path.exists(path):
            dataset_ref = bigquery.DatasetReference(project, schema)
            table_ref = dataset_ref.table(table)
            table_df = self.client.get_table(table_ref)

            df = self.client.list_rows(table_df).to_dataframe()
            df.to_csv(f'data/{project}.{schema}.{table}.csv', sep="\t")
            
        return path
    
    def download_json(self, project, schema, table):
        path = f'./data/{project}.{schema}.{table}.json'
        if not os.path.exists(path):
            dataset_ref = bigquery.DatasetReference(project, schema)
            table_ref = dataset_ref.table(table)
            table_df = self.client.get_table(table_ref)

            df = self.client.list_rows(table_df).to_dataframe()
            df.to_json(os.path.join('data', f'{project}.{schema}.{table}.json'),
                    orient='split', compression='infer', index='true')

        return path
    
    def delete_table(self, schema, table):
        table_ref = self.client.dataset(schema).table(table)
        self.client.delete_table(table_ref)
        
    def add_column(self, project, schema, table, column, type):
        table = self.client.get_table(f'{project}.{schema}.{table}')
        original_schema = table.schema
        new_schema = original_schema[:]  # Creates a copy of the schema.
        new_schema.append(bigquery.SchemaField(column, type))

        table.schema = new_schema
        # Make an API request.
        table = self.client.update_table(table, ["schema"])

        if len(table.schema) == len(original_schema) + 1 == len(new_schema):
            return True
        else:
            return False
        
    def append(self, project, schema, table, new_row):
        table = self.client.get_table(f'{project}.{schema}.{table}')
        errors = self.client.insert_rows_json(table, new_row)
        return errors == []
    
    def load_table_from_df(self, df, schema, table):
        job = self.client.load_table_from_dataframe(df, f'{schema}.{table}')
        return job

def logout():
    from flask import session
    session.pop('user')
