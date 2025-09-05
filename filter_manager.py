import pandas as pd

class FilterManager:
    """Hanterar filter och exkluderingslogik."""
    def __init__(self, metadata):
        self.metadata = metadata

    def apply_filters(self, filters, exclusions):
        """Tillämpa inkluderings- och exkluderingslogik."""
        filtered_data = self.metadata.copy()

        # Steg 1: Tillämpa alla inkluderingsfilter
        for column, value in filters.items():
            if value and value != "All":
                filtered_data = filtered_data[
                    filtered_data[column].str.casefold() == value.casefold()
                ]

        # Steg 2: Tillämpa alla exkluderingsfilter
        for column, value in exclusions.items():
            if value and value != "All":
                filtered_data = filtered_data[
                    filtered_data[column].str.casefold() != value.casefold()
                ]

        return filtered_data
