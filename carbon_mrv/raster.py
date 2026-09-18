import rasterio


def forest_area_ha(raster_path: str, forest_value: int) -> float:
    """Count pixels equal to forest_value and convert to hectares using the
    raster's own pixel size (from its transform) -- never hardcoded, so this
    stays correct if a different-resolution raster is substituted later."""
    with rasterio.open(raster_path) as src:
        band = src.read(1)
        pixel_area_m2 = abs(src.transform.a * src.transform.e)
        forest_pixel_count = int((band == forest_value).sum())

    return forest_pixel_count * pixel_area_m2 / 10_000.0
