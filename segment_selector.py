"""Select useful activity segments while preserving every starred segment."""


def is_starred(segment):
    value = segment.get("starred", False)
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)


def _valid_range(segment):
    start = segment.get("start_index")
    end = segment.get("end_index")
    return (
        isinstance(start, int)
        and not isinstance(start, bool)
        and isinstance(end, int)
        and not isinstance(end, bool)
        and start >= 0
        and end > start
    )


def _overlaps(left, right):
    """Treat ranges as half-open so intervals may meet at one boundary."""
    return (
        left["start_index"] < right["end_index"]
        and right["start_index"] < left["end_index"]
    )


def select_segments(segments):
    """Return selected valid segments in activity order.

    Every starred segment is retained, even when starred segments overlap each
    other. Regular segments overlapping any starred segment are discarded. Among
    the remaining regular segments, longer segments win when ranges overlap.
    """
    candidates = []
    for position, segment in enumerate(segments):
        if not (segment.get("name") or "").strip() or not _valid_range(segment):
            continue
        candidates.append((position, segment))

    starred = [item for item in candidates if is_starred(item[1])]
    regular = [item for item in candidates if not is_starred(item[1])]
    regular.sort(
        key=lambda item: (
            -(item[1]["end_index"] - item[1]["start_index"]),
            item[1]["start_index"],
            item[0],
        )
    )

    starred_segments = [segment for _, segment in starred]
    selected_regular = []
    for _, candidate in regular:
        if any(_overlaps(candidate, existing) for existing in starred_segments):
            continue
        if any(_overlaps(candidate, existing) for existing in selected_regular):
            continue
        selected_regular.append(candidate)

    selected = starred_segments + selected_regular
    return sorted(selected, key=lambda segment: (segment["start_index"], segment["end_index"]))
