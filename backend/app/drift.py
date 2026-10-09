import pandas as pd

TARGET = 0.9
EPSILON = 0.05
WINDOW = 168

def compute_metrics(df: pd.DataFrame):
    df['covered'] = (df['y_true'] >= df['y_lower']) & (df['y_true'] <= df['y_upper'])
    picp = df['covered'].mean()
    mae = (df['y_true'] - df['y_pred']).abs().mean()
    mpiw = (df['y_upper'] - df['y_lower']).mean()
    # Winkler Score for alpha=0.1
    alpha = 0.1
    winkler = ((df['y_upper'] - df['y_lower']) + 
               (2/alpha)*(df['y_lower']-df['y_true'])*(df['y_true'] < df['y_lower']) +
               (2/alpha)*(df['y_true']-df['y_upper'])*(df['y_true'] > df['y_upper'])).mean()
    return {"picp": float(picp), "mae": float(mae), "mpiw": float(mpiw), "winkler": float(winkler)} # type: ignore

def is_drift(picp: float): return picp < (TARGET - EPSILON)