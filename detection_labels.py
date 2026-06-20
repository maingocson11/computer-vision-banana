BANANA_LABEL_VI = "Chuối"


def apply_vietnamese_banana_label(model):
    """Rename YOLO banana class to Vietnamese and return banana class ids."""
    names = getattr(model, "names", None)
    if not names:
        return []

    items = names.items() if isinstance(names, dict) else enumerate(names)
    banana_ids = []

    for class_id, class_name in items:
        if str(class_name).strip().lower() == "banana":
            banana_ids.append(int(class_id))

    if not banana_ids:
        return []

    if isinstance(names, dict):
        for class_id in banana_ids:
            names[class_id] = BANANA_LABEL_VI
    else:
        for class_id in banana_ids:
            names[class_id] = BANANA_LABEL_VI

    return banana_ids
