from cluster_client.config import AppConfig


def show_default_config() -> str:
    """
    Generate a markdown table showing default configuration values.

    Returns:
        str: A markdown table with columns: Option, Type, Default Value
    """
    # Get the model fields from AppConfig
    fields = AppConfig.model_fields

    # First pass: collect all data and calculate column widths
    rows = []
    for field_name, field_info in fields.items():
        # Get the type annotation
        field_type = (
            field_info.annotation.__name__
            if hasattr(field_info.annotation, "__name__")
            else str(field_info.annotation)
        )

        # Get the default value
        default_value = field_info.default

        # Format the default value for display
        if isinstance(default_value, str):
            formatted_default = f'"{default_value}"'
        else:
            formatted_default = str(default_value)

        rows.append((field_name, field_type, formatted_default))

    # Calculate maximum width for each column
    max_option = max(len(row[0]) for row in rows)
    max_type = max(len(row[1]) for row in rows)
    max_default = max(len(row[2]) for row in rows)

    # Ensure minimum widths for headers
    max_option = max(max_option, len("Option"))
    max_type = max(max_type, len("Type"))
    max_default = max(max_default, len("Default Value"))

    # Build the markdown table with padding
    lines = []
    lines.append(
        f"| {'Option'.ljust(max_option)} | {'Type'.ljust(max_type)} | {'Default Value'.ljust(max_default)} |"
    )
    lines.append(
        f"|{'-' * (max_option + 2)}|{'-' * (max_type + 2)}|{'-' * (max_default + 2)}|"
    )

    for option, type_name, default in rows:
        lines.append(
            f"| {option.ljust(max_option)} | {type_name.ljust(max_type)} | {default.ljust(max_default)} |"
        )

    return "\n".join(lines)

