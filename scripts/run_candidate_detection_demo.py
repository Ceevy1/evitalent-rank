from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from evitalent.achievement_detection import AchievementCandidateDetector
from evitalent.demo_samples import HR_MULTI_ACHIEVEMENT_TEXT


def main() -> None:
    candidates = AchievementCandidateDetector().detect(HR_MULTI_ACHIEVEMENT_TEXT)
    print(f"candidate_count={len(candidates)}")
    for item in candidates:
        print(f"{item.candidate_event_id}\t{item.isolated_clause}\t{','.join(item.detected_numeric_expressions)}")


if __name__ == "__main__":
    main()
