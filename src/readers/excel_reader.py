import pandas as pd
import os
import logging

logger = logging.getLogger(__name__)

class ExcelReader:
    """
    A class to read Excel (.xlsx, .xls) files containing publication records to match.
    """
    def __init__(self, file_path):
        self.file_path = file_path
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Excel file not found: {file_path}")

    def read_records(self) -> list:
        """
        Reads Excel file and returns a list of dictionaries, one per row.
        """
        records = []
        try:
            # We can use pandas to read the excel file
            df = pd.read_excel(self.file_path)
            # Fill NaN values with empty string
            df = df.fillna("")
            records = df.to_dict(orient="records")
        except Exception as e:
            logger.error(f"Error reading Excel file {self.file_path}: {e}")
        return records
