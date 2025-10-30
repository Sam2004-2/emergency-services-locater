from django.contrib.gis.db import models


class County(models.Model):
    """
    Administrative county boundary with geographic polygon.
    
    Represents county-level administrative boundaries with multilingual names
    and ISO codes for spatial containment queries.
    """
    
    source_id = models.CharField(max_length=100, null=True, blank=True, help_text="Original source identifier")
    name_en = models.CharField(max_length=100, db_index=True, help_text="County name in English")
    name_local = models.CharField(max_length=100, null=True, blank=True, help_text="County name in local language")
    iso_code = models.CharField(max_length=10, null=True, blank=True, unique=True, help_text="ISO 3166-2 code")
    geom = models.MultiPolygonField(srid=4326, spatial_index=True, help_text="County boundary (WGS84)")

    class Meta:
        db_table = 'boundaries_county'
        verbose_name = 'County'
        verbose_name_plural = 'Counties'
        ordering = ['name_en']

    def __str__(self) -> str:
        return self.name_en
