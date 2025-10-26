from django.contrib.gis.db import models


class County(models.Model):
    """
    Administrative county boundary with geographic polygon.
    
    Represents county-level administrative boundaries with multilingual names
    and ISO codes for spatial containment queries.
    
    Note: This model uses managed=False as data is maintained externally.
    """
    
    id = models.IntegerField(primary_key=True)
    source_id = models.TextField(null=True, blank=True, help_text="Original source identifier")
    name_en = models.TextField(help_text="County name in English")
    name_local = models.TextField(null=True, blank=True, help_text="County name in local language")
    iso_code = models.TextField(null=True, blank=True, help_text="ISO 3166-2 code")
    geom = models.MultiPolygonField(srid=4326, help_text="County boundary (WGS84)")

    class Meta:
        db_table = 'admin_counties'
        managed = False
        verbose_name = 'County'
        verbose_name_plural = 'Counties'

    def __str__(self) -> str:
        return self.name_en
