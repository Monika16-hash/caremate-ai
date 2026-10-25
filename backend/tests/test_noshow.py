import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from ml.noshow import predict_noshow

def test_reliable_patient_low_risk():
    assert predict_noshow(1.0, 0, 10) < 0.5

def test_unreliable_patient_high_risk():
    assert predict_noshow(0.2, 6, 200) > 0.7

def test_probability_range():
    assert 0 <= predict_noshow(0.5, 2, 60) <= 1
