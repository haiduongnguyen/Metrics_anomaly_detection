import json
import pandas as pd
import numpy as np

def lambda_handler(event, context):
    df = pd.DataFrame({
        "a": [1, 2, 3],
        "b": np.array([10, 20, 30])
    })

    return {
        "statusCode": 200,
        "body": json.dumps({
            "msg": "pandas imported successfully!",
            "df": df.to_dict()
        })
    }
