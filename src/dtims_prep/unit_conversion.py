import pandas

def km_to_meters(km: pandas.Series):
    """
    Converts a pandas Series object from floating point values to integer values, 
    multiplying by 1000.
    Fails if there are NaN or Inf values in the series."""
    return (km * 1000.0).round().astype('i4')