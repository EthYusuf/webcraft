"""Image tooling: size guide per placement, quality analysis, placement suggestions, optimisation.

    from webcraft.images import image_guide, analyze_image, suggest_placement

    print(image_guide("hero_background"))          # what size should my hero image be?
    print(analyze_image("photo.jpg", "hero"))      # is this photo good enough there?
    for p in suggest_placement("photo.jpg"):       # where does this photo fit best?
        print(p)
"""

from .analyze import (ERROR, INFO, WARNING, CropSuggestion, ImageReport, Issue, Placement, analyze_image,
                      analyze_info, crop_to_aspect, recommended_size, suggest_placement)
from .optimize import OptimizedImage, has_pillow, optimize_image
from .probe import ImageInfo, ImageProbeError, probe, probe_bytes, probe_url
from .specs import SLOTS, ImageSlot, get_slot, guide_table, image_guide

# Turkish aliases
resim_rehberi = image_guide
resim_analiz = analyze_image
resim_nereye = suggest_placement

__all__ = [
    "SLOTS", "ImageSlot", "get_slot", "image_guide", "guide_table",
    "ImageInfo", "ImageProbeError", "probe", "probe_bytes", "probe_url",
    "analyze_image", "analyze_info", "suggest_placement", "recommended_size", "crop_to_aspect",
    "ImageReport", "Issue", "Placement", "CropSuggestion", "ERROR", "WARNING", "INFO",
    "optimize_image", "OptimizedImage", "has_pillow",
    "resim_rehberi", "resim_analiz", "resim_nereye",
]
