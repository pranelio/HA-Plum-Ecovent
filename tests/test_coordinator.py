import os
import sys

# make repo root available
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from custom_components.plum_ecovent.coordinator import PlumEcoventCoordinator


def test_minor_partial_failure_threshold_is_not_warning() -> None:
    assert PlumEcoventCoordinator._should_warn_partial_failure(1, 40) is False


def test_partial_failure_threshold_warns_by_ratio() -> None:
    assert PlumEcoventCoordinator._should_warn_partial_failure(2, 5) is True


def test_partial_failure_threshold_warns_by_count() -> None:
    assert PlumEcoventCoordinator._should_warn_partial_failure(3, 40) is True
