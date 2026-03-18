import numpy as np
from sklearn.linear_model import LinearRegression

class InfusionAIPredictor:

    def predict_future_level(self, values):
        if len(values) < 5:
            return None

        X = np.array(range(len(values))).reshape(-1, 1)
        y = np.array(values)

        model = LinearRegression()
        model.fit(X, y)

        return float(model.predict([[len(values)+5]])[0])

    def estimate_time_to_empty(self, values):
        if len(values) < 5:
            return None

        diffs = np.diff(values)
        avg_drop = abs(np.mean(diffs))

        if avg_drop == 0:
            return None

        return int(values[-1] / avg_drop)