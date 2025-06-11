from perspective.widget import PerspectiveWidget
import polars as pl

def display(df: pl.DataFrame | pl.LazyFrame):
    """
    Displays a Polars df or lf inline with notebook.
    """
    return PerspectiveWidget(
        df,
        plugin="Datagrid",
        theme="Monokai"
    )