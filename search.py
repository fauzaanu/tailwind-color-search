import re
from glob import glob
from datetime import datetime


def load_tailwind_config():
    with open("tailwind.config.js", "r") as f:
        config_content = f.read()

    # Extract the content of the module.exports object
    match = re.search(r"module\.exports\s*=\s*({[\s\S]*})", config_content)
    if not match:
        raise ValueError("Could not find module.exports in the config file")

    config_str = match.group(1)

    # Extract theme and colors using regex
    theme_match = re.search(
        r"theme\s*:\s*{([^}]*extend\s*:\s*{[^}]*}[^}]*)}", config_str, re.DOTALL
    )
    if not theme_match:
        raise ValueError("Could not find theme in the config")

    theme_content = theme_match.group(1)

    colors_match = re.search(r"colors\s*:\s*{([^}]*)}", theme_content, re.DOTALL)
    if not colors_match:
        raise ValueError("Could not find colors in the theme")

    colors_content = colors_match.group(1)

    # Parse colors content
    colors = {}
    color_matches = re.finditer(r"(\w+)\s*:\s*{([^}]*)}", colors_content)
    for match in color_matches:
        color_name = match.group(1)
        color_variants = {}
        variant_matches = re.finditer(
            r'(\w+)\s*:\s*["\']([^"\']*)["\']', match.group(2)
        )
        for variant_match in variant_matches:
            variant_name = variant_match.group(1)
            variant_value = variant_match.group(2)
            color_variants[variant_name] = variant_value
        colors[color_name] = color_variants

    # Create a simplified config dictionary
    config = {
        "theme": {"extend": {"colors": colors}},
        "content": re.findall(r'"([^"]*)"', config_str),  # Extract content patterns
    }

    return config


def get_color_classes(config):
    colors = config["theme"]["extend"]["colors"]
    color_classes = set()
    for color, variants in colors.items():
        color_classes.add(color)
        for variant in variants.keys():
            if variant != "DEFAULT":
                color_classes.add(f"{color}-{variant}")
    return color_classes


def find_hard_coded_colors(config, color_classes):
    content_patterns = config["content"]
    color_class_pattern = r"\b(bg|text|border|ring)-(\w+(-\w+)?)\b"
    report = []

    for pattern in content_patterns:
        for filepath in glob(pattern, recursive=True):
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
                matches = re.findall(color_class_pattern, content)
                hard_coded = [
                    match for match in matches if match[1] not in color_classes
                ]
                if hard_coded:
                    report.append(
                        f'{filepath}: {", ".join([f"{m[0]}-{m[1]}" for m in hard_coded])}'
                    )

    return report


def main():
    config = load_tailwind_config()
    color_classes = get_color_classes(config)
    report = find_hard_coded_colors(config, color_classes)

    if report:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"hard_coded_colors_report_{timestamp}.txt"
        with open(filename, "w") as f:
            f.write("\n".join(report))
        print(f"Report generated: {filename}")
    else:
        print("No hard-coded color classes found.")


if __name__ == "__main__":
    main()
