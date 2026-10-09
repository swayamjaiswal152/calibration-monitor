import pandas as pd
from app.drift import compute_metrics, is_drift
def test_coverage():
    df = pd.DataFrame({"y_pred":[10,10],"y_lower":[8,8],"y_upper":[12,12],"y_true":[9,13]})
    m = compute_metrics(df)
    assert m["picp"] == 0.5
    assert is_drift(0.5) == True